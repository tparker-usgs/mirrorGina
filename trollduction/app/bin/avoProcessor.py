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

# class MyJSONEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, (datetime.datetime,)):
#             return {"val": obj.isoformat(), "_spec_type": "datetime"}
#         elif isinstance(obj, (decimal.Decimal,)):
#             return {"val": str(obj), "_spec_type": "decimal"}
#         else:
#             return super().default(obj)
#
# def object_hook(obj):
#     _spec_type = obj.get('_spec_type')
#     if not _spec_type:
#         return obj
#
#     if _spec_type in CONVERTERS:
#         return CONVERTERS[_spec_type](obj['val'])
#     else:
#         raise Exception('Unknown {}'.format(_spec_type))

ORBIT_SLACK = timedelta(minutes=30)
def main():
    with Subscribe('', "pytroll://ir108-EARS/Suomi-NPP/viirs/1b", True) as sub:
        for msg in sub.recv():
            datas = json.dumps(msg.data, default=datetime_encoder)
            data = json.loads(datas)
            pprint(data)
            platform_name = data["platform_name"]
            # orbit = data["orbit_number"]
            start_date = parser.parse(data["start_date"])
            print "START: %s" % start_date
            #start = start_date - ORBIT_SLACK
            #end = start_date + ORBIT_SLACK
            start = start_date
            end = start_date + timedelta(minutes=1)
            print ("start %s :: %s" % (start, type(start)))
            print ("end %s :: %s" % (end, type(end)))
            # print "END: %s" % end_time)
            overpass = Pass(platform_name, start, end, instrument='viirs')
            coverage = overpass.area_coverage(get_area_def("AKSC")) 
            #coverage = overpass.area_coverage(get_area_def("AKSC")) * 100

            #print "COVERAGE: %s" % coverage
            #
            # global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", end_time, orbit)
            # global_data.load(["M15"], time_interval=(start_time, end_time))
            # local_data = global_data.project("AKSC", mode="nearest")
            # img = local_data.iamge
            # img.save("/tmp/out.png")


if __name__ == '__main__':
    main()
