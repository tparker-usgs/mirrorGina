#!/usr/bin/env python

# -*- coding: utf-8 -*-

# I waive copyright and related rights in the this work worldwide
# through the CC0 1.0 Universal public domain dedication.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

# Author(s):
#   Tom Parker <tparker@usgs.gov>

"""Retrieve files from GINA
"""


import argparse
import re
import json
import signal
import sys
import logging
import os.path
import posixpath
from datetime import timedelta, datetime
from urlparse import urlparse

import cStringIO
import pycurl


DEFAULT_BACKFILL = 2
DEFAULT_NUM_CONN = 5

INSTRUMENTS = {'viirs':{
    'name':'viirs', 'level':'level1', 'out_path':'viirs/sdr', 
    'match':'/(SVM02|SVM03|SVM04|SVM05|SVM14|SVM15|SVM16|GMTCO)_'
    }}
GINA_URL = ('http://nrt-status.gina.alaska.edu/products.json' +
            '?action=index&commit=Get+Products&controller=products')
OUT_DIR = '/data'


class MirrorGina(object):

    def __init__(self, args):
        self.logger = logging.getLogger('MirrorGina')

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        self.logger.addHandler(ch)

        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)   
            self.logger.info("Verbose logging")
        else:
            logging.getLogger().setLevel(logging.INFO)

        # We should ignore SIGPIPE when using pycurl.NOSIGNAL - see
        # the libcurl tutorial for more info.
        try:
            signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        except ImportError:
            pass

        self._instrument = INSTRUMENTS[args.instrument]
        self.logger.debug("instrument: %s", self._instrument)

        self._num_conn = args.num_conn
        self.logger.debug("num_conn: %s", self._num_conn)

        self._backfill = args.backfill
        self.logger.debug("backfill: %s", self._backfill)

	out_path = os.path.join(OUT_DIR, self._instrument['out_path'])
	if not os.path.exists(out_path):
		os.makedirs(out_path)



    def get_file_list(self):

        self.logger.debug("fetching files")	
        backfill = timedelta(days=self._backfill)
        endDate = datetime.utcnow() + timedelta(days=1)
        startDate =  endDate - backfill

        url = GINA_URL 
        url += '&start_date=' + startDate.strftime('%Y-%m-%d')
        url += '&end_date=' + endDate.strftime('%Y-%m-%d')
        url += '&sensors[]=' + self._instrument['name']
        url += '&processing_levels[]=' + self._instrument['level']

        self.logger.debug("URL: %s", url)
        buf = cStringIO.StringIO()

        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.perform()

        files = json.loads(buf.getvalue())
        buf.close()

        self.logger.info("Found %s files", len(files))
        return files


    def path_from_url(self, url):

        path = urlparse(url).path
        file = posixpath.basename(path)

        return os.path.join(OUT_DIR, self._instrument['out_path'], file)


    def queue_files(self, file_list):

        queue = []
        pattern = re.compile(self._instrument['match'])
        self.logger.debug("%d files before pruning", len(file_list))
        for file in file_list:
            out_path = self.path_from_url(file['url'])

            if pattern.search(out_path) and not os.path.exists(out_path):
                self.logger.debug("Queueing %s", out_path)
                queue.append((file['url'], out_path))
            else:
                self.logger.debug("Skipping %s", out_path)

        self.logger.debug("%d files after pruning", len(queue))
        return queue


    def create_multi(self):
        m = pycurl.CurlMulti()
        m.handles = []
        for i in range(self._num_conn):
            self.logger.debug("creating curl object")
            c = pycurl.Curl()
            c.fp = None
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.MAXREDIRS, 5)
            c.setopt(pycurl.CONNECTTIMEOUT, 30)
            c.setopt(pycurl.TIMEOUT, 300)
            c.setopt(pycurl.NOSIGNAL, 1)
            m.handles.append(c)

        return m


    def fetch_files(self):
        # modeled after retiever-multi.py from pycurl
        file_list = self.get_file_list()
        file_queue = self.queue_files(file_list)

        m = self.create_multi()

        freelist = m.handles[:]
        num_processed = 0
        num_files = len(file_queue)
        self.logger.debug("Fetching %d files with %d connections.", num_files, len(freelist))
        while num_processed < num_files:
            # If there is an url to process and a free curl object, add to multi stack
            while file_queue and freelist:
                url, filename = file_queue.pop(0)
                c = freelist.pop()
                c.fp = open(filename, "wb")
                c.setopt(pycurl.URL, url.encode('ascii', 'replace'))
                c.setopt(pycurl.WRITEDATA, c.fp)
                m.add_handle(c)
                self.logger.debug("added handle")
                # store some info
                c.filename = filename
                c.url = url
            # Run the internal curl state machine for the multi stack
            while 1:
                ret, num_handles = m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break
            # Check for curl objects which have terminated, and add them to the freelist
            while 1:
                num_q, ok_list, err_list = m.info_read()
                for c in ok_list:
                    c.fp.close()
                    c.fp = None
                    m.remove_handle(c)
                    print("Success:", c.filename, c.url, c.getinfo(pycurl.EFFECTIVE_URL))
                    freelist.append(c)
                for c, errno, errmsg in err_list:
                    c.fp.close()
                    c.fp = None
                    m.remove_handle(c)
                    print("Failed: ", c.filename, c.url, errno, errmsg)
                    freelist.append(c)
                num_processed += len(ok_list) + len(err_list)
                if num_q == 0:
                    break
            # Currently no more I/O is pending, could do something in the meantime
            # (display a progress bar, etc.).
            # We just call select() to sleep until some more data is available.
            m.select(1.0)

        # Cleanup
        self.logger.debug("cleaning up")
        for c in m.handles:
            if c.fp is not None:
                c.fp.close()
                c.fp = None
            c.close()
        m.close()

# Get args
def arg_parse():

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--num_conn", 
                        help="# of concurrent connections", type=int, 
                        default=DEFAULT_NUM_CONN)
    parser.add_argument("-b", "--backfill", 
                        help="# of days to back fill", 
                        type=int, default=DEFAULT_BACKFILL)
    parser.add_argument("-v", "--verbose", 
                        help="Verbose logging", 
                        action='store_true')
    parser.add_argument('instrument', choices=INSTRUMENTS.keys(), 
                        help="instrument to query")

    return parser.parse_args()


def main():
    args = arg_parse()

    mirrorGina = MirrorGina(args)
    mirrorGina.fetch_files()


if __name__ == "__main__":
    main()
