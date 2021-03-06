#!/usr/bin/env python

import json
from posttroll.subscriber import Subscribe
from posttroll.message import datetime_encoder
from pprint import pprint
from mpop.satellites import PolarFactory
from datetime import timedelta, datetime
from dateutil import parser
from pyorbital.orbital import Orbital
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
import tomputils.mattermost as mm
from trollimage import colormap
import sys
import traceback
import argparse

PRODUCTS = {'ir108': 'TIR',
            'ir108hr': 'TIR',
            'truecolor': 'VIS',
            'dnb': 'VIS',
            'btd': 'ASH',
            'vis': 'VIS',
            'mir': 'MIR'}
ORBIT_SLACK = timedelta(minutes=30)
GRANULE_SPAN = timedelta(seconds=85.4)
GOLDENROD = (218, 165, 32)
PNG_DIR = '/data/viirs/png'
PNG_DEV_DIR = '/data/viirs/png-dev'
SECTORS = (('AKSC', '1km'),
           ('AKAP', '1km'),
           ('AKEA', '1km'),
           ('AKWA', '1km'),
           ('RUKA', '1km'),
           ('AKAL', '2km'),
           ('AKGA', '2km'),
           ('AKIN', '2km'),
           ('AKSE', '2km'),
           ('AKNP', '5km'),
           ('AKCL', '250m'),
           ('AKPV', '250m'),
           ('AKVN', '250m'),
           ('AKSH', '250m'),
           ('AKBO', '250m'),
           ('AKCE', '250m'),
           ('AKCH', '250m'),
           ('AKGS', '250m'),
           ('BERS', '2km'),
           ('AKNS', '2km'),
           ('CNMI', '1km'),
           ('RUKA', '2km'),
           ('RUKI', '2km'),
           ('RUNP', '5km'))
TYPEFACE = "/app/fonts/Cousine-Bold.ttf"


