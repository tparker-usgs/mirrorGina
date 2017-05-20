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
import logging
import os.path
import os
import posixpath
from datetime import timedelta, datetime
from urlparse import urlparse
import cStringIO
import pycurl
import mattermost as mm
import hashlib
import socket
import viirs
from db import Db
import h5py

DEFAULT_BACKFILL = 2
DEFAULT_NUM_CONN = 5

INSTRUMENTS = {'viirs': {
    'name': 'viirs',
    'level': 'level1',
    'out_path': 'viirs/sdr',
    'match': '/(SVM15|GMTCO)_'
    }}

FACILITIES = ('uafgina', 'gilmore')
GINA_URL = ('http://nrt-status.gina.alaska.edu/products.json'
            + '?action=index&commit=Get+Products&controller=products')
OUT_DIR = os.path.join(os.environ['BASE_DIR'], 'data')
DB_DIR = os.path.join(os.environ['BASE_DIR'], 'db')


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

        self.out_path = os.path.join(OUT_DIR, self._instrument['out_path'], self.args.facility)
        if not os.path.exists(self.out_path):
            self.logger.debug("Making out dir " + self.out_path)
            os.makedirs(self.out_path)

        self.conn = Db(DB_DIR)
        self.mattermost = mm.Mattermost(verbose=True)
        # self.mattermost.set_log_level(logging.DEBUG)

        self.hostname = socket.gethostname()

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

    def get_file_list(self):
        self.logger.debug("fetching files")	
        backfill = timedelta(days=self._backfill)
        end_date = datetime.utcnow() + timedelta(days=1)
        start_date = end_date - backfill

        url = GINA_URL
        url += '&start_date=' + start_date.strftime('%Y-%m-%d')
        url += '&end_date=' + end_date.strftime('%Y-%m-%d')
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
        files = sorted(files, key=lambda k: k['url'], cmp=viirs.filename_comparator)
        return files

    def path_from_url(self, url):
        path = urlparse(url).path
        filename = posixpath.basename(path)

        return os.path.join(self.out_path, filename)

    def queue_files(self, file_list):

        queue = []
        pattern = re.compile(self._instrument['match'])
        self.logger.debug("%d files before pruning", len(file_list))
        for new_file in file_list:
            out_path = self.path_from_url(new_file['url'])

            if pattern.search(out_path) and not os.path.exists(out_path):
                self.logger.debug("Queueing %s", out_path)
                queue.append((new_file, out_path))
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

    def _log_sighting(self, filename, status_code, success, message=None):
        sight_date = datetime.utcnow()
        granule = viirs.Viirs(filename)
        proc_time = granule.proc_date - granule.start
        trans_time = sight_date - granule.proc_date

        if not success:
            msg = '### :x: Failed file: %s %d %s\n' % (granule.channel, granule.orbit, granule.start)
            if message is not None:
                msg += '**Message** %s\n' % message
            msg += '**Processing delay** %s' % mm.format_timedelta(proc_time)
        else:

            pause = timedelta(hours=1)

            # post new orbit messasge
            orbit_proc_time = self.conn.get_orbit_proctime(self.args.facility, granule)
            granule_proc_time = self.conn.get_granule_proctime(self.args.facility, granule)

            if orbit_proc_time is None:
                orb_msg = '### :earth_americas: New orbit from %s: %d' % (self.args.facility, granule.orbit)
            elif orbit_proc_time + pause < granule.proc_date:
                orb_msg = '### :snail: _Reprocessed orbit_ from %s: %d' % (self.args.facility, granule.orbit)
            else:
                orb_msg = None

            if orb_msg:
                orb_msg += '\n**First granule** %s (%s)' % (mm.format_span(granule.start, granule.end), granule.channel)
                count = self.conn.get_orbit_granule_count(granule.orbit - 1, self.args.facility)
                orb_msg += '\n**Granules seen from orbit %d** %d' % (granule.orbit - 1, count)
                self.mattermost.post(orb_msg)

            # post new granule message
            if granule_proc_time is None:
                msg = '### :satellite: New granule from %s\n' % self.args.facility
            elif granule_proc_time + pause < granule.proc_date:
                msg = '### :snail: _Reprocessed granule_ from %s\n' % self.args.facility
            else:
                msg = None

            if msg:
                msg += '**Granule span** %s (%s)\n' % (mm.format_span(granule.start, granule.end), mm.format_timedelta(granule.end - granule.start))
                granule_proc_time = self.conn.get_granule_proctime(self.args.facility, granule)
                msg += '**Processing delay** %s\n' % mm.format_timedelta(proc_time)
                msg += '**Transfer delay** %s\n' % mm.format_timedelta(trans_time)

                if message:
                    msg += "\n**Message: %s" % message

        if 'msg' in locals() and msg is not None:
            self.mattermost.post(msg)
            self.conn.insert_obs(self.args.facility, granule, sight_date, status_code, success)

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
                new_file, filename = file_queue.pop(0)
                url = new_file['url']
                c = freelist.pop()
                c.fp = open(filename, "wb")
                c.setopt(pycurl.URL, url.encode('ascii', 'replace'))
                c.setopt(pycurl.WRITEDATA, c.fp)
                m.add_handle(c)
                self.logger.debug("added handle")
                # store some info
                c.filename = filename
                c.url = url
                c.md5 = new_file['md5sum']
            while 1:
                ret, num_handles = m.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break
            while 1:
                num_q, ok_list, err_list = m.info_read()
                for c in ok_list:
                    print("Success:", c.filename, c.url, c.getinfo(pycurl.EFFECTIVE_URL))
                    status_code = c.getinfo(pycurl.HTTP_CODE)
                    c.fp.close()
                    file_md5 = hashlib.md5(open(c.filename, 'rb').read()).hexdigest()
                    self.logger.debug(str(c.md5) + " : " + str(file_md5))

                    if c.md5 == file_md5:
                        try:
                            h5f = h5py.File(c.filename, 'r')
                            success = True
                            errmsg = None
                        except:
                            success = False
                            errmsg = 'Good checksum, bad format.'
                            os.unlink(c.filename)
                    else:
                        success = False
                        errmsg = 'Bad checksum'
                        os.unlink(c.filename)

                    c.fp = None
                    m.remove_handle(c)
                    freelist.append(c)
                    self._log_sighting(c.filename, status_code, success, message=errmsg)

                for c, errno, errmsg in err_list:
                    print("Failed:", c.filename, c.url, errno, errmsg)
                    status_code = c.getinfo(pycurl.HTTP_CODE)
                    self._log_sighting(c.filename, status_code, False, message=errmsg)
                    c.fp.close()
                    os.unlink(c.filename)
                    c.fp = None
                    m.remove_handle(c)
                    freelist.append(c)
                num_processed += len(ok_list) + len(err_list)
                if num_q == 0:
                    break



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
    parser.add_argument('-f', '--facility', choices=FACILITIES,
                        help="facility to query", required=True)
    parser.add_argument('instrument', choices=INSTRUMENTS.keys(),
                        help="instrument to query")

    return parser.parse_args()


def main():
    args = arg_parse()

    mirror_gina = MirrorGina(args)
    mirror_gina.fetch_files()

if __name__ == "__main__":
    main()
