import mpop.imageo.geo_image as geo_image
#from PIL import Image
from pydecorate import DecoratorAGG
import aggdraw
from trollimage.colormap import rdgy
from trollimage.colormap import Colormap
from trollsched.satpass import Pass
from pprint import pprint
from mpop.projector import get_area_def


C0 = 273.15

def avoir(self):
    """Make a black and white image of the IR 10.8um channel (320m).
       Modeled after mpop.instruments.viirs.ir108
    """
    self.check_channels("M15")
    data = self["M15"].data
    range = (-65 + C0, 35 + C0)
    img = geo_image.GeoImage((data, data, data),
                                self.area,
                                self.time_slot,
                                fill_value=None,
                                mode="RGB",
                                crange=(range, range, range))
    # clouds should be white
    img.enhance(inverse=True)

    return img
avoir.prerequisites = set(["M15"])


def avoirhr(self):
    """Make a black and white image of the IR 10.8um channel (320m).
       Modeled after mpop.instruments.viirs.ir108
    """
    self.check_channels("I05")
    data = self["I05"].data
    range = (-65 + C0, 35 + C0)
    img = geo_image.GeoImage((data, data, data),
                                self.area,
                                self.time_slot,
                                fill_value=None,
                                mode="RGB",
                                crange=(range, range, range))
    # clouds should be white
    img.enhance(inverse=True)

    return img
avoirhr.prerequisites = set(["I05"])


def avovis(self):
    """Make a black and white image of the IR 10.8um channel (320m).
       Modeled after mpop.instruments.viirs.ir108
    """
    self.check_channels("I01")
    data = self["I01"].data
    range = (0 + C0, 100 + C0)
    img = geo_image.GeoImage((data, data, data),
                                self.area,
                                self.time_slot,
                                fill_value=None,
                                mode="RGB",
                                crange=(range, range, range))
    # clouds should be white
    img.enhance(inverse=True)

    return img
avovis.prerequisites = set(["I01"])


def avomir(self):
    """Make a black and white image of the IR 10.8um channel (320m).
       Modeled after mpop.instruments.viirs.ir108
    """
    self.check_channels("I04")
    data = self["I04"].data
    range = (-50 + C0, 50 + C0)
    img = geo_image.GeoImage((data, data, data),
                                self.area,
                                self.time_slot,
                                fill_value=None,
                                mode="RGB",
                                crange=(range, range, range))
    return img
avomir.prerequisites = set(["I04"])
avomir.colormap = Colormap((0.0, (0.0, 0.0, 0.0)),
                           (1.0, (1.0, 1.0, 1.0)))


def avobtd(self):
    """Make BTD composite.
    """
    self.check_channels('M15', 'M16')
    img = geo_image.GeoImage(self["M15"].data - self["M16"].data,
                             self.area,
                             self.time_slot,
                             fill_value=None,
                             mode="L",
                             crange=(-6, 5))
    img.colorize(avobtd.colormap)
    return img
avobtd.prerequisites = set(["M15", "M16"])
avobtd.colormap = Colormap((0.0, (0.5, 0.0, 0.0)),
                           (0.078571, (1.0, 0.0, 0.0)),
                           (0.157142, (1.0, 0.5, 0.0)),
                           (0.235713, (1.0, 1.0, 0.0)),
                           (0.314284, (0.5, 1.0, 0.5)),
                           (0.392855, (0.0, 1.0, 1.0)),
                           (0.471426, (0.0, 0.5, 1.0)),
                           (0.549997, (0.0, 0.0, 1.0)),
                           (0.5500, (0.5, 0.5, 0.5)),
                           (1.0, (1.0, 1.0, 1.0)))


viirs = [avoir, avoirhr, avobtd, avovis, avomir]
