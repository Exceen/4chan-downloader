4chan-downloader
================

Python script to download all images/webms of a 4chan thread

### Download Script ###

The main script is called inb4404.py and can be called like this: `python3 inb4404.py [thread/filename]`

```
usage: inb4404.py [-h] [-c] [-d] [-l] [-n] [-r] [-t] thread/filename

positional arguments:
  thread              url of the thread (or filename; one url per line)

optional arguments:
  -h, --help          show this help message and exit
  -c, --with-counter  show a counter next the the image that has been
                      downloaded
  -d, --date          show date as well
  -l, --less          show less information (surpresses checking messages)
  -n, --use-names     use thread names instead of the thread ids
                      (...4chan.org/board/thread/thread-id/thread-name)
  -r, --reload        reload the queue file every 5 minutes
  -t, --title         save original filenames
      --no-new-dir    don't create the `new` directory
```

You can parse a file instead of a thread url. In this file you can put as many links as you want, you just have to make sure that there's one url per line. A line is considered to be a url if the first 4 letters of the line start with 'http'.

If you use the --use-names argument, the thread name is used to name the respective thread-directory instead of the thread id. You can specify this name yourself, e.g.: `https://boards.4chan.org/a/thread/12345678/this-is-my-thread-name`

### Requirements ###

This script can be called using the default python3 libraries. Only if you want to use the `--use-names` parameter you have to install the dependencies from the `requirements.txt`-file. This can be done by calling `pip install -r requirements.txt`.

### Thread Watcher ###

This is a work-in-progress script but basic functionality is already given. If you call the script like

`python thread-watcher.py -b vg -q mhg -f queue.txt -n "Monster Hunter"`

then it looks for all threads that include `mhg` inside the `vg` board, stores the thread url into `queue.txt` and adds `/Monster-Hunter` at the end of the url so that you can use the --use-names argument from the actual download script.

### Legacy ###

The current scripts are written in python3, in case you still use python2 you can use an old version of the script inside the legacy directory.

### TODO ###

fix duplicated filenames when running with `--title`
