#!/usr/bin/python
import urllib2, argparse, logging
import os, re, time
import httplib

from multiprocessing import Process

log = logging.getLogger('inb4404')
workpath = os.path.dirname(os.path.realpath(__file__))

def load(url):
    return urllib2.urlopen(url).read()

def main():
    parser = argparse.ArgumentParser(description='inb4404')
    parser.add_argument('thread', nargs=1, help='url of the thread (or filename; one url per line)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')    

    if args.thread[0][:4].lower() == 'http':
        download_thread(args.thread[0])
    else:
        download_from_file(args.thread[0])

def download_thread(thread_link):
    board = thread_link.split('/')[3]
    thread = thread_link.split('/')[5].split('#')[0]

    directory = os.path.join(workpath, 'downloads', board, thread)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # os.chdir(directory) # unnecessary if directory is given instead of filename only when writing

    while True:
        try:
            for link, img in list(set(re.findall('(\/\/i.4cdn.org/\w+\/(\d+\.(?:jpg|png|gif|webm)))', load(thread_link)))):
                img_path = directory + '/' + img
                if not os.path.exists(img_path):
                    # log.info(img.ljust(18) + ' | /' + board + '/' + thread)
                    try:
                        data = load('https:' + link)
                        log.info(img)
                    except urllib2.HTTPError, err:
                        log.error(img + ' 404\'d')
                        continue
                    with open(img_path, 'w') as f:
                        f.write(data)
                    copy_directory = os.path.join(workpath, 'new', board, thread)
                    if not os.path.exists(copy_directory):
                        os.makedirs(copy_directory)
                    copy_path = copy_directory + '/' + img
                    with open(copy_path, 'w') as f:
                        f.write(data)
        except urllib2.HTTPError, err:
            print err
            log.info('%s 404\'d', thread_link)
            break
        except (urllib2.URLError, httplib.BadStatusLine, httplib.IncompleteRead):
            log.warning('something went wrong')

        print('.')
        time.sleep(20)

def download_from_file(filename):
    try:
        for link in filter(None, [line.strip() for line in open(filename) if line[:1] != '#']):
            Process(target=download_thread, args=(link, )).start()
    except Exception, e:
        raise e

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
