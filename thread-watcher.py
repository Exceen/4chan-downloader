#!/usr/bin/python
from urllib import request
import argparse
import logging
import os
import re

# TODO
# add argument to have something like vg/monster-hunter/ and inside that dir all threads separated by their id

# ./thread-watcher.py -b vg -q mhg -f queue.txt -n "Monster Hunter"


log = logging.getLogger('thread-watcher')
workpath = os.path.dirname(os.path.realpath(__file__))


def load(url):
    req = request.Request(url, headers={'User-Agent': '4chan Browser'})
    return request.urlopen(req).read()


def main():
    parser = argparse.ArgumentParser(description='thread-watcher')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    parser.add_argument('-b', '--board', help='board', required=True)
    parser.add_argument('-q', '--query', help='search term', required=True)
    parser.add_argument('-f', '--queuefile', help='queue file', required=True)
    parser.add_argument('-n', '--naming', help='dir name for saved threads', required=True)
    args = parser.parse_args()

    name = args.naming.lower().replace(' ', '-')
    query = args.query
    base_url = 'https://boards.4chan.org/' + args.board + '/'
    catalog_url = base_url + 'catalog'

    current_threads = []
    regex = '"(\d+)":\{(?!"sub").*?"sub":"((?!").*?)"'
    for threadid, title in list(set(re.findall(regex, load(catalog_url).decode('utf-8')))):
        if query not in title:
            continue
        current_threads.append(base_url + 'thread/' + threadid + '/' + name)

    ignored_lines = ['#', '-', '\n']
    queue_threads = [line.strip() for line in open(args.queuefile, 'r') if line[0] not in ignored_lines]

    new_threads = list(set(current_threads) - set(queue_threads))
    if args.verbose:
        print(new_threads)

    if len(new_threads) > 0:
        with open(args.queuefile, 'a') as f:
            for thread in new_threads:
                f.write(thread)
                f.write('\n')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
