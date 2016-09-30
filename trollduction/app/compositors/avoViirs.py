import mpop.imageo.geo_image as geo_image
#from PIL import Image
from pydecorate import DecoratorAGG
import aggdraw
from trollimage.colormap import rdbu

def avoir(self):
    """Make a black and white image of the IR 10.8um channel (320m).
    """
    self.check_channels("M15")

    img = geo_image.GeoImage(self["M15"].data,
                                self.area,
                                self.time_slot,
                                fill_value=0,
                                mode="L",
                                crange=(-70 + 273.15, 57.5 + 273.15))

    # trim data to -65 - 30 c
    img.stretch_linear("M15", 5/127.5, 22.5/127.5)

    # clouds should be white
    img.enhance(inverse=True)

    # couldn't get this working in the l2processor config
    img.add_overlay(color=(255,255,255))

    pil_img = img.pil_image()
    pil_img.format = "PNG"
    dc = DecoratorAGG(pil_img)
    dc.align_bottom()

    font=aggdraw.Font("blue","/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",size=16)
    dc.add_text("2099/09/09 01:66:66 UTC Suomi-NPP VIIRS thermal infrared brightness temperature(C)",
font=font)
    dc.add_scale(rdbu, extend=True)

    return img

avoir.prerequisites = set(["M15"])

viirs = [avoir]
