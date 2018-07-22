#!/usr/bin/python
import urllib2, argparse, logging
import os, re, time
import httplib
import fileinput
from multiprocessing import Process

# TODO
# add argument to have something like vg/monster-hunter/ and inside that dir all threads separated by their id

# ./thread-watcher.py -b vg -q mhg -f queue.txt -n "Monster Hunter"


log = logging.getLogger('thread-watcher')
workpath = os.path.dirname(os.path.realpath(__file__))
args = None

def load(url):
    req = urllib2.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib2.urlopen(req).read()

def main():
    global args
    parser = argparse.ArgumentParser(description='thread-watcher')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    parser.add_argument('-b', '--board', nargs=1, help='board', required=True)
    parser.add_argument('-q', '--query', nargs=1, help='search term', required=True)
    parser.add_argument('-f', '--queuefile', nargs=1, help='queue file', required=True)
    parser.add_argument('-n', '--naming', nargs=1, help='dir name for saved threads', required=True)
    args = parser.parse_args()

    required_args = [args.board, args.query, args.queuefile, args.naming]
    for arg in required_args:
        if arg == None or len(arg) == 0 or len(arg[0]) == 0:
            exit()

    name = args.naming[0].lower().replace(' ', '-')
    query = args.query[0]
    base_url = 'https://boards.4chan.org/' + args.board[0] + '/'
    catalog_url = base_url + 'catalog'

    current_threads = []
    regex = '"(\d+)":\{(?!"sub").*?"sub":"((?!").*?)"'
    for threadid, title in list(set(re.findall(regex, load(catalog_url)))):
        if query not in title:
            continue
        current_threads.append(base_url + 'thread/' + threadid + '/' + name)

    ignored_lines = ['#', '-', '\n']
    queue_threads = [line.strip() for line in open(args.queuefile[0], 'r') if line[0] not in ignored_lines]
    
    new_threads = list(set(current_threads) - set(queue_threads))
    if args.verbose:
        print new_threads

    if len(new_threads) > 0:
        with open(args.queuefile[0], 'a') as f:
            for thread in new_threads:
                f.write(thread)
                f.write('\n')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
                            