class AvoProcessor(object):
    def __init__(self, args):
        self.mattermost = mm.Mattermost()
        self.product = args.product

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
        start_slack = start - ORBIT_SLACK
        print ("start %s :: %s" % (start_slack, type(start_slack)))
        print ("end %s :: %s" % (end, type(end)))
        overpass = Pass(platform_name, start_slack, end, instrument='viirs')
        previous_overpass = Pass(platform_name, start_slack - GRANULE_SPAN,
                                 end - GRANULE_SPAN, instrument='viirs')

        images = []
        colorbar_text_color = GOLDENROD
        img_colormap = None
        dev = False
        for (sector, size) in SECTORS:
            size_sector = size+sector
            sector_def = get_area_def(size_sector)
            coverage = overpass.area_coverage(sector_def)
            previous_coverage = previous_overpass.area_coverage(sector_def)
            print "%s coverage: %f" % (size_sector, coverage)

            if coverage < .1 or not coverage > previous_coverage:
                continue
            images.append((size_sector, coverage * 100))

            global_data = PolarFactory.create_scene(platform_name, "", "viirs",
                                                    start_slack,
                                                    data["orbit_number"])
            label = platform_name + " "

            if self.product == 'ir108':
                global_data.load(global_data.image.avoir.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                img = local_data.image.avoir()
                label += "VIIRS thermal infrared brightness temperature(C)"
                colormap.greys.set_range(-65, 35)
                img_colormap = colormap.greys
                tick_marks = 10
                minor_tick_marks = 5
            elif self.product == 'ir108hr':
                global_data.load(global_data.image.avoirhr.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                img = local_data.image.avoirhr()
                label += "VIIRS HR thermal infrared brightness temperature(C)"
                colormap.greys.set_range(-65, 35)
                img_colormap = colormap.greys
                tick_marks = 10
                minor_tick_marks = 5
            elif self.product == 'vis':
                global_data.load(global_data.image.avovis.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                img = local_data.image.avovis()
                label += "VIIRS visible reflectance (percent)"
                colormap.greys.set_range(0, 100)
                img_colormap = colormap.greys
                tick_marks = 20
                minor_tick_marks = 10
            elif self.product == 'mir':
                global_data.load(global_data.image.avomir.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                img = local_data.image.avomir()
                label += "VIIRS mid-infrared brightness temperature (c)"
                global_data.image.avomir.colormap.set_range(-50, 50)
                img_colormap = global_data.image.avomir.colormap
                tick_marks = 20
                minor_tick_marks = 10
            elif self.product == 'truecolor':
                global_data.load(global_data.image.truecolor.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                img = local_data.image.truecolor()
                label += "VIIRS true color"
            elif self.product == 'dnb':
                global_data.load(global_data.image.avodnb.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                size = local_data.channels[0].data.size
                data_size = local_data.channels[0].data.count()

                if float(data_size) / size < .1:
                    continue
                img = local_data.image.avodnb()
                img.enhance(stretch='linear')
                label += "VIIRS day/night band"
                dev = True
            elif self.product == 'btd':
                global_data.load(global_data.image.avobtd.prerequisites,
                                 time_interval=(start_slack, end))
                local_data = global_data.project(size_sector)
                img = local_data.image.avobtd()
                label += "VIIRS brightness temperature difference"
                img_colormap = global_data.image.avobtd.colormap
                # set_range disabled while troubleshooting image contrast
                img_colormap.set_range(-6,5)
                tick_marks = 1
                minor_tick_marks = .5
                colorbar_text_color = (0,0,0)
            else:
                raise Exception("unknown product")

            if platform_name == 'NOAA-20':
                label += " Preliminary, Non-Operational Data"
            img.add_overlay(color=GOLDENROD)
            pilimg = img.pil_image()
            dc = DecoratorAGG(pilimg)
            dc.align_bottom()

            font = aggdraw.Font(colorbar_text_color, TYPEFACE, size=14)
            if img_colormap is not None:
                dc.add_scale(img_colormap, extend=True, tick_marks=tick_marks,
                             minor_tick_marks=minor_tick_marks, font=font,
                             height=20, margins=[1, 1], )
                dc.new_line()

            lat = float(sector_def.proj_dict['lat_0'])
            lon = float(sector_def.proj_dict['lon_0'])
            passes = Orbital(platform_name).get_next_passes(start_slack, 1,
                                                          lon, lat, 0)
            if passes is not None:
                file_start = passes[0][0]
            else:
                file_start = start
            start_string = file_start.strftime('%m/%d/%Y %H:%M UTC')
            font = aggdraw.Font(GOLDENROD, TYPEFACE, size=14)
            dc.add_text(start_string + " " + label, font=font, height=30,
                        extend=True, bg_opacity=128, bg='black')

            if dev:
                filepath = os.path.join(PNG_DEV_DIR, sector)
            else:
                filepath = os.path.join(PNG_DIR, sector)

            if not os.path.exists(filepath):
                print("Making out dir " + filepath)
                os.makedirs(filepath)

            #filename = "%s-%s-%s.png" % (size_sector,
            #                             self.product,
            #                             file_start.strftime('%Y%m%d-%H%M'))

            filename = "%s.viirs.--.--.%s.%s.png" % (
                file_start.strftime('%Y%m%d.%H%M'), size_sector, PRODUCTS[self.product])


            filepath = os.path.join(filepath, filename)

            print("Saving to %s" % filepath)
            pilimg.save(filepath)

        proc_end = datetime.now()
        if len(images) < 1:
            msg = "### :hourglass: Granule covers no sectors."
        else:
            msg = "### :camera: New image"
            msg += "\n\n| Sector | Coverage (%) |"
            msg += "\n|:-------|:------------:|"
            for (sector, coverage) in images:
                msg += '\n| %s | %d |' % (sector, coverage)
        msg += "\n**Granule span** %s" % mm.format_span(start, end)
        delta = mm.format_timedelta(proc_end - proc_start)
        span = mm.format_span(proc_start, proc_end)
        msg += '\n**Processing time** %s (%s)' % (delta, span)
        delta = mm.format_timedelta(proc_end - start)
        msg += '\n**Accumulated delay** %s' % delta
        self.mattermost.post(msg)


def arg_parse():

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-p', '--product', choices=dict.keys(PRODUCTS),
                        help="product to produce", required=True)

    return arg_parser.parse_args()


def main():
    args = arg_parse()
    processor = AvoProcessor(args)

    topic = "pytroll://%s-EARS/viirs/1b" % args.product
    with Subscribe('', topic, True) as sub:
        for msg in sub.recv():
            try:
                processor.process_message(msg)
            except:  # catch *all* exceptions
                errmsg = "### Unexpected error "
                errmsg += "\n**Product** %s" % args.product
                e = sys.exc_info()
                if len(e) == 3:
                    errmsg += '\n %s' % e[1]
                    errmsg += '\n %s' % traceback.format_exc()
                processor.mattermost.post(errmsg)


if __name__ == '__main__':
    main()
