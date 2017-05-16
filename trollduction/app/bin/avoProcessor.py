#!/usr/bin/env python

import json
from posttroll.subscriber import Subscribe
from posttroll.message import datetime_encoder
from pprint import pprint
from mpop.satellites import PolarFactory
import datetime
import dateutil.parser
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

# def object_hook(obj):
#     _spec_type = obj.get('_spec_type')
#     if not _spec_type:
#         return obj
#
#     if _spec_type in CONVERTERS:
#         return CONVERTERS[_spec_type](obj['val'])
#     else:
#         raise Exception('Unknown {}'.format(_spec_type))


def main():
    with Subscribe('', "pytroll://ir108-EARS/Suomi-NPP/viirs/1b", True) as sub:
        for msg in sub.recv():
            datas = json.dumps(msg.data, default=datetime_encoder)
            data = json.loads(datas)
            pprint(data)
            # platform_name = data["platform_name"]
            # orbit = data["orbit_number"]
            start_date = dateutil.parser.parse(data["start_date"])
            start_time = dateutil.parser.parse(data["collection"][0]["start_time"])
            start_time = datetime.datetime.combine(start_date, start_time.time())

            print "START: %s" + str(start_time)
            print 'START: %s' % type(start_time)
            # print "END: " + str(end_time) + "\n"
            # overpass = Pass(platform_name, start_time, end_time)
            # coverage = overpass.area_coverage(get_area_def("AKSC")) * 100
            # print "COVERAGE: " + str(coverage) + "%\n"
            #
            # global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", end_time, orbit)
            # global_data.load(["M15"], time_interval=(start_time, end_time))
            # local_data = global_data.project("AKSC", mode="nearest")
            # img = local_data.iamge
            # img.save("/tmp/out.png")


if __name__ == '__main__':
    main()