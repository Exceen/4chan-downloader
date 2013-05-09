import os
import re
import urllib
# import time

class ImgDownloader4chan:

    def __init__(self):
        # self.rescan_time = 10

        self.raw_url = raw_input('Please enter the URL of the thread:\n').split('#')[0]
        print ''
        self.board = self.raw_url.split('/')[3]
        self.thread = self.raw_url.split('/')[5]

        self.url = self.create_url()
        self.directory = self.create_directory()

        self.loop()

    def loop(self):
        self.image_urls = self.find_image_urls()

        while len(self.image_urls) > self.remove_duplicates():
            print ''
            self.download_images()
            # time.sleep(self.rescan_time)

            print ''
            self.image_urls = self.find_image_urls()

        print '\nFinished.'

    def create_url(self):

        template = 'http://boards.4chan.org/{board}/res/{thread}'
        template = template.replace('{board}', self.board)
        template = template.replace('{thread}', self.thread)
        return template

    def create_directory(self):
        """
        Creates a directory called 'downloads' with the subdirectories for the images.
        e.g.: ./downloads/{board}/{thread}
        """
        directory = os.path.join(os.getcwd(), 'downloads', self.board, self.thread)

        if not os.path.exists(directory):
            os.makedirs(directory)

        return directory

    def find_image_urls(self):
        """
        Should find all images which should be downloaded from 4chan. Yes, 'should'.
        """
        img_urls = []
        html = urllib.urlopen(self.url).read()
        tmp_urls = re.findall('(/[A-Za-z]+/src/\\d+\\.)(jpeg|jpg|png|gif)', html)

        for img in tmp_urls:
            img_urls.append('http://images.4chan.org' + img[0] + img[1])

        print str(len(img_urls)/2) + ' images found.' # note: img_urls containts every url twice

        return list(set(img_urls)) # removes duplicates in img_urls

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

        return len(duplicates)

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
