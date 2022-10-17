#!/usr/bin/python3
import urllib.request, urllib.error, urllib.parse, argparse, logging
import os, re, time
import http.client
import fileinput
from multiprocessing import Process
from multiprocessing import Lock, current_process, Manager
#import queue


log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None
###
# Danger: making these sleep timers too low can cause their corresponding while loops to execute too quickly, bogging down the CPU
call_download_thread_while_loop_sleep_time = .25
download_from_file_while_loop_sleep_time = .25
###
queue_cleanup_timer = 30 #in seconds, how often to check for dead links and mark them dead in the config file
thread_check_timer = 20 #in seconds, how often to queue up all threads to check for new content
manager = Manager() #getting a manager object we can use to create managed data types
tasks_to_accomplish = manager.list() #queue for threads to pull work out of
links_to_remove = manager.list() #queue used to keep track of threads to remove from config


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
    parser.add_argument('-p', '--parallel-threads', type=int, default=4, help='Number of parallel threads to run at once. Default is 4')
    args = parser.parse_args()

    if args.date:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')

    thread = args.thread[0].strip()
    if thread[:4].lower() == 'http':
        download_thread(thread, args)
    else:
        download_from_file(thread)

    if args.title:
        try:
            import bs4
        except ImportError:
            logging.error("Could not import BeautifulSoup! Disabling --title option...")
            args.title = False

def load(url):
    req = urllib.request.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib.request.urlopen(req).read()


def get_title_list(html_content):
    ret = list()

    from bs4 import BeautifulSoup
    parsed = BeautifulSoup(html_content, 'html.parser')
    divs = parsed.find_all("div", {"class": "fileText"})

    for i in divs:
        current_child = i.findChildren("a", recursive = False)[0]
        try:
            ret.append(current_child["title"])
        except KeyError:
            ret.append(current_child.text)

    return ret


def call_download_thread(que, links_to_remove):
    while True:
        try:
            if len(que) == 0: #check if there are any jobs waiting
                time.sleep(call_download_thread_while_loop_sleep_time) #sleep to prevent while loop from dominating CPU
                continue
            thread_link = que.pop(0)
            download_thread(thread_link, links_to_remove)
        except KeyboardInterrupt:
            break
        except:
            pass


def download_thread(thread_link, links_to_remove):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]

        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):
            thread = thread_tmp

    try:
        regex = '(\/\/i(?:s|)\d*\.(?:4cdn|4chan)\.org\/\w+\/(\d+\.(?:jpg|png|gif|webm)))'
        html_result = load(thread_link).decode('utf-8')
        regex_result = list(set(re.findall(regex, html_result)))

        directory = os.path.join(workpath, 'downloads', board, thread)
        if not os.path.exists(directory):
            os.makedirs(directory)

        regex_result = sorted(regex_result, key=lambda tup: tup[1])
        regex_result_len = len(regex_result)
        regex_result_cnt = 1

        if args.title:
            all_titles = get_title_list(html_result)

        for enum_index, enum_tuple in enumerate(regex_result):
            link, img = enum_tuple

            if args.title:
                img = all_titles[enum_index]

            img_path = os.path.join(directory, img)
            if not os.path.exists(img_path):
                data = load('https:' + link)

                output_text = board + '/' + thread + '/' + img
                if args.with_counter:
                    output_text = '[' + str(regex_result_cnt).rjust(len(str(regex_result_len))) +  '/' + str(regex_result_len) + '] ' + output_text

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
        #raise #commenting this out to test my theory

    if not args.less:
        log.info('Checking ' + board + '/' + thread)

    return True


def download_from_file(filename):
    running_links = [] #4chan threads to check periodically
    last_config_reload = time.time()
    last_queue_check = time.time()

    processes = []

    for w in range(args.parallel_threads):
        p = Process(target=call_download_thread, args=(tasks_to_accomplish, links_to_remove))
        processes.append(p)
        p.start()

    try:
        while True:

            for link in [_f for _f in [line.strip() for line in open(filename) if line[:4] == 'http'] if _f]:
                if link not in running_links:
                    running_links.append(link)
                    log.info('Added ' + link)
                    tasks_to_accomplish.append(link)

            # if enough time has passed, recheck list of running threads
            if time.time() >= (last_queue_check + thread_check_timer):
                for i in running_links:
                    if i not in tasks_to_accomplish: # check if the link we're adding is already in the queue. only add if it isnt
                        tasks_to_accomplish.append(i)
                last_queue_check = time.time()

            # check if there are any links that have died, and mark them as dead so they are no longer checked
            if args.reload and time.time() >= (last_config_reload + queue_cleanup_timer): # Non blocking 5 minute interval check
                for link in links_to_remove:
                    for line in fileinput.input(filename, inplace=True):
                        print(line.replace(link, '-' + link), end='')
                    running_links.remove(link)
                    links_to_remove.remove(link)
                    log.info('Removed ' + link)
                if not args.less:
                    log.info('Reloading ' + args.thread[0]) # thread = filename here; reloading on next loop
                last_config_reload = time.time()

            # if, for some reason, we do not have the required amount of threads running, spin up new threads
            while len(processes) != args.parallel_threads:
                p = Process(target=call_download_thread, args=(tasks_to_accomplish, links_to_remove))
                processes.append(p)
                p.start()

            # check for any threads that have completed
            for process in processes:
                process.join(download_from_file_while_loop_sleep_time) #this will clean up any processes that exited/crashed somehow, while also blocking for .25 seconds


    except KeyboardInterrupt:
        for p in processes: #close processes
            p.terminate()
        pass

    return

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
