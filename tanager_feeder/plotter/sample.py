import colorutils
import numpy as np
from tanager_feeder import utils


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
        self.hue = None
        self.white_colors = None
        self.index = None
        self.white_index = None

    def add_spectrum(self, geom, reflectance, wavelengths):
        self.geoms.append(geom)
        self.data[geom] = {"reflectance": reflectance, "wavelength": wavelengths}

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

    def get_phase_angles(self):
        phase_angles = []
        dummy_phase = 0
        for geom in self.geoms:
            i, e, az = utils.get_i_e_az(geom)
            if i is not None and e is not None:
                g = utils.get_phase_angle(i, e, az)
                phase_angles.append(g)
            else:
                phase_angles.append(dummy_phase)  # dummy value
                dummy_phase += 1
        return phase_angles

    # generate a list of hex colors that are evenly distributed from dark to light across a single hue.
    # reorder the list such that high phase angles are light colored and small phase angles are dark.
    def set_colors(self, hue):
        self.hue = hue
        phase_angles = self.get_phase_angles()

        if len(self.geoms) > 3:
            # Generate a list of colors to use for plots on a dark background
            N = len(self.geoms) / 2
            if len(self.geoms) % 2 != 0:
                N += 1
            N = int(N) + 2
            hsv_tuples = [(hue, 1, x * 1.0 / N) for x in range(4, N)]
            hsv_tuples = hsv_tuples + [(hue, (N - x) * 1.0 / N, 1) for x in range(N)]

            # Generate a list of colors to use for plots on a white background
            N = N + 2
            white_hsv_tuples = [(hue, 1, x * 1.0 / N) for x in range(1, N)]
            white_hsv_tuples = white_hsv_tuples + [(hue, (N - x) * 1.0 / N, 1) for x in range(N - 4)]

            # For small numbers of spectra, you end up with a couple extra and the first plotted are darker than you want.
        elif len(self.geoms) == 3:
            hsv_tuples = []
            hsv_tuples.append((hue, 1, 0.8))  # dark spectrum
            hsv_tuples.append((hue, 0.8, 1))
            hsv_tuples.append((hue, 0.3, 1))  # light spectrum

            white_hsv_tuples = []
            white_hsv_tuples.append((hue, 1, 0.6))  # dark spectrum
            white_hsv_tuples.append((hue, 1, 0.9))
            white_hsv_tuples.append((hue, 0.5, 1))  # light spectrum

        elif len(self.geoms) == 2:
            hsv_tuples = []
            hsv_tuples.append((hue, 1, 0.9))  # dark spectrum
            hsv_tuples.append((hue, 0.5, 1))

            white_hsv_tuples = []
            white_hsv_tuples.append((hue, 0.7, 1))  # light spectrum
            white_hsv_tuples.append((hue, 1, 0.8))  # dark spectrum

        elif len(self.geoms) == 1:
            hsv_tuples = [(hue, 1, 1)]
            white_hsv_tuples = [(hue, 1, 0.7)]

        # Order colors to correspond to phase angles. light colors = high phase angles.
        sorted_phase_angles = sorted(phase_angles)
        self.colors = list(np.zeros(len(phase_angles)))
        self.white_colors = list(np.zeros(len(phase_angles)))
        for original_color_list_index, val in enumerate(sorted_phase_angles):
            final_color_list_index = phase_angles.index(val)
            phase_angles[final_color_list_index] = -10000000  # Never choose this index again.
            self.colors[final_color_list_index] = colorutils.hsv_to_hex(hsv_tuples[original_color_list_index])
            self.white_colors[final_color_list_index] = colorutils.hsv_to_hex(white_hsv_tuples[original_color_list_index])

        self.index = -1
        self.white_index = -1

        # self.__next_color=self.colors[0]

    def restart_color_cycle(self):
        self.index = -1
        self.white_index = -1

    def next_color(self):
        self.index += 1
        try:
            self.index = self.index % len(self.colors)
        except ZeroDivisionError:
            print(self.index)
            print(self.hue)
            print(self.colors)
            print(self.geoms)
        return self.colors[self.index]

    def next_white_color(self):
        self.white_index += 1
        self.white_index = self.index % len(self.white_colors)
        return self.white_colors[self.white_index]
