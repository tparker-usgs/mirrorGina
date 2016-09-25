def avoir(self):
    """Make a black and white image of the IR 10.8um channel (320m).
    """
    self.check_channels("I05")

    img = geo_image.GeoImage(self["I05"].data,
                                self.area,
                                self.time_slot,
                                fill_value=0,
                                mode="L",
                                crange=(-70 + 273.15, 57.5 + 273.15))
    img.enhance(inverse=True)
    return img

avoir.prerequisites = set(["I05"])

viirs = [avoir]
