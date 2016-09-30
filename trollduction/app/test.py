#!/usr/bin/env python

from mpop.satellites import PolarFactory
from datetime import datetime
from mpop.utils import debug_on

debug_on()

time_slot = datetime(2016, 9, 28, 21, 00, 43)
orbit = "25502"

global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", time_slot,
orbit)
global_data.load([10.8])
print global_data

img = global_data.image.avoir()

