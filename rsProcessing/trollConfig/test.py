from mpop.satellites import PolarFactory 
from datetime import datetime
from mpop.utils import debug_on
debug_on()

time_slot = datetime(2016,8,1,22,16,52)
orbit ="24680"
global_data = PolarFactory.create_scene("Suomi-NPP", "", "viirs", time_slot, orbit)
global_data.load(["M14"], "true")
print global_data 
