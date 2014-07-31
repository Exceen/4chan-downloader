#!/usr/bin/python
import urllib2, argparse, logging
import os, sys, re, time
import httplib

log = logging.getLogger('inb4404')

def load(url):
	return urllib2.urlopen(url).read()

def main():
	parser = argparse.ArgumentParser(description='inb4404')
	parser.add_argument('thread', nargs=1, help='url of the thread')
	args = parser.parse_args()

	logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%I:%M:%S %p')

	workpath = os.path.dirname(os.path.realpath(__file__))
	board = ''.join(args.thread).split('/')[3]
	thread = ''.join(args.thread).split('/')[5].split('#')[0]

	directory = os.path.join(workpath, 'downloads', board, thread)
	if not os.path.exists(directory):
		os.makedirs(directory)

	os.chdir(directory)

	while len(args.thread):
		for t in args.thread:
			try:
				for link, img in re.findall('(\/\/i.4cdn.org/\w+\/(\d+\.(?:jpg|png|gif|webm)))', load(t)):
					if not os.path.exists(img):
						log.info(img)
						data = load('https:' + link)
						with open(img, 'w') as f:
							f.write(data)
			except urllib2.HTTPError, err:
				log.info('%s 404\'d', t)
				args.thread.remove(t)
				continue
			except (urllib2.URLError, httplib.BadStatusLine, httplib.IncompleteRead):
				log.warning('something went wrong')
		print('.')
		time.sleep(20)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		pass
