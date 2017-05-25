import mpop.imageo.geo_image as geo_image
#from PIL import Image
from pydecorate import DecoratorAGG
import aggdraw
from trollimage.colormap import rdbu
from trollsched.satpass import Pass
from pprint import pprint
from mpop.projector import get_area_def

def avoir(self):
    """Make a black and white image of the IR 10.8um channel (320m).
       Modeled after mpop.instruments.viirs.ir108
    """
    self.check_channels("M15")
    data = self["M15"].data
    range = (-70 + 273.15, 57.5 + 273.15)
    img = geo_image.GeoImage((data, data, data),
                                self.area,
                                self.time_slot,
                                fill_value=None,
                                mode="RGB",
                                crange=(range, range, range))

    # trim data to -65 - 35 c
    img.stretch_linear(0, cutoffs=(5/255, 22.5/255))
    img.stretch_linear(1, cutoffs=(5/255, 22.5/255))
    img.stretch_linear(2, cutoffs=(5/255, 22.5/255))

    # clouds should be white
    img.enhance(inverse=True)

    img.add_overlay(color=(218,165,32))

    return img

avoir.prerequisites = set(["M15"])

viirs = [avoir]
