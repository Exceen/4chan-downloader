#!/usr/bin/python
import urllib2, argparse, logging
import os, re, time
import httplib 
import fileinput
from multiprocessing import Process

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

def load(url):
    req = urllib2.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib2.urlopen(req).read()

def main():
    global args
    parser = argparse.ArgumentParser(description='inb4404')
    parser.add_argument('thread', nargs=1, help='url of the thread (or filename; one url per line)')
    parser.add_argument('-n', '--use-names', action='store_true', help='use thread names instead of the thread ids (...4chan.org/board/thread/thread-id/thread-name)')
    parser.add_argument('-r', '--reload', action='store_true', help='reload the file every 5 minutes')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')    

    if args.thread[0][:4].lower() == 'http':
        download_thread(args.thread[0])
    else:
        download_from_file(args.thread[0])

def download_thread(thread_link):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]
    if len(thread_link.split('/')) > 6:
        thread_tmp = thread_link.split('/')[6].split('#')[0]

        if args.use_names or os.path.exists(os.path.join(workpath, 'downloads', board, thread_tmp)):                
            thread = thread_tmp

    directory = os.path.join(workpath, 'downloads', board, thread)
    if not os.path.exists(directory):
        os.makedirs(directory)

    while True:
        try:
            for link, img in list(set(re.findall('(\/\/is\d*\.4chan\.org/\w+\/(\d+\.(?:jpg|png|gif|webm)))', load(thread_link)))):
                img_path = os.path.join(directory, img)
                if not os.path.exists(img_path):
                    data = load('https:' + link)

                    log.info(board + '/' + thread + '/' + img)

                    with open(img_path, 'w') as f:
                        f.write(data)

                    ##################################################################################
                    # saves new images to a seperate directory
                    # if you delete them there, they are not downloaded again
                    # if you delete an image in the 'downloads' directory, it will be downloaded again
                    copy_directory = os.path.join(workpath, 'new', board, thread)
                    if not os.path.exists(copy_directory):
                        os.makedirs(copy_directory)
                    copy_path = os.path.join(copy_directory, img)
                    with open(copy_path, 'w') as f:
                        f.write(data)
                    ##################################################################################
        except urllib2.HTTPError, err:
            time.sleep(10)
            try:
                load(thread_link)    
            except urllib2.HTTPError, err:
                log.info('%s 404\'d', thread_link)
                break
            continue
        except (urllib2.URLError, httplib.BadStatusLine, httplib.IncompleteRead):
            log.warning('Something went wrong')

        log.info('Checking ' + board + '/' + thread)
        time.sleep(20)

def download_from_file(filename):
    running_links = []
    while True:
        processes = []
        for link in filter(None, [line.strip() for line in open(filename) if line[:4] == 'http']):
            if link not in running_links:
                running_links.append(link)
                log.info('Added ' + link)

            process = Process(target=download_thread, args=(link, ))
            process.start()
            processes.append([process, link])

        if len(processes) == 0:
            log.warning(filename + ' empty')
        
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
                    print line.replace(link, '-' + link),
                running_links.remove(link)
                log.info('Removed ' + link)
            log.info('Reloading ' + args.thread[0]) # thread = filename here; reloading on next loop
        else:
            break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
