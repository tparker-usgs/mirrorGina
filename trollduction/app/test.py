#!/usr/bin/env python

from mpop.satellites import PolarFactory
from datetime import datetime
from mpop.utils import debug_on
from trollsched.satpass import Pass
from mpop.projector import get_area_def

debug_on()

time_slot = datetime(2016, 9, 28, 21, 00, 43)
orbit = "25502"

global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", time_slot,
orbit)
global_data.load([10.8])
print global_data

overpass = Pass("Suomi-NPP", time_slot, time_slot, instrument="viirs")
print "Coverage: ",  overpass.area_coverage(get_area_def("AKSC"))

local_data = global_data.project("AKSC", mode="nearest")
img = local_data.image.avoir()
img.save ("/data/test.png")
