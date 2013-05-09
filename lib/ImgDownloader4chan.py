import os
import sys
import urllib
import re
# import subprocess
import time

class ImgDownloader4chan:

    def __init__(self):
        self.image_url = 'http://images.4chan.org'
        self.rescan_time = 5
        self.board = raw_input('What board should I download from?\n')
        self.thread = raw_input('Which thread number?\n')
        self.url = self.make_url()

        if self.find_image_urls(self.url) != []: # otherwise no images are available to download
            self.directory = self.make_directory()
            self.loop()

    def loop(self):
        for x in xrange(1,3):
            self.image_urls = self.find_image_urls(self.url)

            # if self.images_urls != []:
            self.remove_duplicates()
            self.download_images()
            time.sleep(self.rescan_time)

        print 'Finished.'
    def make_url(self):
        template = 'http://boards.4chan.org/{board}/res/{thread}'
        template = template.replace('{board}', self.board)
        template = template.replace('{thread}', self.thread)
        return template
    def make_directory(self):
        """
        Creates a directory called 'downloads' with the subdirectories for the images.
        e.g.: ./downloads/{board}/{thread}
        """
        directory = os.path.join(os.getcwd(), 'downloads', self.board, self.thread)

        if not os.path.exists(directory):
            os.makedirs(directory)

        return directory

    def find_image_urls(self, url):
        """
        Should find all images which should be downloaded from 4chan. Yes, 'should'.
        """
        img_urls = []
        html = urllib.urlopen(url).read()
        tmp_urls = re.findall('(/[A-Za-z]+/src/\\d+\\.)(jpeg|jpg|png|gif)', html)

        for img in tmp_urls:
            img_urls.append(self.image_url + img[0] + img[1])

        print str(len(img_urls)/2) + ' images found.' # little bit buggy, because img_urls contains the URLs twice
        return list(set(img_urls))

    def remove_duplicates(self):
        """
        Removes the image-URLs which are downloaded previously.
        """
        duplicates = []

        for file in self.image_urls:
            if os.path.isfile(os.path.join(self.directory, file.split('/')[-1])):
                duplicates.append(file)

        for file in duplicates:
            self.image_urls.remove(file)

        print str(len(duplicates)) + ' files downloaded previously.'

    def download_images(self):
        """
        Downloads every image from the self.image_urls.
        """
        total_num_images = len(self.image_urls)
        current_image = 1

        for url in self.image_urls:
            print 'Downloading image ' + str(current_image) + ' of ' + str(total_num_images) + '.'
            urllib.urlretrieve(url, self.directory + '/' + url.split('/')[-1])
            current_image = current_image + 1
