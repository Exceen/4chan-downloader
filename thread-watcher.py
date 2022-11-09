#!/usr/bin/python
from itertools import chain
from urllib import request
import argparse
import json
import re

# TODO
# add argument to have something like vg/monster-hunter/ and inside that dir all threads separated by their id

# ./thread-watcher.py -b vg -q mhg -f queue.txt -n "Monster Hunter"


API_URL_TEMPLATE = 'https://a.4cdn.org/{board}/catalog.json'
THREAD_URL_TEMPLATE = 'https://boards.4chan.org/{board}/thread/{id}/{name}'


def get_threads(board, url_template=None):
    template = url_template or API_URL_TEMPLATE
    url = template.format(board=board)
    req = request.Request(url, headers={'User-Agent': '4chan Browser',
                                        'Content-Type': 'application/json'})
    content = request.urlopen(req).read().decode('utf-8')
    catalog = json.loads(content)
    return chain.from_iterable([page['threads'] for page in catalog])


def main():
    parser = argparse.ArgumentParser(description='thread-watcher')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    parser.add_argument('-b', '--board', help='board', required=True)
    parser.add_argument('-q', '--query', help='search term (supports regex)', required=True)
    parser.add_argument('-f', '--queuefile', help='queue file', required=True)
    parser.add_argument('-n', '--naming', help='dir name for saved threads', required=True)
    parser.add_argument('-u', '--thread-url', help='base url of the chans boards (default: https://boards.4chan.org/{board}/thread/{id}/{name})')
    parser.add_argument('-a', '--api-url', help='base url of the chans api (default: https://a.4cdn.org/{board}/catalog.json)')
    args = parser.parse_args()

    url_template = args.thread_url or THREAD_URL_TEMPLATE
    name = args.naming.lower().replace(' ', '-')
    file = open(args.queuefile, 'a+')
    file.seek(0)
    query = re.compile(args.query)

    ignored_lines = ['#', '-', '\n']
    queue_threads = [line.strip() for line in file if line[0] not in ignored_lines]

    for thread in get_threads(args.board, args.api_url):
        thread_url = url_template.format(board=args.board, id=thread['no'], name=name)

        if query.search(thread.get('sub', thread.get('com', ''))) and thread_url not in queue_threads:
            file.write('%s\n' % thread_url)
            if args.verbose:
                print(thread_url)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
