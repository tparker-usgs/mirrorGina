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
import os
import posixpath
from datetime import timedelta, datetime
from urlparse import urlparse
import sqlite3
import requests
import cStringIO
import pycurl
from mattermost import Mattermost
import hashlib

DEFAULT_BACKFILL = 2
DEFAULT_NUM_CONN = 5

# INSTRUMENTS = {'viirs':{
#     'name':'viirs', 'level':'level1', 'out_path':'viirs/sdr',
#     'match':'/(SVM02|SVM03|SVM04|SVM05|SVM14|SVM15|SVM16|GMTCO)_'
#     }}
INSTRUMENTS = {'viirs':{
    'name':'viirs', 'level':'level1', 'out_path':'viirs/sdr',
    'match':'/(SVM05|GMTCO)_'
    }}
GINA_URL = ('http://nrt-status.gina.alaska.edu/products.json' +
            '?action=index&commit=Get+Products&controller=products')
#OUT_DIR = os.environ['OUT_DIR']
OUT_DIR = '/data'
DB_FILE = OUT_DIR + '/gina.db'

class MirrorGina(object):

    def __init__(self, args):
        self.args = args
        self.logger = self._setup_logging()

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
            self.logger.debug("Making out dir " + out_path)
            os.makedirs(out_path)

        self.conn = self._get_db_conn()
        self.mattermost = Mattermost(verbose=True)
        # self.mattermost.set_log_level(logging.DEBUG)



    def _setup_logging(self):
        logger = logging.getLogger('MirrorGina')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        if self.args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Verbose logging")
        else:
            logging.getLogger().setLevel(logging.INFO)

        return logger

    def _get_db_conn(self):
        conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sighting (
                        granule_date timestamp, 
                        granule_channel, 
                        sight_date timestamp, 
                        proc_date timestamp, 
                        size int,
                        status_code,
                        success,
                        PRIMARY KEY (granule_date, granule_channel));''')

        conn.commit()

        return conn


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
                queue.append((file, out_path))
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
            c.setopt(pycurl.TIMEOUT, 600)
            c.setopt(pycurl.NOSIGNAL, 1)
            m.handles.append(c)

        return m

    def _log_sighting(self, filename, size, statusCode, success, message = None):
        sightDate = datetime.utcnow()
        granuleDate = datetime.strptime(filename[-68:-50], 'd%Y%m%d_t%H%M%S%f')
        granuleChannel = filename[-78:-73]
        procDate = datetime.strptime(filename[-32:-13], '%Y%m%d%H%M%S%f')
        self.conn.execute('''INSERT OR IGNORE INTO sighting (granule_date, granule_channel, sight_date, proc_date, size, status_code, success) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', (granuleDate, granuleChannel, sightDate, procDate, size, statusCode, success))
        self.conn.commit()
        procTime = procDate - granuleDate
        transTime = sightDate - procDate
        if success:
            msg = 'New file: %s %s\n' % (granuleChannel, granuleDate)
            msg += '  processing delay:  %s\n' % format_timedelta(procTime)
            msg += '  transfer delay:  %s' % format_timedelta(transTime)
        else:
            msg = 'Failed file: %s %s\n' % (granuleChannel, granuleDate)
            msg += '  processing delay: %s' % format_timedelta(procTime)

        if message:
            msg += "\n  message: %s" % message

        self.mattermost.post(msg)


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
                file, filename = file_queue.pop(0)
                url = file['url']
                c = freelist.pop()
                c.fp = open(filename, "wb")
                c.setopt(pycurl.URL, url.encode('ascii', 'replace'))
                c.setopt(pycurl.WRITEDATA, c.fp)
                m.add_handle(c)
                self.logger.debug("added handle")
                # store some info
                c.filename = filename
                c.url = url
                c.md5 = file['md5sum']
            # Run the internal curl state machine for the multi stack
            while 1:
                ret, num_handles = m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break
            # Check for curl objects which have terminated, and add them to the freelist
            while 1:
                num_q, ok_list, err_list = m.info_read()
                for c in ok_list:
                    print("Success:", c.filename, c.url, c.getinfo(pycurl.EFFECTIVE_URL))
                    size = c.getinfo(pycurl.CONTENT_LENGTH_DOWNLOAD)
                    statusCode = c.getinfo(pycurl.HTTP_CODE)
                    c.fp.close()
                    c.fp = None
                    m.remove_handle(c)
                    freelist.append(c)
                    file_md5 = hashlib.md5(open(c.filename, 'rb').read()).hexdigest()
                    self.logger.debug(str(c.md5) + " : " + str(file_md5))
                    success = c.md5 == file_md5
                    self._log_sighting(c.filename, size, statusCode, success)


                for c, errno, errmsg in err_list:
                    print("Failed:", c.filename, c.url, errno, errmsg)
                    size = c.getinfo(pycurl.CONTENT_LENGTH_DOWNLOAD)
                    statusCode = c.getinfo(pycurl.HTTP_CODE)
                    self._log_sighting(c.filename, size, statusCode, False, message=errmsg)
                    sight_date = datetime.utcnow()
                    granule = c.filename[-68:-50]
                    proc_date = c.filename[-36:-13]
                    success = False
                    c.fp.close()
                    os.unlink(c.filename)
                    c.fp = None
                    m.remove_handle(c)
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
        self.conn.close()

def format_timedelta(timedelta):
    seconds = timedelta.total_seconds()

    days, r = divmod(seconds, 60 * 60 * 24)
    hours, r = divmod(r, 60 * 60)
    minutes, r = divmod(r, 60)
    seconds = r

    timestring = ''
    if days > 0:
        timestring += '%dd ' % days

    if hours > 0:
        timestring += '%dh ' % hours


    if minutes > 0:
        timestring += '%dm ' % minutes

    timestring += '%ds' % seconds

    return timestring

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
