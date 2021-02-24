import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import matplotlib.tri as mtri

from tanager_feeder import utils


class Plot:
    def __init__(
        self,
        plotter,
        fig,
        white_fig,
        samples,
        title,
        oversize_legend=False,
        plot_scale=18,
        plot_width=215,
        x_axis="wavelength",
        y_axis="reflectance",
        xlim=None,
        ylim=None,
        exclude_artifacts=False,
        draw=True,
    ):
        pass

    # def __initfoo__(
    #     self,
    #     plotter,
    #     fig,
    #     white_fig,
    #     samples,
    #     title,
    #     oversize_legend=False,
    #     plot_scale=18,
    #     plot_width=215,
    #     x_axis="wavelength",
    #     y_axis="reflectance",
    #     xlim=None,
    #     ylim=None,
    #     exclude_artifacts=False,
    #     draw=True,
    # ):
    #     return
        self.plotter = plotter
        self.samples = samples
        self.contour_levels = []
        self.fig = fig
        self.white_fig = white_fig
        self.original_fig_size = (self.fig.get_figwidth(), self.fig.get_figheight())
        self.title = ""  # This will be the text to put on the notebook tab
        # self.geoms={'i':[],'e':[]} #This is a dict like this: {'i':[10,20],'e':[-10,0,10,20,30,40,50]} telling which
        # incidence and emission angles to include on the plot. empty lists mean plot all available.

        self.x_axis = x_axis
        self.y_axis = y_axis
        self.ylim = None  # About to set based on either data limits or zoom if specified
        self.xlim = None  # same as ylim
        self.exclude_artifacts = exclude_artifacts
        self.markers_drawn = False  # Referenced to decide whether to display markerstyle options in open_options
        self.lines_drawn = False  # Referenced to decide whether to display linestyle options in open_options
        # If y limits for plot not specified, make the plot wide enough to display min and max values for all samples.

        if ylim is None and xlim is None:
            for i, sample in enumerate(self.samples):
                for j, label in enumerate(sample.geoms):
                    if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]:
                        continue
                    if i == 0 and j == 0:
                        self.ylim = [np.min(sample.data[label][self.y_axis]), np.max(sample.data[label][self.y_axis])]

                    else:

                        sample_min = np.min(sample.data[label][self.y_axis])
                        sample_max = np.max(sample.data[label][self.y_axis])
                        self.ylim[0] = np.min([self.ylim[0], sample_min])
                        self.ylim[1] = np.max([self.ylim[1], sample_max])

            # add a little margin around edges
            if self.ylim is None:
                self.ylim = [0, 1]  # Happens if you are making a new tab with no data
            delta_y = self.ylim[1] - self.ylim[0]
            self.ylim[0] = self.ylim[0] - delta_y * 0.02
            self.ylim[1] = self.ylim[1] + delta_y * 0.02


        elif ylim is None:
            for i, sample in enumerate(self.samples):
                for j, label in enumerate(sample.geoms):
                    if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]:
                        continue

                    index_left = (
                        np.abs(np.array(sample.data[label][self.x_axis]) - xlim[0])
                    ).argmin()  # find index of min x
                    index_right = (
                        np.abs(np.array(sample.data[label][self.x_axis]) - xlim[1])
                    ).argmin()  # find index of max x
                    if i == 0 and j == 0:
                        self.ylim = [
                            np.min(sample.data[label][self.y_axis][index_left:index_right]),
                            np.max(sample.data[label][self.y_axis][index_left:index_right]),
                        ]
                    else:
                        sample_min = np.min(
                            sample.data[label][self.y_axis][index_left:index_right]
                        )  # find min value between min and max x
                        sample_max = np.max(
                            sample.data[label][self.y_axis][index_left:index_right]
                        )  # find max value between min and max x
                        self.ylim[0] = np.min([self.ylim[0], sample_min])
                        self.ylim[1] = np.max([self.ylim[1], sample_max])

            # add a little margin around edges
            if self.ylim is None:
                self.ylim = [0, 1]  # Happens if you are making a new tab with no data
            delta_y = self.ylim[1] - self.ylim[0]
            self.ylim[0] = self.ylim[0] - delta_y * 0.02
            self.ylim[1] = self.ylim[1] + delta_y * 0.02

        else:  # specified if this is a zoomed in plot
            self.ylim = ylim

        # If x limits for plot not specified, make the plot wide enough to display min and max values for all samples.
        if xlim is None:
            for i, sample in enumerate(self.samples):
                for j, label in enumerate(sample.geoms):
                    if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]:
                        continue

                    if i == 0 and j == 0:
                        sample_min = np.min(sample.data[label][self.x_axis][0:10])
                        sample_min = np.min(sample.data[label][self.x_axis])
                        sample_max = np.max(sample.data[label][self.x_axis])
                        self.xlim = [sample_min, sample_max]
                    else:
                        sample_min = np.min(sample.data[label][self.x_axis])
                        sample_max = np.max(sample.data[label][self.x_axis])
                        self.xlim[0] = np.min([self.xlim[0], sample_min])
                        self.xlim[1] = np.max([self.xlim[1], sample_max])

            if self.xlim is None:
                self.xlim = [400, 2400]  # Happens if you are making a new tab with no data
            delta_x = self.xlim[1] - self.xlim[0]

            if self.x_axis != "wavelength":  # add a little margin around edges
                self.xlim[0] = self.xlim[0] - delta_x * 0.02
                self.xlim[1] = self.xlim[1] + delta_x * 0.02

        else:  # This will be specified if this is a zoomed in plot
            self.xlim = xlim

        # we'll use these to generate hsv lists of colors for each sample, which will be evenly distributed across a
        # gradient to make it easy to see what the overall trend of reflectance is.
        #         self.hues=[200,12,130,290,170,37,330]
        self.hues = [200, 12, 130, 290, 170, 37]
        self.color_names = ["Blue", "Red", "Green", "Magenta", "Teal", "Custom"]
        self.oversize_legend = oversize_legend
        self.plot_scale = plot_scale
        self.annotations = (
            []
        )  # These will be vertical lines drawn to help with analysis to show where slopes are being calculated, etc
        self.white_annotations = []

        self.files = []
        self.num_spectra = 0  # This is the total number of spectra we're plotting. We want to get a count so we know
        # where to put the legend (on top or to the right).
        for i, sample in enumerate(self.samples):
            if sample.file not in self.files:
                self.files.append(sample.file)
            sample.set_colors(self.hues[i % len(self.hues)])
            self.num_spectra += len(sample.geoms)

        self.title = title

        self.max_legend_label_len = 0  # This will tell us how much horizontal space to give the legend
        self.legend_len = 0
        self.assign_legend_labels()
        self.legend_style = "Full list"

        plot_width = plot_width * 0.85
        if self.max_legend_label_len == 0:
            ratio = 1000
            self.legend_anchor = 1.05
        else:
            ratio = int(plot_width / self.max_legend_label_len) + 0.1
            self.legend_anchor = 1.12 + 1.0 / ratio * 1.3

        self.gs = mpl.gridspec.GridSpec(1, 2, width_ratios=[ratio, 1])

        if self.x_axis != "theta":
            self.ax = fig.add_subplot(self.gs[0])
        else:
            self.ax = self.fig.add_subplot(self.gs[0], projection="polar")

        with plt.style.context(("default")):
            if self.x_axis != "theta":
                self.white_ax = self.white_fig.add_subplot(self.gs[0])
            else:
                self.white_ax = self.white_fig.add_subplot(self.gs[0], projection="polar")
            self.white_leg_ax = self.white_fig.add_subplot(self.gs[1])

        self.leg_ax = self.fig.add_subplot(self.gs[1])
        self.leg_ax.set_yticklabels([])
        self.leg_ax.set_xticklabels([])
        self.leg_ax.spines["bottom"].set_color(None)
        self.leg_ax.spines["top"].set_color(None)
        self.leg_ax.spines["right"].set_color(None)
        self.leg_ax.spines["left"].set_color(None)

        self.white_leg_ax.set_yticklabels([])
        self.white_leg_ax.set_xticklabels([])
        self.white_leg_ax.spines["bottom"].set_color(None)
        self.white_leg_ax.spines["top"].set_color(None)
        self.white_leg_ax.spines["right"].set_color(None)
        self.white_leg_ax.spines["left"].set_color(None)

        self.leg_ax.tick_params(axis="both", which="both", colors="0.2")
        self.white_leg_ax.tick_params(axis="both", which="both", colors="1")


        pos1 = self.ax.get_position()  # get the original position
        y0 = pos1.y0 * 1.5  # This is all just magic to tweak the exact position.
        height = pos1.height * 0.9
        if self.oversize_legend:
            #             if self.x_axis=='theta': self.plot_scale=self.plot_scale*2
            height = pos1.height * self.plot_scale / self.legend_len
            y0 = 1 - self.plot_scale / self.legend_len + pos1.y0 * self.plot_scale / (self.legend_len) * 0.5

        if self.x_axis != "theta" or True:
            pos2 = [pos1.x0 - 0.02, y0, pos1.width, height]
        else:
            pos2 = [pos1.x0 - 0.1, y0 * 0.6, pos1.width * 1.4, pos1.height * (1.4 + 0.006 * self.legend_len)]

        self.ax.set_position(pos2)

        self.white_ax.set_position(
            pos2
        )  # set a new position, slightly adjusted so it doesn't go off the edges of the screen.

        pos1 = self.ax.get_position()
        pos2 = self.leg_ax.get_position()
        if self.x_axis != "theta":
            new_pos = [pos2.x0 - 0.05, pos1.y0, pos2.width, pos1.height]
        else:
            new_pos = [pos2.x0 - 0.05, pos1.y0, pos2.width, pos1.height]
        self.leg_ax.set_position(new_pos)
        self.white_leg_ax.set_position(new_pos)

        if draw:
            self.draw()

        print("finished drawing")

        self.contour = None
        self.colorbar = None
        self.white_contour = None
        self.white_colorbar = None

    @staticmethod
    def geom_to_label(geom):
        i = geom[0]
        e = geom[1]
        az = geom[2]
        label = f"(i={i} e={e} az={az})"
        return label

    def assign_legend_labels(self):
        self.repeats = False  # Find if there are samples with the exact same name. If so, put the title in the
        # legend as well as the name.
        self.names = []
        self.legend_labels = {}
        for sample in self.samples:
            self.legend_labels[sample] = []
            for label in sample.geoms:
                if self.y_axis not in sample.data[label] or self.x_axis not in sample.data[label]:
                    continue
            if sample.name in self.names:
                self.repeats = True
            else:
                self.names.append(sample.name)

        for sample in self.samples:
            for geom in sample.geoms:
                if self.y_axis not in sample.data[geom] or self.x_axis not in sample.data[geom]:
                    continue
                legend_label = sample.name + " " + self.geom_to_label(geom)
                if self.repeats:
                    legend_label = sample.title + ": " + sample.name + " " + self.geom_to_label(geom)
                if len(self.samples) == 1:
                    legend_label = legend_label.replace(sample.name, "").replace("(i=", "i=").replace(")", "")
                if len(legend_label) > self.max_legend_label_len:
                    self.max_legend_label_len = len(legend_label)

                self.legend_labels[sample].append(legend_label)
                self.legend_len += 1

    def save(self, fig):
        path = self.plotter.get_path()
        if not path:
            return
        if "." in path:
            available_formats = ["eps", "pdf", "pgf", "png", "ps", "raw", "rgba", "svg", "svgz"]
            save_format = path.split(".")[-1]
            if save_format not in available_formats:
                path = path + ".png"
        fig.savefig(path, facecolor=fig.get_facecolor())

    def set_title(self, title, draw=True):
        self.title = title
        self.ax.set_title(title, fontsize=24)
        if self.x_axis != "theta":
            self.ax.title.set_position([0.5, 1.02])
        else:
            self.ax.title.set_position([0.5, 0.83])
        with plt.style.context("default"):
            self.white_ax.set_title(title, fontsize=24, color="black")
            if self.x_axis != "theta":
                self.white_ax.title.set_position([0.5, 1.02])
            else:
                self.white_ax.title.set_position([0.5, 0.83])
        if draw:
            self.white_fig.canvas.draw()
            self.fig.canvas.draw()

    def draw_vertical_lines(self, xcoords):
        for _ in range(len(self.annotations)):
            try:
                self.annotations.pop(0).remove()
            except IndexError:
                print("Error! Annotation was erased somewhere it was not supposed to be!")

        for _ in range(len(self.white_annotations)):
            try:
                self.white_annotations.pop(0).remove()
            except IndexError:
                print("Error! Annotation was erased somewhere it was not supposed to be!")

        for x in xcoords:
            self.annotations.append(self.ax.axvline(x=x, color="lightgray", linewidth=1))
            self.white_annotations.append(self.white_ax.axvline(x=x, color="black", linewidth=1))

        self.fig.canvas.draw()
        self.white_fig.canvas.draw()

    def adjust_x(self, left, right):
        if self.x_axis != "theta":
            self.ax.set_xlim(left, right)
            self.white_ax.set_xlim(left, right)
            self.xlim = [left, right]
            self.set_x_ticks()
        else:
            pass
        self.fig.canvas.draw()
        self.white_fig.canvas.draw()

    def adjust_y(self, bottom, top):
        if self.x_axis == "theta":
            pass

        else:
            self.ax.set_ylim(bottom, top)
            self.white_ax.set_ylim(bottom, top)
            self.ylim = [bottom, top]
            self.set_y_ticks()
        self.fig.canvas.draw()
        self.white_fig.canvas.draw()

    def adjust_z(self, low, high):
        plot_pos = self.ax.get_position()
        interval = np.abs(high - low) / 7
        if interval == 0:
            return
        if high > low:
            self.contour_levels = np.arange(low, high + interval / 2, interval)
        else:
            raise Exception("Negative range")

        self.colorbar.remove()
        self.white_colorbar.remove()

        for coll in self.contour.collections:
            coll.remove()
        for coll in self.white_contour.collections:
            coll.remove()

        x = self.samples[0].data["all samples"]["e"]
        y = self.samples[0].data["all samples"]["i"]
        z = self.samples[0].data["all samples"][self.y_axis]
        triang = mtri.Triangulation(x, y)

        self.contour = self.ax.tricontourf(triang, z, levels=self.contour_levels)
        self.ax.plot(x, y, "+", color="white", markersize=5, alpha=0.5)
        self.ax.set_position(plot_pos)
        self.colorbar = self.fig.colorbar(self.contour, ax=self.ax, use_gridspec=False, anchor=(2, 2))
        self.ax.set_position(plot_pos)
        self.fig.canvas.draw()

        with plt.style.context(("default")):
            self.white_contour = self.white_ax.tricontourf(triang, z, levels=self.contour_levels)
            self.white_ax.plot(x, y, "+", color="white", markersize=5, alpha=0.5)
            self.white_ax.set_position(plot_pos)
            self.white_colorbar = self.fig.colorbar(
                self.white_contour, ax=self.white_ax, use_gridspec=False, anchor=(2, 2)
            )
            self.white_colorbar.ax.tick_params(labelsize=14)
            self.white_fig.canvas.draw()

    def set_x_ticks(self):

        order = -3.0
        delta_x = self.xlim[1] - self.xlim[0]

        # Decide where to place tick marks.
        while np.power(10, order) - delta_x < 0:
            order += 1

        if delta_x / np.power(10, order) > 0.5:
            order = order - 1
        else:
            order = order - 2

        order = int(order * -1)

        interval = np.round(delta_x / 5, order)

        interval_2 = np.round(interval / 5, order)
        order2 = order
        while interval_2 == 0:
            order2 += 1
            interval_2 = np.round(interval / 5, order2)
        if np.round(self.xlim[0], order) <= self.xlim[0]:

            major_ticks = np.arange(np.round(self.xlim[0], order), self.xlim[1] + 0.01 ** float(-1 * order), interval)
            minor_ticks = np.arange(np.round(self.xlim[0], order), self.xlim[1] + 0.01 ** float(-1 * order), interval_2)
        else:

            major_ticks = np.arange(
                np.round(self.xlim[0], order) - 10 ** float(-1 * order),
                self.xlim[1] + 0.01 ** float(-1 * order),
                interval,
            )
            minor_ticks = np.arange(
                np.round(self.xlim[0], order) - 10 ** float(-1 * order),
                self.xlim[1] + 0.01 ** float(-1 * order),
                interval_2,
            )

        self.ax.set_xticks(major_ticks)
        self.ax.set_xticks(minor_ticks, minor=True)
        with plt.style.context("default"):
            self.white_ax.set_xticks(major_ticks)
            self.white_ax.set_xticks(minor_ticks, minor=True)

    def set_y_ticks(self):
        order = -10.0
        delta_y = self.ylim[1] - self.ylim[0]

        # Decide where to place tick marks.
        while np.power(10, order) - delta_y < 0:
            order += 1

        if delta_y / np.power(10, order) > 0.5:
            order = order - 1
        else:
            order = order - 2

        order = int(order * -1)
        interval = np.round(delta_y / 5, order)
        while interval == 0:  # I don't think this ever happens.
            order += 1
            interval = np.round(delta_y / 5, order)

        if np.isnan(interval):  # Happens if all y values are equal
            interval = 0.002

        self.ax.grid(which="minor", alpha=0.1)
        self.ax.grid(which="major", alpha=0.1)
        with plt.style.context("default"):
            self.white_ax.grid(which="minor", alpha=0.3)
            self.white_ax.grid(which="major", alpha=0.3)

    def draw(self):

        self.ax.cla()
        self.white_ax.cla()

        self.visible_data = []
        self.visible_data_headers = []
        self.lines = []
        self.white_lines = []

        for sample in self.samples:
            sample.restart_color_cycle()  # Makes sure that we start at the same point for replotting

        if self.x_axis == "contour":
            x = self.samples[0].data["all samples"]["e"]
            y = self.samples[0].data["all samples"]["i"]
            z = self.samples[0].data["all samples"][self.y_axis]
            self.visible_data_headers.append("emission")
            self.visible_data.append(x)
            self.visible_data_headers.append("incidence")
            self.visible_data.append(y)
            self.visible_data_headers.append(self.y_axis)
            self.visible_data.append(z)

            triang = mtri.Triangulation(x, y)
            if (
                len(self.contour_levels) == 0
            ):  # contour levels are set here, and also in adjust z if the user does it manually
                interval = (np.max(z) - np.min(z)) / 7
                self.contour_levels = np.arange(np.min(z), np.max(z), interval)
                self.contour_levels = np.append(self.contour_levels, np.max(z))

            self.contour = self.ax.tricontourf(triang, z, levels=self.contour_levels)

            self.colorbar = self.fig.colorbar(self.contour, ax=self.ax)
            self.ax.plot(x, y, "+", color="white", markersize=5, alpha=0.5)

            with plt.style.context(("default")):
                self.white_contour = self.white_ax.tricontourf(triang, z, levels=self.contour_levels)
                self.white_colorbar = self.white_fig.colorbar(self.white_contour, ax=self.white_ax)
                self.white_colorbar.ax.tick_params(labelsize=14)
                self.white_ax.plot(x, y, "+", color="white", markersize=5, alpha=0.5)

            self.adjust_x(np.min(x), np.max(x))
            self.adjust_y(np.min(y), np.max(y))

        else:

            min_r = None  # we'll use these for setting polar r limits if we are doing a polar plot.
            max_r = None

            for j, sample in enumerate(self.samples):
                for i, label in enumerate(sample.geoms):
                    legend_label = self.legend_labels[sample][i]

                    color = sample.next_color()
                    white_color = sample.next_white_color()

                    if self.x_axis != "theta":
                        self.visible_data_headers.append(self.x_axis)
                        self.visible_data.append(sample.data[label][self.x_axis])

                    if (
                        self.y_axis == "reflectance"
                        or self.y_axis == "difference"
                        or self.y_axis == "normalized reflectance"
                    ) and self.x_axis == "wavelength":
                        wavelengths = sample.data[label][self.x_axis]
                        reflectance = sample.data[label][self.y_axis]

                        if (
                            self.exclude_artifacts
                        ):  # If we are excluding data from the suspect region from 1050 to 1450 nm, divide each
                            # spectrum into 3 segments. One on either side of that bad region, and then one straight
                            # dashed line through the bad region. All the same color. Only attach a legend label to
                            # the first one so the legend only gets drawn once.
                            _, _, g = self.plotter.get_e_i_g(label)
                            if self.plotter.artifact_danger(g):  # Only exclude data for high phase angle spectra
                                artifact_index_left = self.plotter.get_index(
                                    np.array(wavelengths), utils.MIN_WAVELENGTH_ARTIFACT_FREE
                                )
                                artifact_index_right = self.plotter.get_index(
                                    np.array(wavelengths), utils.MAX_WAVELENGTH_ARTIFACT_FREE
                                )
                                w_1, r_1 = wavelengths[0:artifact_index_left], reflectance[0:artifact_index_left]
                                w_2 = [wavelengths[artifact_index_left], wavelengths[artifact_index_right]]
                                r_2 = [reflectance[artifact_index_left], reflectance[artifact_index_right]]
                                w_3, r_3 = wavelengths[artifact_index_right:-1], reflectance[artifact_index_right:-1]
                                self.lines.append(
                                    self.ax.plot(
                                        w_1, r_1, sample.linestyle, label=legend_label, color=color, linewidth=2
                                    )
                                )
                                if sample.linestyle != "--":
                                    self.lines.append(self.ax.plot(w_2, r_2, "--", color=color, linewidth=2))
                                else:
                                    self.lines.append(self.ax.plot(w_2, r_2, ".", color=color, linewidth=2))
                                self.lines.append(self.ax.plot(w_3, r_3, sample.linestyle, color=color, linewidth=2))

                                self.visible_data_headers.append(legend_label)
                                self.visible_data.append(list(r_1) + list(r_2) + list(r_3))

                                with plt.style.context("default"):
                                    self.lines_drawn = True
                                    self.white_lines.append(
                                        self.white_ax.plot(
                                            w_1,
                                            r_1,
                                            sample.linestyle,
                                            label=legend_label,
                                            color=white_color,
                                            linewidth=2,
                                        )
                                    )
                                    if sample.linestyle != "--":
                                        self.white_lines.append(
                                            self.white_ax.plot(w_2, r_2, "--", color=white_color, linewidth=2)
                                        )
                                    else:
                                        self.white_lines.append(
                                            self.white_ax.plot(w_2, r_2, ".", color=color, linewidth=2)
                                        )
                                    self.white_lines.append(
                                        self.white_ax.plot(w_3, r_3, sample.linestyle, color=white_color, linewidth=2)
                                    )
                            else:
                                self.lines_drawn = True
                                self.lines.append(
                                    self.ax.plot(
                                        wavelengths,
                                        reflectance,
                                        sample.linestyle,
                                        label=legend_label,
                                        color=color,
                                        linewidth=2,
                                    )
                                )
                                self.visible_data_headers.append(legend_label)
                                self.visible_data.append(reflectance)

                                with plt.style.context("default"):
                                    self.white_lines.append(
                                        self.white_ax.plot(
                                            wavelengths,
                                            reflectance,
                                            sample.linestyle,
                                            label=legend_label,
                                            color=white_color,
                                            linewidth=2,
                                        )
                                    )

                        else:
                            if len(wavelengths) > 50:
                                self.lines_drawn = True  # Referenced to decide whether to display linestyle options
                                self.lines.append(
                                    self.ax.plot(
                                        wavelengths,
                                        reflectance,
                                        sample.linestyle,
                                        label=legend_label,
                                        color=color,
                                        linewidth=2,
                                    )
                                )
                            else:
                                self.markers_drawn = True  # Referenced to decide whether to display markerstyle options
                                self.lines.append(
                                    self.ax.plot(
                                        wavelengths,
                                        reflectance,
                                        "-" + sample.markerstyle,
                                        label=legend_label,
                                        color=color,
                                        linewidth=2,
                                        markersize=5,
                                    )
                                )

                            self.visible_data_headers.append(legend_label)
                            self.visible_data.append(reflectance)

                            with plt.style.context("default"):
                                if len(wavelengths) > 50:
                                    self.white_lines.append(
                                        self.white_ax.plot(
                                            wavelengths,
                                            reflectance,
                                            sample.linestyle,
                                            label=legend_label,
                                            color=white_color,
                                            linewidth=2,
                                        )
                                    )
                                else:
                                    self.white_lines.append(
                                        self.white_ax.plot(
                                            wavelengths,
                                            reflectance,
                                            "-" + sample.markerstyle,
                                            label=legend_label,
                                            color=white_color,
                                            linewidth=2,
                                            markersize=5,
                                        )
                                    )
                    elif self.x_axis == "g":
                        self.markers_drawn = True
                        self.lines_drawn = False
                        self.visible_data_headers.append(legend_label)
                        self.visible_data.append(sample.data[label][self.y_axis])

                        self.lines.append(
                            self.ax.plot(
                                sample.data[label][self.x_axis],
                                sample.data[label][self.y_axis],
                                sample.markerstyle,
                                label=legend_label,
                                color=color,
                                markersize=6,
                            )
                        )
                        # self.lines.append(self.ax.plot(sample.data[label][self.x_axis],
                        # sample.data[label][self.y_axis],label=legend_label,color=color, markersize=6))
                        with plt.style.context("default"):
                            self.lines.append(
                                self.white_ax.plot(
                                    sample.data[label][self.x_axis],
                                    sample.data[label][self.y_axis],
                                    sample.markerstyle,
                                    label=legend_label,
                                    color=white_color,
                                    markersize=6,
                                )
                            )
                            # self.lines.append(self.white_ax.plot(sample.data[label][self.x_axis],
                            # sample.data[label][self.y_axis], label=legend_label,color=white_color, markersize=6))
                    elif self.x_axis == "theta":
                        self.markers_drawn = True
                        self.lines_drawn = False
                        theta = sample.data[label]["e"]
                        theta = np.array(theta) * -1 * 3.14159 / 180 + 3.14159 / 2
                        r = sample.data[label][self.y_axis]
                        if (
                            i == 0 and j == 0
                        ):  # If this is the first line we are plotting, we'll need to create the polar axis.
                            self.ax.plot(
                                theta,
                                np.array(r),
                                "-" + sample.markerstyle,
                                color=color,
                                label=legend_label,
                                markersize=6,
                            )

                            with plt.style.context("default"):
                                self.white_ax.plot(
                                    theta,
                                    np.array(r),
                                    "-" + sample.markerstyle,
                                    color=white_color,
                                    label=legend_label,
                                    markersize=6,
                                )

                            min_r = np.min(r)
                            max_r = np.max(r)
                            delta = max_r - min_r
                            self.ax.set_ylim(min_r - delta / 10, max_r + delta / 10)
                            self.ax.set_thetamin(0)
                            self.ax.set_thetamax(180)

                            self.white_ax.set_ylim(min_r - delta / 10, max_r + delta / 10)
                            self.white_ax.set_thetamin(0)
                            self.white_ax.set_thetamax(180)

                            self.set_title(self.title, draw=False)

                        else:  # if this is not the first line being plotted on this radial plot, we can just add on

                            self.ax.plot(
                                theta,
                                np.array(r),
                                "-" + sample.markerstyle,
                                color=color,
                                label=legend_label,
                                markersize=6,
                            )
                            with plt.style.context("default"):
                                self.white_ax.plot(
                                    theta,
                                    np.array(r),
                                    "-" + sample.markerstyle,
                                    color=white_color,
                                    label=legend_label,
                                    markersize=6,
                                )
                            if np.min(r) < min_r or np.max(r) > max_r:
                                min_r = np.min([min_r, np.min(r)])
                                max_r = np.max([max_r, np.max(r)])

                        if (
                            i == len(sample.geoms) - 1 and j == len(self.samples) - 1
                        ):  # On the last sample, set the range of the value being plotted on the radial axis.

                            delta = max_r - min_r
                            self.ax.set_ylim(min_r - delta / 10, max_r + delta / 10)
                            self.ax.set_yticks(np.round(np.arange(min_r, max_r + delta / 10, delta / 2), 4))
                            self.ax.set_thetagrids(
                                np.arange(0, 180.1, 30), labels=["90", "60", "30", "0", "-30", "-60", "-90"]
                            )

                            with plt.style.context("default"):
                                self.white_ax.set_ylim(min - delta / 10, max_r + delta / 10)
                                self.white_ax.set_rgrids(np.round(np.arange(min_r, max_r + delta / 10, delta / 2), 3))
                                self.white_ax.set_yticks(np.round(np.arange(min_r, max_r + delta / 10, delta / 2), 3))
                                self.white_ax.set_thetagrids(
                                    np.arange(0, 180.1, 30), labels=["90", "60", "30", "0", "-30", "-60", "-90"]
                                )
                                self.white_ax.tick_params(axis="both", colors="black")
                    else:
                        self.visible_data_headers.append(legend_label)
                        self.visible_data.append(sample.data[label][self.y_axis])
                        self.markers_drawn = True
                        self.lines.append(
                            self.ax.plot(
                                sample.data[label][self.x_axis],
                                sample.data[label][self.y_axis],
                                "-" + sample.markerstyle,
                                label=legend_label,
                                color=color,
                                markersize=5,
                            )
                        )
                        with plt.style.context("default"):
                            self.white_lines.append(
                                self.white_ax.plot(
                                    sample.data[label][self.x_axis],
                                    sample.data[label][self.y_axis],
                                    "-" + sample.markerstyle,
                                    label=legend_label,
                                    color=white_color,
                                    markersize=5,
                                )
                            )

        self.set_title(self.title, draw=False)

        if self.x_axis == "contour":
            self.ax.set_xlabel("Emission (degrees)", fontsize=18)
            self.ax.set_ylabel("Incidence (degrees)", fontsize=18)
            with plt.style.context(("default")):
                self.white_ax.set_xlabel("Emission (degrees)", fontsize=18)
                self.white_ax.set_ylabel("Incidence (degrees)", fontsize=18)
        elif self.y_axis == "reflectance":
            self.ax.set_ylabel("Reflectance", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_ylabel("Reflectance", fontsize=18)
        elif self.y_axis == "normalized reflectance":
            self.ax.set_ylabel("Normalized Reflectance", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_ylabel("Normalized Reflectance", fontsize=18)
        elif self.y_axis == "difference":
            # pylint: disable = anomalous-backslash-in-string
            self.ax.set_ylabel("$\Delta$R", fontsize=18)
            with plt.style.context("default"):
                # pylint: disable = anomalous-backslash-in-string
                self.white_ax.set_ylabel("$\Delta$R", fontsize=18)
        elif self.y_axis == "slope":
            self.ax.set_ylabel("Slope", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_ylabel("Slope", fontsize=18)
        elif self.y_axis == "band depth":
            self.ax.set_ylabel("Band Depth", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_ylabel("Band Depth", fontsize=18)

        if self.x_axis == "wavelength":
            self.ax.set_xlabel("Wavelength (nm)", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_xlabel("Wavelength (nm)", fontsize=18)
        elif self.x_axis == "i":
            self.ax.set_xlabel("Incidence (degrees)", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_xlabel("Incidence (degrees)", fontsize=18)
        elif self.x_axis == "e":
            self.ax.set_xlabel("Emission (degrees)", fontsize=18)
            with plt.style.context("default"):
                self.ax.set_xlabel("Emission (degrees)", fontsize=18)
        elif self.x_axis == "g":
            self.ax.set_xlabel("Phase angle (degrees)", fontsize=18)
            with plt.style.context("default"):
                self.white_ax.set_xlabel("Phase angle (degrees)", fontsize=18)

        self.ax.tick_params(labelsize=14)
        with plt.style.context(("default")):
            self.white_ax.tick_params(labelsize=14)
        if self.x_axis != "contour":
            self.draw_legend(self.legend_style)

        self.white_ax.tick_params(
            axis="both", colors="black"
        )  # the plot style context should take care of this but doesn't.

        if self.x_axis != "theta":  # If it is theta, we did this already
            self.ax.set_xlim(*self.xlim)
            self.white_ax.set_xlim(*self.xlim)
            self.ax.set_ylim(*self.ylim)
            self.white_ax.set_ylim(*self.ylim)
            self.set_x_ticks()
            self.set_y_ticks()
        print("hooey")
        return
        # TODO: Test thoroughly, especially for plotting remote data
        # TODO: after clearing data cache, new tab (2) still turns up (instead of new tab)
        # TODO: after clearing data cache, cannot plot same file again.
        self.fig.canvas.draw()
        self.white_fig.canvas.draw()

    def draw_legend(self, legend_style):
        self.legend_style = (
            legend_style  # Does something if this method is called from Plot settings changing legend style
        )
        if self.ax.get_legend() is not None:
            self.ax.get_legend().remove()
        if self.white_ax.get_legend() is not None:
            self.white_ax.get_legend().remove()

        self.leg_ax.patches = []
        self.leg_ax.cla()
        self.white_leg_ax.patches = []
        self.white_leg_ax.cla()

        if legend_style == "Full list":
            self.leg_ax.set_visible(False)
            self.white_leg_ax.set_visible(False)
            if self.x_axis != "theta":
                self.ax.legend(bbox_to_anchor=(self.legend_anchor, 1), loc=1, borderaxespad=0.0)
                with plt.style.context(("default")):
                    self.white_ax.legend(bbox_to_anchor=(self.legend_anchor, 1), loc=1, borderaxespad=0.0)
            else:
                self.ax.legend(bbox_to_anchor=(self.legend_anchor * 1.2, 0.85), loc=1, borderaxespad=0.0)
                with plt.style.context(("default")):
                    self.white_ax.legend(bbox_to_anchor=(self.legend_anchor * 1.2, 0.85), loc=1, borderaxespad=0.0)
        else:
            self.leg_ax.set_visible(True)
            self.white_leg_ax.set_visible(True)

            left = 0.08
            bottom = 0.01
            width = 0.25
            buffer_per_sample = 0.05
            num_samples_plotted = len(self.legend_labels.keys())
            total_buffer = buffer_per_sample * (num_samples_plotted - 1)
            sample_height = (
                0.99 / num_samples_plotted - total_buffer / num_samples_plotted
            )  # full height of plot =1, divide by number of samples plotted,
            # subtract a buffer for each after the first one.
            sample_height = sample_height * 0.999
            for sample in self.samples:
                if num_samples_plotted == 1:
                    fontsize = 14
                elif num_samples_plotted == 2:
                    fontsize = 14
                    left = 0.05
                else:
                    fontsize = 8
                    left = 0

                if num_samples_plotted in [1, 2]:
                    self.leg_ax.text(
                        0,
                        bottom,
                        sample.name,
                        verticalalignment="bottom",
                        horizontalalignment="right",
                        transform=self.leg_ax.transAxes,
                        color="lightgray",
                        fontsize=fontsize,
                        rotation=90,
                    )
                    self.white_leg_ax.text(
                        0,
                        bottom,
                        sample.name,
                        verticalalignment="bottom",
                        horizontalalignment="right",
                        transform=self.leg_ax.transAxes,
                        color="black",
                        fontsize=fontsize,
                        rotation=90,
                    )
                else:
                    self.leg_ax.text(
                        0,
                        bottom - 0.01,
                        sample.name,
                        verticalalignment="top",
                        horizontalalignment="left",
                        transform=self.leg_ax.transAxes,
                        color="lightgray",
                        fontsize=fontsize,
                    )
                    self.white_ax.text(
                        0,
                        bottom - 0.01,
                        sample.name,
                        verticalalignment="top",
                        horizontalalignment="left",
                        transform=self.leg_ax.transAxes,
                        color="black",
                        fontsize=fontsize,
                    )

                if sample not in self.legend_labels:
                    continue
                num_colors = len(self.legend_labels[sample])

                height = sample_height / num_colors
                for i in range(num_colors):
                    if i == 0:
                        self.leg_ax.text(
                            left + width,
                            bottom,
                            self.legend_labels[sample][0].replace(sample.name, "").replace("(i", "i").strip(")"),
                            verticalalignment="bottom",
                            horizontalalignment="left",
                            transform=self.leg_ax.transAxes,
                            color="lightgray",
                            fontsize=fontsize,
                        )
                        self.white_leg_ax.text(
                            left + width,
                            bottom,
                            self.legend_labels[sample][0].replace(sample.name, "").replace("(i", "i").strip(")"),
                            verticalalignment="bottom",
                            horizontalalignment="left",
                            transform=self.leg_ax.transAxes,
                            color="black",
                            fontsize=fontsize,
                        )
                    elif i == num_colors - 1:
                        self.leg_ax.text(
                            left + width,
                            bottom + height,
                            self.legend_labels[sample][-1].replace(sample.name, "").replace("(i", "i").strip(")"),
                            verticalalignment="top",
                            horizontalalignment="left",
                            transform=self.leg_ax.transAxes,
                            color="lightgray",
                            fontsize=fontsize,
                        )
                        self.white_leg_ax.text(
                            left + width,
                            bottom + height,
                            self.legend_labels[sample][-1].replace(sample.name, "").replace("(i", "i").strip(")"),
                            verticalalignment="top",
                            horizontalalignment="left",
                            transform=self.leg_ax.transAxes,
                            color="black",
                            fontsize=fontsize,
                        )

                    p = patches.Rectangle(
                        (left, bottom), width, height, facecolor=sample.colors[i], transform=self.leg_ax.transAxes
                    )
                    self.leg_ax.add_patch(p)
                    p = patches.Rectangle(
                        (left, bottom), width, height, facecolor=sample.white_colors[i], transform=self.leg_ax.transAxes
                    )
                    self.white_leg_ax.add_patch(p)
                    bottom += height

                p = patches.Rectangle(
                    (left, bottom - sample_height),
                    width,
                    sample_height,
                    fill=False,
                    edgecolor="lightgray",
                    transform=self.leg_ax.transAxes,
                )
                self.leg_ax.add_patch(p)
                p = patches.Rectangle(
                    (left, bottom - sample_height),
                    width,
                    sample_height,
                    fill=False,
                    edgecolor="black",
                    transform=self.leg_ax.transAxes,
                )
                self.white_leg_ax.add_patch(p)
                bottom += buffer_per_sample
