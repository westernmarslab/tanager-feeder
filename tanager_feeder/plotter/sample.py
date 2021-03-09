import colorutils
import numpy as np


class Sample:
    def __init__(self, name, file, title):
        self.title = title
        self.name = name
        self.file = file
        self.data = {}
        self.geoms = []
        self.linestyle = "-"
        self.markerstyle = "o"
        self.colors = None
        self.white_colors = None
        self.index = None
        self.white_index = None

    def add_spectrum(self, geom, reflectance, wavelengths):
        self.geoms.append(geom)
        self.data[geom] = {"reflectance": [], "wavelength": []}
        self.data[geom]["reflectance"] = reflectance
        self.data[geom]["wavelength"] = wavelengths

    def set_linestyle(self, linestyle):
        self.linestyle = linestyle

    def set_markerstyle(self, markerstyle):
        self.markerstyle = markerstyle

    def add_offset(self, offset, y_axis):
        try:
            offset = float(offset)
        except ValueError:
            print("Error: Invalid offset")
            return

        for spec_label in self.data:
            if y_axis in self.data[spec_label]:
                old = np.array(self.data[spec_label][y_axis])
                self.data[spec_label][y_axis] = old + offset

    # generate a list of hex colors that are evenly distributed from dark to light across a single hue.
    def set_colors(self, hue):

        if len(self.geoms) > 3:
            N = len(self.geoms) / 2
            if len(self.geoms) % 2 != 0:
                N += 1
            N = int(N) + 2

            hsv_tuples = [(hue, 1, x * 1.0 / N) for x in range(4, N)]
            hsv_tuples = hsv_tuples + [(hue, (N - x) * 1.0 / N, 1) for x in range(N)]
            self.colors = []
            for h_tuple in hsv_tuples:
                self.colors.append(colorutils.hsv_to_hex(h_tuple))

            N = N + 2
            white_hsv_tuples = [(hue, 1, x * 1.0 / N) for x in range(1, N)]
            white_hsv_tuples = white_hsv_tuples + [(hue, (N - x) * 1.0 / N, 1) for x in range(N - 4)]
            self.white_colors = []
            for wh_tuple in white_hsv_tuples:
                self.white_colors.append(colorutils.hsv_to_hex(wh_tuple))

        # For small numbers of spectra, you end up with a couple extra and the first plotted are darker than you want.
        elif len(self.geoms) == 3:
            self.colors = []
            self.colors.append(colorutils.hsv_to_hex((hue, 1, 0.8)))  # dark spectrum
            self.colors.append(colorutils.hsv_to_hex((hue, 0.8, 1)))
            self.colors.append(colorutils.hsv_to_hex((hue, 0.3, 1)))  # light spectrum

            self.white_colors = []

            self.white_colors.append(colorutils.hsv_to_hex((hue, 1, 0.6)))  # dark spectrum
            self.white_colors.append(colorutils.hsv_to_hex((hue, 1, 0.9)))
            self.white_colors.append(colorutils.hsv_to_hex((hue, 0.5, 1)))  # light spectrum

        elif len(self.geoms) == 2:
            self.colors = []
            self.colors.append(colorutils.hsv_to_hex((hue, 1, 0.9)))  # dark spectrum
            self.colors.append(colorutils.hsv_to_hex((hue, 0.5, 1)))

            self.white_colors = []
            self.white_colors.append(colorutils.hsv_to_hex((hue, 0.7, 1)))  # light spectrum
            self.white_colors.append(colorutils.hsv_to_hex((hue, 1, 0.8)))  # dark spectrum
        elif len(self.geoms) == 1:
            self.colors = []
            self.colors.append(colorutils.hsv_to_hex((hue, 1, 1)))

            self.white_colors = []
            self.white_colors.append(colorutils.hsv_to_hex((hue, 1, 0.7)))

        self.index = -1
        self.white_index = -1

        # self.__next_color=self.colors[0]

    def restart_color_cycle(self):
        self.index = -1
        self.white_index = -1

    def next_color(self):
        self.index += 1
        self.index = self.index % len(self.colors)
        return self.colors[self.index]

    def next_white_color(self):
        self.white_index += 1
        self.white_index = self.index % len(self.white_colors)
        return self.white_colors[self.white_index]
