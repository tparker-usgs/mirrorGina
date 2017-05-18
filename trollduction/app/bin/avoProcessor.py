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


ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4
                         )
def process_message(msg):
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

    print ("start %s :: %s" % (start, type(start)))
    print ("end %s :: %s" % (end, type(end)))

    overpass = Pass(platform_name, start, end, instrument='viirs')
    coverage = overpass.area_coverage(get_area_def("AKSC"))
    print "COVERAGE: %f" % coverage

    global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", start, data["orbit_number"])
    global_data.load(global_data.image.avoir.prerequisites, time_interval=(start, end))
    local_data = global_data.project("AKSC")

    img = global_data.image.avoir()
    img.save("/tmp/img.png")


def main():
    with Subscribe('', "pytroll://ir108-EARS/Suomi-NPP/viirs/1b", True) as sub:
        for msg in sub.recv():
            process_message(msg)


if __name__ == '__main__':
    main()
