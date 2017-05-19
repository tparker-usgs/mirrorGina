#!/usr/bin/env python

import json
from posttroll.subscriber import Subscribe
from posttroll.message import datetime_encoder
from pprint import pprint
from mpop.satellites import PolarFactory
from datetime import timedelta, datetime
from dateutil import parser
from mpop.utils import debug_on
from trollsched.satpass import Pass
from mpop.projector import get_area_def
import mpop.imageo.geo_image as geo_image
#from PIL import Image
from pydecorate import DecoratorAGG
import aggdraw
from trollimage.colormap import rdbu
from trollsched.satpass import Pass
from mpop.projector import get_area_def
import os
import os.path
import mattermost as mm

ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
PNG_DIR = '/data/viirs/png'

class AvoProcessor(object):
    def __init__(self):
        self.mattermost = mm.Mattermost(verbose=True)

    def process_message(self, msg):
        '''
        {u'dataset': [{u'uid': u'GMTCO_npp_d20170516_t2226438_e2228081_b28766_c20170516223539386762_cspp_dev.h5',
                       u'uri': u'/data/viirs/sdr/uafgina/GMTCO_npp_d20170516_t2226438_e2228081_b28766_c20170516223539386762_cspp_dev.h5'},
                      {u'uid': u'SVM05_npp_d20170516_t2226438_e2228081_b28766_c20170516223540162289_cspp_dev.h5',
                       u'uri': u'/data/viirs/sdr/uafgina/SVM05_npp_d20170516_t2226438_e2228081_b28766_c20170516223540162289_cspp_dev.h5'}],
         u'end_decimal': 1,
         u'end_time': u'2017-05-16T22:28:08.100000',
         u'orbit_number': 28766,
         u'orig_platform_name': u'npp',
         u'platform_name': u'Suomi-NPP',
         u'proctime': u'2017-05-16T22:35:39.386762',
         u'sensor': [u'viirs'],
         u'start_date': u'2017-05-16T22:26:43',
         u'start_decimal': 8,
         u'start_time': u'2017-05-16T22:26:43.800000'}
        '''

        datas = json.dumps(msg.data, default=datetime_encoder)
        print("datas: %s : %s" % (type(datas), datas))
        data = json.loads(datas)
        print("datas: %s " % type(data))
        pprint(data)
        platform_name = data["platform_name"]
        start = parser.parse(data["start_date"])
        end = start + GRANULE_SPAN
        start -= ORBIT_SLACK
        sector = 'AKSC'
        print ("start %s :: %s" % (start, type(start)))
        print ("end %s :: %s" % (end, type(end)))

        overpass = Pass(platform_name, start, end, instrument='viirs')
        coverage = overpass.area_coverage(get_area_def(sector))
        print "COVERAGE: %f" % coverage


        if coverage > .1:
            global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", start, data["orbit_number"])
            global_data.load(global_data.image.avoir.prerequisites, time_interval=(start, end))
            local_data = global_data.project(sector)

            img = local_data.image.avoir()
            filename = "AKSC-ir-%s.png" % parser.parse(data["start_date"]).strftime('%Y%m%d-%H%M')
            filepath = os.path.join(PNG_DIR, filename)
            print("Saving to %s" % filepath)
            img.save(filepath)

            msg = ':camera: New image for sector %s: %s' % (sector, filename)
            msg += '\n  coverage: %d' % int(coverage * 100)
            print "posting %s" % msg
            self.mattermost.post(msg)


def main():
    processor = AvoProcessor()
    with Subscribe('', "pytroll://ir108-EARS/Suomi-NPP/viirs/1b", True) as sub:
        for msg in sub.recv():
            processor.process_message(msg)


if __name__ == '__main__':
    main()
