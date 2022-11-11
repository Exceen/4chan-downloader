#!/usr/bin/python3
import argparse
import fileinput
import http.client
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from multiprocessing import Process, Manager

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

queue_cleanup_timer = 30  # in seconds, how often to check for dead links and mark them dead in the config file
thread_check_timer = 20  # in seconds, how often to queue up all threads to check for new content

manager = Manager()  # getting a manager object we can use to create managed data types
tasks_to_accomplish = manager.list()  # queue for threads to pull work out of
links_to_remove = manager.list()  # queue used to keep track of threads to remove from config


def main():
    global args
    parser = argparse.ArgumentParser(description='inb4404')
    parser.add_argument('thread', nargs=1, help='url of the thread (or filename; one url per line)')
    parser.add_argument('-c', '--with-counter', action='store_true', help='show a counter next the the image that has been downloaded')
    parser.add_argument('-d', '--date', action='store_true', help='show date as well')
    parser.add_argument('-l', '--less', action='store_true', help='show less information (surpresses checking messages)')
    parser.add_argument('-n', '--use-names', action='store_true', help='use thread names instead of the thread ids (...4chan.org/board/thread/thread-id/thread-name)')
    parser.add_argument('-r', '--reload', action='store_true', help='reload the queue file every 5 minutes')
    parser.add_argument('-t', '--title', action='store_true', help='save original filenames')
    parser.add_argument('-p', '--parallel-threads', type=int, default=4, help='number of parallel threads to run at once. (default=4)')
    args = parser.parse_args()

    if args.date:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')

    if args.title:
        try:
            import bs4
            import django
        except ImportError:
            logging.error('Could not import the required modules! Disabling --title option...')
            args.title = False

    thread = args.thread[0].strip()
    if thread[:4].lower() == 'http':
        while True:
            download_thread(thread, args)
            time.sleep(20)
    else:
        download_from_file(thread)


def load(url):
    req = urllib.request.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib.request.urlopen(req).read()


def get_title_list(html_content):
    ret = list()

    from bs4 import BeautifulSoup
    parsed = BeautifulSoup(html_content, 'html.parser')
    divs = parsed.find_all("div", {"class": "fileText"})

    for i in divs:
        current_child = i.findChildren("a", recursive=False)[0]
        try:
            ret.append(current_child["title"])
        except KeyError:
            ret.append(current_child.text)

    return ret


def download_thread(thread_link, args):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]
        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):
            thread = thread_tmp

    try:
        regex = r'(\/\/i(?:s|)\d*\.(?:4cdn|4chan)\.org\/\w+\/(\d+\.(?:jpg|png|gif|webm)))'
        html_result = load(thread_link).decode('utf-8')
        regex_result = list(set(re.findall(regex, html_result)))
        regex_result = sorted(regex_result, key=lambda tup: tup[1])
        regex_result_len = len(regex_result)
        regex_result_cnt = 1

        directory = os.path.join(workpath, 'downloads', board, thread)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if args.title:
            all_titles = get_title_list(html_result)

        for enum_index, enum_tuple in enumerate(regex_result):
            link, img = enum_tuple

            if args.title:
                img = all_titles[enum_index]
                from django.utils.text import get_valid_filename
                img_path = os.path.join(directory, get_valid_filename(img))
            else:
                img_path = os.path.join(directory, img)

            if not os.path.exists(img_path):
                data = load('https:' + link)

                output_text = board + '/' + thread + '/' + img
                if args.with_counter:
                    output_text = '[' + str(regex_result_cnt).rjust(len(str(regex_result_len))) + '/' + str(regex_result_len) + '] ' + output_text

                log.info(output_text)

                with open(img_path, 'wb') as f:
                    f.write(data)

                ##################################################################################
                # saves new images to a seperate directory
                # if you delete them there, they are not downloaded again
                # if you delete an image in the 'downloads' directory, it will be downloaded again
                copy_directory = os.path.join(workpath, 'new', board, thread)
                if not os.path.exists(copy_directory):
                    os.makedirs(copy_directory)
                copy_path = os.path.join(copy_directory, img)
                with open(copy_path, 'wb') as f:
                    f.write(data)
                ##################################################################################
            regex_result_cnt += 1

    except urllib.error.HTTPError:
        time.sleep(10)
        try:
            load(thread_link)
        except urllib.error.HTTPError:
            log.info('%s 404\'d', thread_link)
            links_to_remove.append(thread_link)
    except (urllib.error.URLError, http.client.BadStatusLine, http.client.IncompleteRead):
        log.fatal(thread_link + ' crashed!')

    if not args.less:
        log.info('Checking ' + board + '/' + thread)

def call_download_thread(queue, args):
    while True:
        try:
            if len(queue) == 0:  # check if there are any jobs waiting
                time.sleep(0.25)  # sleep to prevent while loop from dominating CPU
            else:
                download_thread(queue.pop(0), args)
        except KeyboardInterrupt:
            break
        except:
            pass


def download_from_file(filename):
    processes = []
    running_links = []  # 4chan threads to check periodically

    last_config_reload = time.time()
    last_queue_check = time.time()

    while len(processes) < args.parallel_threads:
        p = Process(target=call_download_thread, args=(tasks_to_accomplish, args))
        processes.append(p)
        p.start()

    try:
        while True:
            for link in [line.strip() for line in open(filename) if line[:4] == 'http']:
                if link not in running_links:
                    running_links.append(link)
                    tasks_to_accomplish.append(link)
                    log.info('Added ' + link)

            # if enough time has passed, recheck list of running threads
            if time.time() >= (last_queue_check + thread_check_timer):
                for i in running_links:
                    if i not in tasks_to_accomplish:  # check if the link we're adding is already in the queue. only add if it is not
                        tasks_to_accomplish.append(i)
                last_queue_check = time.time()

            # check if there are any links that have died, and mark them as dead so they are no longer checked
            if args.reload and time.time() >= (last_config_reload + queue_cleanup_timer):
                for link in links_to_remove:
                    for line in fileinput.input(filename, inplace=True):
                        print(line.replace(link, '-' + link), end='')
                    running_links.remove(link)
                    links_to_remove.remove(link)
                    log.info('Removed ' + link)
                if not args.less:
                    log.info('Reloading ' + args.thread[0])  # thread = filename here; reloading on next loop
                last_config_reload = time.time()

            # if, for some reason, we do not have the required amount of threads running, spin up new threads
            while len(processes) < args.parallel_threads:
                p = Process(target=call_download_thread, args=(tasks_to_accomplish, args))
                processes.append(p)
                p.start()

            # check for any threads that have completed
            for process in processes:
                process.join(0.25)  # this will clean up any processes that exited/crashed somehow, while also blocking for .25 seconds

    except KeyboardInterrupt:
        for p in processes:  # close processes
            p.terminate()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
