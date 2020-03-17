#!/usr/bin/python
from itertools import chain
from urllib import request
import argparse
import json
import logging
import os

# TODO
# add argument to have something like vg/monster-hunter/ and inside that dir all threads separated by their id

# ./thread-watcher.py -b vg -q mhg -f queue.txt -n "Monster Hunter"


log = logging.getLogger('thread-watcher')
workpath = os.path.dirname(os.path.realpath(__file__))
API_URL_BASE = 'https://a.4cdn.org'
URL_BASE = 'https://boards.4chan.org'


def load_catalog(board):
    url = '{base}/{board}/catalog.json'.format(base=API_URL_BASE, board=board)
    req = request.Request(url, headers={'User-Agent': '4chan Browser',
                                        'Content-Type': 'application/json'})
    content = request.urlopen(req).read().decode('utf-8')
    return json.loads(content)


def get_threads(board):
    catalog = load_catalog(board)
    return chain.from_iterable([page['threads'] for page in catalog])


def main():
    parser = argparse.ArgumentParser(description='thread-watcher')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    parser.add_argument('-b', '--board', help='board', required=True)
    parser.add_argument('-q', '--query', help='search term', required=True)
    parser.add_argument('-f', '--queuefile', help='queue file', required=True)
    parser.add_argument('-n', '--naming', help='dir name for saved threads', required=True)
    args = parser.parse_args()

    name = args.naming.lower().replace(' ', '-')
    thread_url = '{base}/{board}/%d/{name}'.format(
        base=URL_BASE,
        board=args.board,
        name=name,
    )

    current_threads = []
    for thread in get_threads(args.board):
        if args.query in thread.get('sub', ''):
            current_threads.append(thread_url % thread['no'])

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
