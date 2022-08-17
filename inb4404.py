#!/usr/bin/python3
import urllib.request, urllib.error, urllib.parse, argparse, logging
import os, re, time
import http.client
import fileinput
from multiprocessing import Process

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

def main():
    global args
    parser = argparse.ArgumentParser(description='inb4404')
    parser.add_argument('thread', nargs=1, help='url of the thread (or filename; one url per line)')
    parser.add_argument('-c', '--with-counter', action='store_true', help='show a counter next the the image that has been downloaded')
    parser.add_argument('-d', '--date', action='store_true', help='show date as well')
    parser.add_argument('-l', '--less', action='store_true', help='show less information (surpresses checking messages)')
    parser.add_argument('-n', '--use-names', action='store_true', help='use thread names instead of the thread ids (...4chan.org/board/thread/thread-id/thread-name)')
    parser.add_argument('-r', '--reload', action='store_true', help='reload the queue file every 5 minutes')
    parser.add_argument('-s', '--sleep', action='store', help='sleep `N` seconds between every download', metavar='N') # TODO
    parser.add_argument('-t', '--title', action='store_true', help='save original filenames')

    parser.add_argument('--single-process', action='store_true', help='disable multiprocessing, download one thread at a time')

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

def call_download_thread(thread_link, args):
    try:
        download_thread(thread_link, args)
    except KeyboardInterrupt:
        pass

    return

def download_thread(thread_link, args):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]

        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):
            thread = thread_tmp

    while True:
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
                break
            continue
        except (urllib.error.URLError, http.client.BadStatusLine, http.client.IncompleteRead):
            log.fatal(thread_link + ' crashed!')
            raise

        if not args.less:
            log.info('Checking ' + board + '/' + thread)
        time.sleep(20)

def run_single_process(links_list):
    for l in links_list:
        call_download_thread(l, args)

def run_multiple_process(links_list, processes_list):
    for l in links_list:
        process = Process(target=call_download_thread, args=(l, args, ))
        process.start()
        processes_list.append([process, l])

        if len(processes_list) == 0:
            log.warning(filename + ' empty')

def download_from_file(filename):
    running_links = []
    while True:
        processes = []
        for link in [_f for _f in [line.strip() for line in open(filename) if line[:4] == 'http'] if _f]: # Fix this line
            if link not in running_links:
                running_links.append(link)
                log.info('Added ' + link)

        if args.single_process:
            run_single_process(running_links)
        else:
            run_multiple_process(running_links, processes)

        if args.reload:
            time.sleep(60 * 5) # 5 minutes
            links_to_remove = []
            for process, link in processes:
                if not process.is_alive():
                    links_to_remove.append(link)
                else:
                    process.terminate()

            for link in links_to_remove:
                for line in fileinput.input(filename, inplace=True):
                    print(line.replace(link, '-' + link), end='')
                running_links.remove(link)
                log.info('Removed ' + link)
            if not args.less:
                log.info('Reloading ' + args.thread[0]) # thread = filename here; reloading on next loop
        else:
            break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
