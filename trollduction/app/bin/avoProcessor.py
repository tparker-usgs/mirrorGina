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
from trollimage import colormap
import sys

ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
PNG_DIR = '/data/viirs/png'
SECTORS = ('AKSC',
           'AKAP',
           'AKEA',
           'AKWA',
           'RUKA',
           'AKAL',
           'AKGA',
           'AKIN',
           'AKSE',
           'AKNP',
           'AKCL',
           'AKPV',
           'AKVN',
           'AKSH',
           'AKBO',
           'AKCE',
           'AKCH',
           'BERS',
           'AKNS',
           'CNMI',
           'RUKA2km',
           'RUKI',
           'RUNP')

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
        proc_start = datetime.now()
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
        previous_overpass = Pass(platform_name, start - GRANULE_SPAN, end - GRANULE_SPAN, instrument='viirs')

        images = []
        for sector in SECTORS:
            sector_def = get_area_def(sector)
            coverage = overpass.area_coverage(sector_def)
            previous_coverage = previous_overpass.area_coverage(sector_def)
            print "%s coverage: %f" % (sector, coverage)

            if coverage < .1 or not coverage > previous_coverage:
                continue

            global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", start, data["orbit_number"])
            global_data.load(global_data.image.avoir.prerequisites, time_interval=(start, end))
            local_data = global_data.project(sector)

            img = local_data.image.avoir().pil_image()

            dc = DecoratorAGG(img)
            dc.align_bottom()

            font=aggdraw.Font(0xff0000ff,"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",size=14)
            colormap.greys.set_range(30, -65)
            dc.add_scale(colormap.greys, extend=True, tick_marks=10, minor_tick_marks=5, font=font, height=20, margins=[1,1],)
            dc.new_line()
            dc.add_text("%s Suomi-NPP VIIRS thermal infrared brightness temperature(C)" % start, font=font, height=30, extend=True, bg_opacity=255, bg='black')

            filename = "%s-ir-%s.png" % (sector, parser.parse(data["start_date"]).strftime('%Y%m%d-%H%M'))
            filepath = os.path.join(PNG_DIR, filename)
            print("Saving to %s" % filepath)
            img.save(filepath)
            if images is None:
                images
            images.append((sector, coverage * 100))

        proc_end = datetime.now()
        if len(images) < 1:
            msg = "### :hourglass: Granule covers no sectors. (%s)" %  start
        else:
            msg = "### :camera: New images"
            msg += "\n\n| Sector | Coverage (%) |"
            msg += "\n|:-------|:------------:|"
            for (sector, coverage) in images:
                msg += '\n| %s | %d |' % (sector, coverage)
        msg += "\n**Granule span** %s" % mm.format_span(start, end)
        msg += '\n**Processing time** %s (%s)' % (mm.format_timedelta(proc_end - proc_start), mm.format_span(proc_start, proc_end))
        msg += '\n**Accumulated delay** %s' % (mm.format_timedelta(proc_end - start))
        self.mattermost.post(msg)

def main():
    processor = AvoProcessor()
    with Subscribe('', "pytroll://ir108-EARS/Suomi-NPP/viirs/1b", True) as sub:
        for msg in sub.recv():
            try:
                processor.process_message(msg)
            except:  # catch *all* exceptions
                e = sys.exc_info()[0]
                processor.mattermost.post("Error: %s" % e)


if __name__ == '__main__':
    main()
