from tkinter import BOTH, Menu

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

from tanager_feeder.plotter.sample import Sample
from tanager_feeder.plotter.plot import Plot

from tanager_feeder import utils


class Tab:
    # Title override is true if the title of this individual tab is set manually by user.
    # If it is False, then the tab and plot title will be a combo of the file title plus the sample that is plotted.
    def __init__(
        self,
        plotter,
        title,
        samples,
        tab_index=None,
        geoms=None,
        original=None,
        x_axis="wavelength",
        y_axis="reflectance",
        xlim=None,
        ylim=None,
        exclude_artifacts=False,
        exclude_specular=False,
        specularity_tolerance=None,
        draw=True,
    ):
        if geoms is None:
            geoms = {"i": [], "e": [], "az": []}
        self.plotter = plotter
        if original is None:  # This is true if we're not normalizing anything.
            # holding on to the original data lets us reset.
            self.original_samples = list(samples)
        else:
            self.original_samples = original
        self.samples = samples
        self.geoms = geoms

        self.title = title
        base = title
        i = 1
        while title in self.plotter.titles:
            title = base + " (" + str(i) + ")"
            i = i + 1
        self.notebook_title = title
        self.plotter.titles.append(self.notebook_title)

        self.x_axis = x_axis
        self.y_axis = y_axis
        self.xlim = xlim
        self.ylim = ylim
        self.zlim = None

        self.exclude_artifacts = exclude_artifacts
        self.exclude_specular = exclude_specular
        self.specularity_tolerance = specularity_tolerance

        self.width = self.plotter.notebook.winfo_width()
        self.height = self.plotter.notebook.winfo_height()

        # If we need a bigger frame to hold a giant long legend, expand.
        self.legend_len = 0
        for sample in self.samples:
            self.legend_len += len(sample.geoms)
        self.legend_height = self.legend_len * 21 + 100  # 21 px per legend entry.
        self.plot_scale = (self.height - 130) / 21
        self.plot_width = self.width / 9  # very vague character approximation of plot width

        if self.height > self.legend_height:
            self.top = utils.NotScrolledFrame(self.plotter.notebook)
            self.oversize_legend = False
        else:
            self.top = utils.VerticalScrolledFrame(self.plotter.controller, self.plotter.notebook)
            self.oversize_legend = True

        self.top.min_height = np.max([self.legend_height, self.height - 50])
        self.top.pack()

        # If this is being created from the File -> Plot option, or from right click -> new tab, just put the
        # tab at the end.
        if tab_index is None:
            self.plotter.notebook.add(self.top, text=self.notebook_title + " x")
            self.plotter.notebook.select(self.plotter.notebook.tabs()[-1])
            self.index = self.plotter.notebook.index(self.plotter.notebook.select())
        # If this is being called after the user did Right click -> choose samples to plot, put it at the same
        # index as before.
        else:
            self.plotter.notebook.add(self.top, text=self.title + " x")
            self.plotter.notebook.insert(tab_index, self.plotter.notebook.tabs()[-1])
            self.plotter.notebook.select(self.plotter.notebook.tabs()[tab_index])
            self.index = tab_index

        self.fig = mpl.figure.Figure(
            figsize=(self.width / self.plotter.dpi, self.height / self.plotter.dpi), dpi=self.plotter.dpi
        )
        with plt.style.context(("default")):
            self.white_fig = mpl.figure.Figure(
                figsize=(self.width / self.plotter.dpi, self.height / self.plotter.dpi), dpi=self.plotter.dpi
            )
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.top.interior)
        self.white_canvas = FigureCanvasTkAgg(self.white_fig, master=self.top.interior)
        self.canvas.get_tk_widget().bind("<Button-3>", lambda event: self.open_right_click_menu(event))
        self.canvas.get_tk_widget().bind("<Button-1>", lambda event: self.close_right_click_menu(event))

        self.canvas.get_tk_widget().pack(expand=True, fill=BOTH)
        self.plot = Plot(
            self.plotter,
            self.fig,
            self.white_fig,
            self.samples,
            self.title,
            self.oversize_legend,
            self.plot_scale,
            self.plot_width,
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            xlim=self.xlim,
            ylim=self.ylim,
            exclude_artifacts=self.exclude_artifacts,
            draw=draw,
        )

        if draw:
            self.canvas.draw()  # sometimes silently crashes if run from pip module (not IDE) on some login
            # configurations. Related to thread safety (only crashes for remote plotting, which involves a
            # separate thread). To protect against this, draw will be false if this is called from a separate
            # thread and the user is asked for input instead.

        self.popup_menu = Menu(self.top.interior, tearoff=0)
        if self.x_axis == "wavelength" and (self.y_axis == "reflectance" or self.y_axis == "normalized reflectance"):
            self.popup_menu.add_command(label="Edit plot", command=self.ask_which_samples)
            self.popup_menu.add_command(label="Plot settings", command=self.open_plot_settings)
            self.popup_menu.add_command(label="Open analysis tools", command=self.open_analysis_tools)
        else:
            self.popup_menu.add_command(label="Plot settings", command=self.open_plot_settings)

        self.save_menu = Menu(self.popup_menu, tearoff=0)
        self.save_menu.add_command(label="White background", command=self.save_white)
        self.save_menu.add_command(label="Dark background", command=self.save_dark)
        self.popup_menu.add_cascade(label="Save plot", menu=self.save_menu)
        self.popup_menu.add_command(label="Export data to .csv", command=self.export)

        self.popup_menu.add_command(label="New tab", command=self.new)
        self.popup_menu.add_command(label="Close tab", command=self.close)

        self.plotter.menus.append(self.popup_menu)

        self.contour_sample = None
        self.incidence_samples = None
        self.emission_samples = None
        self.error_samples = None
        self.base_sample = None
        self.recip_samples = None
        self.sample_options_dict = None
        self.sample_options_list = None
        self.base_spectrum_label = None
        self.existing_indices = None

        self.frozen = False

    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False

    def save_white(self):
        self.canvas.get_tk_widget().pack_forget()
        self.white_canvas.get_tk_widget().pack(expand=True, fill=BOTH)
        self.white_canvas.get_tk_widget().bind("<Button-3>", lambda event: self.open_right_click_menu(event))
        self.white_canvas.get_tk_widget().bind("<Button-1>", lambda event: self.close_right_click_menu(event))
        self.plot.save(self.white_fig)

    def export(self):
        path = self.plotter.get_path()
        if not path:
            return

        if path[-4 : len(path)] != ".csv":
            path += ".csv"

        headers = self.plot.visible_data_headers
        data = self.plot.visible_data
        headers = (",").join(headers)

        # data=np.transpose(data) doesn't work if not all columns are same length
        data_lines = []
        max_len = 0
        for col in data:
            if len(col) > max_len:
                max_len = len(col)

        for col in data:
            j = 0
            for val in col:
                if j < len(data_lines):
                    data_lines[j] += "," + str(val)
                else:
                    data_lines.append(str(val))
                j = j + 1
            while j < max_len:
                data_lines[j] += ","
                j += 1

        with open(path, "w+") as f:
            f.write(headers + "\n")
            for line in data_lines:
                f.write(line + "\n")

    def save_dark(self):
        self.white_canvas.get_tk_widget().pack_forget()
        self.canvas.get_tk_widget().pack(expand=True, fill=BOTH)
        self.canvas.get_tk_widget().bind("<Button-3>", lambda event: self.open_right_click_menu(event))
        self.canvas.get_tk_widget().bind("<Button-1>", lambda event: self.close_right_click_menu(event))
        self.plot.save(self.fig)

    def new(self):
        self.plotter.new_tab()

    def open_options(self):
        self.plotter.controller.open_options(self, self.title)

    # This is needed so that this can be one of the parts of a dict for buttons:
    # self.view_notebook.select:[lambda:tab.get_top()],.
    # That way when the top gets recreated in refresh, the reset button will get the new one instead of creating
    # errors by getting the old one.
    def get_top(self):
        return self.top

    def set_exclude_artifacts(self, exclude_bool):
        for i, sample in enumerate(self.plot.samples):
            sample.set_colors(self.plot.hues[i % len(self.plot.hues)])

        i = len(self.plot.ax.lines)
        j = 0
        # Delete all of the lines except annotations e.g. vertical lines showing where slopes are being calculated.
        for _ in range(i):
            if self.plot.ax.lines[j] not in self.plot.annotations:
                self.plot.ax.lines[j].remove()
            else:
                j += 1
        j = 0
        for _ in range(i):
            if self.plot.white_ax.lines[j] not in self.plot.white_annotations:
                self.plot.white_ax.lines[j].remove()
            else:
                j += 1

        self.exclude_artifacts = exclude_bool
        self.plot.exclude_artifacts = bool
        self.plot.draw()
        self.canvas.draw()
        self.white_canvas.draw()

    def on_visibility(self, event):
        self.close_right_click_menu(event)

    # find reflectance at a given wavelength.
    # if we're on the edges, average out a few values.
    @staticmethod
    def get_vals(wavelengths, reflectance, nm):
        index = (np.abs(wavelengths - nm)).argmin()  # find index of wavelength

        r = reflectance[index]
        w = wavelengths[index]

        if (
            wavelengths[index] < 600 or wavelengths[index] > 2200
        ):  # If we're on the edges, spectra are noisy. Calculate slopes based on an average.
            if 2 < index < len(reflectance):
                r = np.mean(reflectance[index - 3: index + 3])
                w = wavelengths[index]
            elif index > 2:
                r = np.mean(reflectance[-7:-1])
                w = wavelengths[-4]
            elif index < len(reflectance) - 3:
                r = np.mean(reflectance[0:6])  # Take the first 6 values if you are at the beginning
                w = wavelengths[3]

        return w, r

    @staticmethod
    def get_index(array, val):
        index = (np.abs(array - val)).argmin()
        return index

    def offset(self, sample_name, offset):
        if ":" in sample_name:
            title = sample_name.split(":")[0]
            name = sample_name.split(":")[1]
        else:
            title = None
            name = sample_name
        for i, sample in enumerate(self.samples):
            if name == sample.name:
                if title is None or sample.title == title:
                    self.samples.pop(i)
                    new_sample = Sample(sample.name, sample.file, sample.title)
                    new_sample.data = {}
                    for key in sample.data:
                        new_sample.data[key] = {}
                        for key2 in sample.data[key]:
                            new_sample.data[key][key2] = list(sample.data[key][key2])
                    new_sample.geoms = list(sample.geoms)
                    new_sample.add_offset(offset, self.y_axis)
                    self.samples.insert(i, new_sample)
                    self.refresh(original=self.original_samples, y_axis=self.y_axis)
                    break

    def calculate_avg_reflectance(self, left, right):
        left, right = self.validate_left_right(left, right)
        avgs = []
        self.incidence_samples = []
        self.emission_samples = []
        artifact_warning = False

        self.contour_sample = Sample("all samples", "file", "title")
        self.contour_sample.data = {"all samples": {"i": [], "e": [], "average reflectance": []}}
        self.contour_sample.geoms = ["all samples"]

        for i, sample in enumerate(self.samples):
            incidence_sample = Sample(sample.name, sample.file, sample.title)
            emission_sample = Sample(sample.name, sample.file, sample.title)
            for geom in sample.geoms:
                i = geom[0]
                e = geom[1]
                az = geom[2]

                g = utils.get_phase_angle(i, e, az)

                if (
                    self.exclude_artifacts
                ):  # If we are excluding artifacts, don't calculate reflectance for anything in the range that
                    # is considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning = True
                        continue

                wavelengths = np.array(sample.data[geom]["wavelength"])
                reflectance = np.array(sample.data[geom][self.y_axis])

                index_left = self.get_index(wavelengths, left)
                index_right = self.get_index(wavelengths, right)

                avg = np.mean(reflectance[index_left:index_right])

                incidence = sample.name + " (i=" + str(i) + ")"
                emission = sample.name + " (e=" + str(e) + ")"

                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence] = {"e": [], "theta": [], "g": [], "average reflectance": []}
                    incidence_sample.geoms.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission] = {"i": [], "average reflectance": []}
                    emission_sample.geoms.append(emission)

                incidence_sample.data[incidence]["e"].append(e)
                incidence_sample.data[incidence]["theta"].append(e)
                incidence_sample.data[incidence]["g"].append(g)
                incidence_sample.data[incidence]["average reflectance"].append(avg)
                emission_sample.data[emission]["i"].append(i)
                emission_sample.data[emission]["average reflectance"].append(avg)

                self.contour_sample.data["all samples"]["e"].append(e)
                self.contour_sample.data["all samples"]["i"].append(i)
                self.contour_sample.data["all samples"]["average reflectance"].append(avg)

                avgs.append(geom + ": " + str(avg))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, avgs, artifact_warning

    def calculate_band_centers(self, left, right, use_max_for_centers, center_based_on_delta_to_continuum):
        left, right = self.validate_left_right(left, right)
        centers = []
        self.incidence_samples = []
        self.emission_samples = []
        artifact_warning = False

        self.contour_sample = Sample("all samples", "file", "title")
        self.contour_sample.data = {"all samples": {"i": [], "e": [], "band center": []}}
        self.contour_sample.geoms = ["all samples"]

        for i, sample in enumerate(self.samples):
            incidence_sample = Sample(sample.name, sample.file, sample.title)
            emission_sample = Sample(sample.name, sample.file, sample.title)
            for label in sample.geoms:
                e, i, g = self.plotter.get_e_i_g(label)

                if (
                    self.exclude_artifacts
                ):  # If we are excluding artifacts, don't calculate slopes for anything in the range that is
                    # considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning = True
                        continue

                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(sample.data[label][self.y_axis])

                # find reflectance at left and right wavelengths.
                # if we're on the edges, average out a few values.
                w_left, r_left = self.get_vals(wavelengths, reflectance, left)
                index_left = self.get_index(wavelengths, left)

                w_right, r_right = self.get_vals(wavelengths, reflectance, right)
                index_right = self.get_index(wavelengths, right)

                slope = (r_right - r_left) / (w_right - w_left)
                continuum = reflectance[index_left] + slope * (
                    wavelengths[index_left:index_right] - wavelengths[index_left]
                )
                diff = continuum - reflectance[index_left:index_right]

                if center_based_on_delta_to_continuum:
                    index_peak = list(diff).index(
                        np.min(diff)
                    )  # this is confusing, because we report an absorption band as positive depth, a local maximum
                    # in the spectrum occurs at the minimum value of diff.
                    index_trough = list(diff).index(np.max(diff))
                else:
                    r_trough = np.min(reflectance[index_left:index_right])
                    r_peak = np.max(reflectance[index_left:index_right])
                    index_trough = list(reflectance[index_left:index_right]).index(r_trough)
                    index_peak = list(reflectance[index_left:index_right]).index(r_peak)

                if np.abs(diff[index_peak]) > np.abs(diff[index_trough]) and use_max_for_centers:
                    center = wavelengths[index_peak + index_left]
                else:
                    center = wavelengths[index_trough + index_left]

                incidence = sample.name + " (i=" + str(i) + ")"
                emission = sample.name + " (e=" + str(e) + ")"

                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence] = {"e": [], "theta": [], "g": [], "band center": []}
                    incidence_sample.geoms.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission] = {"i": [], "band center": []}
                    emission_sample.geoms.append(emission)

                incidence_sample.data[incidence]["e"].append(e)
                incidence_sample.data[incidence]["theta"].append(e)
                incidence_sample.data[incidence]["g"].append(g)
                incidence_sample.data[incidence]["band center"].append(center)
                emission_sample.data[emission]["i"].append(i)
                emission_sample.data[emission]["band center"].append(center)

                self.contour_sample.data["all samples"]["e"].append(e)
                self.contour_sample.data["all samples"]["i"].append(i)
                self.contour_sample.data["all samples"]["band center"].append(center)

                centers.append(label + ": " + str(center))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, centers, artifact_warning

    def calculate_band_depths(self, left, right, report_negative, center_based_on_delta_to_continuum):
        left, right = self.validate_left_right(left, right)
        depths = []
        self.incidence_samples = []
        self.emission_samples = []
        artifact_warning = False

        self.contour_sample = Sample("all samples", "file", "title")
        self.contour_sample.data = {"all samples": {"i": [], "e": [], "band depth": []}}
        self.contour_sample.geoms = ["all samples"]

        for i, sample in enumerate(self.samples):
            incidence_sample = Sample(sample.name, sample.file, sample.title)
            emission_sample = Sample(sample.name, sample.file, sample.title)
            for label in sample.geoms:
                e, i, g = self.plotter.get_e_i_g(label)

                if (
                    self.exclude_artifacts
                ):  # If we are excluding artifacts, don't calculate slopes for anything in the range that is
                    # considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning = True
                        continue

                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(sample.data[label][self.y_axis])

                # find reflectance at left and right wavelengths.
                # if we're on the edges, average out a few values.
                w_left, r_left = self.get_vals(wavelengths, reflectance, left)
                index_left = self.get_index(wavelengths, left)

                w_right, r_right = self.get_vals(wavelengths, reflectance, right)
                index_right = self.get_index(wavelengths, right)

                slope = (r_right - r_left) / (w_right - w_left)
                continuum = reflectance[index_left] + slope * (
                    wavelengths[index_left:index_right] - wavelengths[index_left]
                )
                diff = (continuum - reflectance[index_left:index_right]) / continuum

                if center_based_on_delta_to_continuum:
                    index_peak = list(diff).index(
                        np.min(diff)
                    )  # this is confusing, because we report an absorption band as positive depth, a local maximum
                    # in the spectrum occurs at the minimum value of diff.
                    index_trough = list(diff).index(np.max(diff))
                else:
                    r_trough = np.min(reflectance[index_left:index_right])
                    r_peak = np.max(reflectance[index_left:index_right])
                    index_trough = list(reflectance[index_left:index_right]).index(r_trough)
                    index_peak = list(reflectance[index_left:index_right]).index(r_peak)

                if np.abs(diff[index_peak]) > np.abs(diff[index_trough]) and report_negative:
                    depth = diff[index_peak]
                else:
                    depth = diff[index_trough]

                incidence = sample.name + " (i=" + str(i) + ")"
                emission = sample.name + " (e=" + str(e) + ")"

                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence] = {"e": [], "theta": [], "g": [], "band depth": []}
                    incidence_sample.geoms.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission] = {"i": [], "band depth": []}
                    emission_sample.geoms.append(emission)

                incidence_sample.data[incidence]["e"].append(e)
                incidence_sample.data[incidence]["theta"].append(e)
                incidence_sample.data[incidence]["g"].append(g)
                incidence_sample.data[incidence]["band depth"].append(depth)
                emission_sample.data[emission]["i"].append(i)
                emission_sample.data[emission]["band depth"].append(depth)

                self.contour_sample.data["all samples"]["e"].append(e)
                self.contour_sample.data["all samples"]["i"].append(i)
                self.contour_sample.data["all samples"]["band depth"].append(depth)

                depths.append(label + ": " + str(depth))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, depths, artifact_warning

    @staticmethod
    def get_e_i_g(label):  # Extract e, i, and g from a label.
        i = int(label.split("i=")[1].split(" ")[0])
        e = int(label.split("e=")[1].split(" ")[0].strip(")"))
        az = int(label.split("az=")[1].strip(")"))
        g = utils.get_phase_angle(i, e, az)
        return e, i, g

    def calculate_slopes(self, left, right):
        left, right = self.validate_left_right(left, right)
        slopes = []
        self.incidence_samples = []
        self.emission_samples = []

        self.contour_sample = Sample("all samples", "file", "title")
        self.contour_sample.data = {"all samples": {"i": [], "e": [], "slope": []}}
        self.contour_sample.geoms = ["all samples"]

        artifact_warning = False

        for i, sample in enumerate(self.samples):
            incidence_sample = Sample(sample.name, sample.file, sample.title)
            emission_sample = Sample(sample.name, sample.file, sample.title)
            for label in sample.geoms:
                e, i, g = self.plotter.get_e_i_g(label)

                if (
                    self.exclude_artifacts
                ):  # If we are excluding artifacts, don't calculate slopes for anything in the range that is
                    # considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning = True  # We'll return this to the controller, which will throw up a dialog
                        # warning the user that we are skipping some spectra.
                        continue

                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(
                    sample.data[label][self.y_axis]
                )  # y_axis is either reflectance or normalized reflectance

                # find reflectance at left and right wavelengths.
                # if we're on the edges, average out a few values.
                w_left, r_left = self.get_vals(wavelengths, reflectance, left)
                w_right, r_right = self.get_vals(wavelengths, reflectance, right)

                slope = (r_right - r_left) / (w_right - w_left)

                incidence = sample.name + " (i=" + str(i) + ")"
                emission = sample.name + " (e=" + str(e) + ")"

                if incidence not in incidence_sample.data:
                    incidence_sample.data[incidence] = {"e": [], "theta": [], "g": [], "slope": []}
                    incidence_sample.geoms.append(incidence)
                if emission not in emission_sample.data:
                    emission_sample.data[emission] = {"i": [], "slope": []}
                    emission_sample.geoms.append(emission)

                incidence_sample.data[incidence]["e"].append(e)
                incidence_sample.data[incidence]["theta"].append(e)
                incidence_sample.data[incidence]["g"].append(g)
                incidence_sample.data[incidence]["slope"].append(slope)
                emission_sample.data[emission]["i"].append(i)
                emission_sample.data[emission]["slope"].append(slope)

                self.contour_sample.data["all samples"]["e"].append(e)
                self.contour_sample.data["all samples"]["i"].append(i)
                self.contour_sample.data["all samples"]["slope"].append(slope)

                slopes.append(label + ": " + str(slope))
            self.emission_samples.append(emission_sample)
            self.incidence_samples.append(incidence_sample)
        self.plot.draw_vertical_lines([left, right])

        return left, right, slopes, artifact_warning

    def validate_left_right(self, left, right):
        try:
            left = float(left)
        except ValueError:
            for sample in self.samples:
                for i, label in enumerate(sample.geoms):
                    wavelengths = np.array(sample.data[label]["wavelength"])
                    if i == 0:
                        left = np.min(wavelengths)
                    else:
                        left = np.min([left, np.min(wavelengths)])
        try:
            right = float(right)
        except ValueError:
            for sample in self.samples:
                for i, label in enumerate(sample.geoms):

                    wavelengths = np.array(sample.data[label]["wavelength"])
                    if i == 0:
                        right = np.max(wavelengths)
                    else:
                        right = np.max([right, np.max(wavelengths)])

        return left, right

    def calculate_error(self, left, right, abs_val):
        left, right = self.validate_left_right(left, right)
        self.error_samples = []
        artifact_warning = False
        error = False

        self.contour_sample = Sample("all samples", "file", "title")
        self.contour_sample.data = {"all samples": {"i": [], "e": [], "difference": []}}
        self.contour_sample.geoms = ["all samples"]

        for i, sample in enumerate(self.samples):
            if i == 0 and len(self.samples) > 1:
                self.base_sample = sample  # Sample(sample.name,sample.file,sample.title)
                continue

            if len(self.samples) == 1:
                # if there is only one sample, we'll use the base to build an error sample with spectra showing
                # difference from middle spectrum in list.
                i = int(len(sample.geoms) / 2)
                self.base_spectrum_label = sample.geoms[i]
                self.base_sample = Sample(
                    self.base_spectrum_label, "file", "title"
                )  # This is used for putting the title onto the new plot (delta R compared to sample (i=x, e=y))

            error_sample = Sample(sample.name, sample.file, sample.title)
            self.error_samples.append(error_sample)

            for label in sample.geoms:
                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(sample.data[label][self.y_axis])
                e, i, g = self.plotter.get_e_i_g(label)
                if (
                    self.exclude_artifacts
                ):  # If we are excluding artifacts, don't calculate slopes for anything in the range that is
                    # considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning = True  # We'll return this to the controller, which will throw up a
                        # dialog warning the user that we are skipping some spectra.
                        continue

                index_left = self.get_index(wavelengths, left)
                index_right = self.get_index(wavelengths, right)

                if len(self.samples) == 1:
                    error_sample.data[label] = {}
                    error_sample.data[label]["difference"] = (
                        reflectance - sample.data[self.base_spectrum_label]["reflectance"]
                    )
                    error_sample.data[label]["wavelength"] = wavelengths
                    error_sample.geoms.append(label)

                    self.contour_sample.data["all samples"]["e"].append(e)
                    self.contour_sample.data["all samples"]["i"].append(i)
                    if index_left != index_right:
                        difference = (
                            reflectance[index_left:index_right]
                            - sample.data[self.base_spectrum_label]["reflectance"][index_left:index_right]
                        )
                        if abs_val:
                            difference = np.abs(difference)
                        self.contour_sample.data["all samples"]["difference"].append(np.mean(difference))
                    else:
                        difference = (
                            reflectance[index_left] - sample.data[self.base_spectrum_label]["reflectance"][index_left]
                        )
                        if abs_val:
                            difference = np.abs(difference)
                        self.contour_sample.data["all samples"]["difference"].append(difference)

                else:
                    found = False
                    for existing_label in self.base_sample.geoms:
                        e_old, i_old, _ = self.plotter.get_e_i_g(existing_label)
                        if e == e_old and i == i_old:
                            error_sample.data[label] = {}
                            error_sample.data[label]["difference"] = (
                                reflectance - self.base_sample.data[existing_label]["reflectance"]
                            )
                            error_sample.data[label]["wavelength"] = wavelengths
                            error_sample.geoms.append(label)

                            self.contour_sample.data["all samples"]["e"].append(e)
                            self.contour_sample.data["all samples"]["i"].append(i)
                            if index_left != index_right:
                                difference = (
                                    reflectance[index_left:index_right]
                                    - self.base_sample.data[existing_label]["reflectance"][index_left:index_right]
                                )
                                if abs_val:
                                    difference = np.abs(difference)
                                self.contour_sample.data["all samples"]["difference"].append(np.mean(difference))
                            else:
                                difference = (
                                    reflectance[index_left]
                                    - self.base_sample.data[existing_label]["reflectance"][index_left]
                                )
                                if abs_val:
                                    difference = np.abs(difference)
                                self.contour_sample.data["all samples"]["difference"].append(difference)

                            found = True
                            break
                    if not found:
                        if error == "":
                            error = "Error: No corresponding spectrum found.\n"
                        error += "\n" + label
                        error_sample.data[label] = {}
                        error_sample.data[label]["difference"] = reflectance
                        error_sample.data[label]["wavelength"] = wavelengths
                        error_sample.geoms.append(label)

                        self.contour_sample.data["all samples"]["e"].append(e)
                        self.contour_sample.data["all samples"]["i"].append(i)
                        self.contour_sample.data["all samples"]["difference"].append(np.mean(reflectance))

        print(error)

        avg_errs = []
        for sample in self.error_samples:
            for label in sample.geoms:
                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(sample.data[label]["difference"])
                index_left = self.get_index(wavelengths, left)
                index_right = self.get_index(wavelengths, right)
                if index_right != index_left:
                    if abs_val:
                        avg = np.mean(np.abs(sample.data[label]["difference"][index_left:index_right]))
                    else:
                        avg = np.mean(sample.data[label]["difference"][index_left:index_right])
                else:
                    avg = sample.data[label]["difference"][index_right]
                avg_errs.append(label + ": " + str(avg))

        self.plot.draw_vertical_lines([left, right])

        return left, right, avg_errs, artifact_warning

    def calculate_reciprocity(self, left, right):
        left, right = self.validate_left_right(left, right)
        avgs = []
        self.recip_samples = (
            []
        )  # for each recip_sample.data[label], there will be up to two points, which should be reciprocal
        # measurements of each other. E.g. recip_sample.name=White Reference,
        # recip_sample.data['White reference (i=-20,e=20)'] will contain data for both i=-30,e=-10, and also i=10, e=30.
        artifact_warning = False

        self.contour_sample = Sample("all samples", "file", "title")
        self.contour_sample.data = {"all samples": {"i": [], "e": [], "delta R": []}}
        self.contour_sample.geoms = ["all samples"]

        for i, sample in enumerate(self.samples):
            recip_sample = Sample(sample.name, sample.file, sample.title)
            for label in sample.geoms:
                e, i, g = self.plotter.get_e_i_g(label)

                if (
                    self.exclude_artifacts
                ):  # If we are excluding artifacts, don't calculate for anything in the range that is
                    # considered to be suspect
                    if self.plotter.artifact_danger(g, left, right):
                        artifact_warning = True  # We'll return this to the controller, which will throw up a
                        # dialog warning the user that we are skipping some spectra.
                        continue

                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(sample.data[label][self.y_axis])

                index_left = self.get_index(wavelengths, left)
                index_right = self.get_index(wavelengths, right)
                if index_right != index_left:
                    avg = np.mean(reflectance[index_left:index_right])
                else:
                    avg = reflectance[index_left]

                recip_label = sample.name + " (i=" + str(-1 * e) + " e=" + str(-1 * i) + ")"

                diff = None
                if label not in recip_sample.data and recip_label not in recip_sample.data:
                    recip_sample.data[label] = {"e": [], "g": [], "i": [], "average reflectance": []}
                    recip_sample.geoms.append(label)

                if label in recip_sample.data:
                    recip_sample.data[label]["e"].append(e)
                    recip_sample.data[label]["i"].append(i)
                    recip_sample.data[label]["g"].append(g)
                    recip_sample.data[label]["average reflectance"].append(avg)

                    if len(recip_sample.data[label]["average reflectance"]) > 1:
                        diff = np.abs(
                            np.max(recip_sample.data[label]["average reflectance"])
                            - np.min(recip_sample.data[label]["average reflectance"])
                        )

                elif recip_label in recip_sample.data:
                    recip_sample.data[recip_label]["e"].append(e)
                    recip_sample.data[recip_label]["i"].append(i)
                    recip_sample.data[recip_label]["g"].append(g)
                    recip_sample.data[recip_label]["average reflectance"].append(avg)
                    if len(recip_sample.data[recip_label]["average reflectance"]) > 1:
                        diff = np.abs(
                            np.max(recip_sample.data[recip_label]["average reflectance"])
                            - np.min(recip_sample.data[recip_label]["average reflectance"])
                        )  # This works fine if for some reason there are multiple measurements for the same sample
                        # at the same geometry. It just takes the min and max.
                        recip = diff / np.mean(recip_sample.data[recip_label]["average reflectance"])

                if diff is not None:
                    avgs.append(label + ": " + str(recip))  # I don't think this is the average of anything
            self.recip_samples.append(recip_sample)

        for sample in self.recip_samples:
            for label in sample.data:
                if len(sample.data[label]["average reflectance"]) > 1:
                    e, i, g = self.get_e_i_g(label)

                    diff = np.abs(
                        np.max(sample.data[label]["average reflectance"])
                        - np.min(sample.data[label]["average reflectance"])
                    )  # This works fine if for some reason there are multiple measurements for the same sample
                    # at the same geometry. It just takes the min and max.
                    recip = diff / np.mean(sample.data[label]["average reflectance"])

                    self.contour_sample.data["all samples"]["e"].append(e)
                    self.contour_sample.data["all samples"]["i"].append(i)
                    self.contour_sample.data["all samples"]["delta R"].append(recip)
                    self.contour_sample.data["all samples"]["e"].append(-1 * i)
                    self.contour_sample.data["all samples"]["i"].append(-1 * e)
                    self.contour_sample.data["all samples"]["delta R"].append(recip)

        self.plot.draw_vertical_lines([left, right])

        return left, right, avgs, artifact_warning

    def plot_error(self, x_axis):
        if x_axis == "e,i":
            x_axis = "contour"
            tab = Tab(
                self.plotter,
                "\u0394" + "R compared to " + self.base_sample.name,
                [self.contour_sample],
                x_axis="contour",
                y_axis="difference",
            )
        else:
            tab = Tab(
                self.plotter,
                "\u0394" + "R compared to " + self.base_sample.name,
                self.error_samples,
                x_axis="wavelength",
                y_axis="difference",
            )
        return tab

    def plot_reciprocity(self, x_axis):
        if x_axis == "e,i":
            x_axis = "contour"
            tab = Tab(self.plotter, "Reciprocity", [self.contour_sample], x_axis=x_axis, y_axis="delta R")
        else:
            tab = Tab(self.plotter, "Reciprocity", self.recip_samples, x_axis=x_axis, y_axis="average reflectance")
        return tab

    def plot_avg_reflectance(self, x_axis):
        if x_axis in ("e", "theta"):
            Tab(
                self.plotter,
                "Reflectance vs " + x_axis,
                self.incidence_samples,
                x_axis=x_axis,
                y_axis="average reflectance",
            )
        elif x_axis == "i":
            Tab(
                self.plotter,
                "Reflectance vs " + x_axis,
                self.emission_samples,
                x_axis=x_axis,
                y_axis="average reflectance",
            )
        elif x_axis == "g":
            Tab(
                self.plotter,
                "Reflectance vs " + x_axis,
                self.incidence_samples,
                x_axis=x_axis,
                y_axis="average reflectance",
            )
        elif x_axis == "e,i":
            Tab(
                self.plotter, "Reflectance", [self.contour_sample], x_axis="contour", y_axis="average reflectance"
            )

    def plot_band_centers(self, x_axis):
        if x_axis in ("e", "theta"):
            Tab(
                self.plotter, "Band center vs " + x_axis, self.incidence_samples, x_axis=x_axis, y_axis="band center"
            )
        elif x_axis == "i":
            Tab(
                self.plotter, "Band center vs " + x_axis, self.emission_samples, x_axis=x_axis, y_axis="band center"
            )
        elif x_axis == "g":
            Tab(
                self.plotter, "Band center vs " + x_axis, self.incidence_samples, x_axis=x_axis, y_axis="band center"
            )
        elif x_axis == "e,i":
            Tab(self.plotter, "Band center", [self.contour_sample], x_axis="contour", y_axis="band center")

    def plot_band_depths(self, x_axis):
        if x_axis in ("e", "theta"):
            Tab(
                self.plotter, "Band depth vs " + x_axis, self.incidence_samples, x_axis=x_axis, y_axis="band depth"
            )
        elif x_axis == "i":
            Tab(
                self.plotter, "Band depth vs " + x_axis, self.emission_samples, x_axis=x_axis, y_axis="band depth"
            )
        elif x_axis == "g":
            Tab(
                self.plotter, "Band depth vs " + x_axis, self.incidence_samples, x_axis=x_axis, y_axis="band depth"
            )
        elif x_axis == "e,i":
            Tab(self.plotter, "Band depth", [self.contour_sample], x_axis="contour", y_axis="band depth")

    def plot_slopes(self, x_axis):
        if x_axis == "e,i":
            Tab(self.plotter, "Slope", [self.contour_sample], x_axis="contour", y_axis="slope")
        elif x_axis in ("e", "theta"):
            Tab(self.plotter, "Slope vs " + x_axis, self.incidence_samples, x_axis=x_axis, y_axis="slope")
        elif x_axis == "i":
            Tab(self.plotter, "Slope vs " + x_axis, self.emission_samples, x_axis=x_axis, y_axis="slope")
        elif x_axis == "g":
            Tab(self.plotter, "Slope vs " + x_axis, self.incidence_samples, x_axis=x_axis, y_axis="slope")
        elif x_axis == "i,e":
            Tab(self.plotter, "Slope", [self.contour_sample], x_axis="contour", y_axis="slope")

    # not implemented
    def calculate_photometric_variability(self, left, right):
        left = float(left)
        right = float(right)
        photo_var = []

        for sample in self.samples:
            min_slope = None
            max_slope = None
            for i, label in enumerate(sample.geoms):

                wavelengths = np.array(sample.data[label]["wavelength"])
                reflectance = np.array(sample.data[label]["reflectance"])
                index_left = (np.abs(wavelengths - left)).argmin()  # find index of wavelength
                index_right = (np.abs(wavelengths - right)).argmin()  # find index of wavelength
                slope = (reflectance[index_right] - reflectance[index_left]) / (index_right - index_left)
                if i == 0:
                    min_slope = slope
                    min_slope_label = label.split("(")[1].strip(")") + " (" + str(slope) + ")"
                    max_slope = slope
                    max_slope_label = label.split("(")[1].strip(")") + " (" + str(slope) + ")"
                else:
                    if slope < min_slope:
                        min_slope = slope
                        min_slope_label = label.split("(")[1].strip(")") + " (" + str(slope) + ")"
                    if slope > max_slope:
                        max_slope = slope
                        max_slope_label = label.split("(")[1].strip(")") + " (" + str(slope) + ")"

            var = max_slope - min_slope
            photo_var.append(sample.name + ": " + str(var))
            photo_var.append("  min: " + min_slope_label)
            photo_var.append("  max: " + max_slope_label)

        self.plot.draw_vertical_lines([left, right])

        return photo_var

    def normalize(self, wavelength):
        wavelength = float(wavelength)

        normalized_samples = []
        for sample in self.samples:

            normalized_sample = Sample(
                sample.name, sample.file, sample.title
            )  # Note that we aren't editing the original samples list, we're making entirely new objects.
            # This way we can reset later.
            for label in sample.geoms:
                wavelengths = np.array(sample.data[label]["wavelength"])
                if "reflectance" in sample.data[label]:
                    reflectance = np.array(sample.data[label]["reflectance"])
                else:
                    reflectance = np.array(sample.data[label]["normalized reflectance"])
                index = (
                    np.abs(wavelengths - wavelength)
                ).argmin()  # find index of wavelength closest to wavelength we want to normalize to

                multiplier = 1 / reflectance[index]  # Normalize to 1

                reflectance = reflectance * multiplier
                reflectance = list(reflectance)
                # if label not in normalized_sample.data:
                normalized_sample.data[label] = {"wavelength": [], "normalized reflectance": []}

                normalized_sample.geoms.append(label)
                normalized_sample.data[label]["wavelength"] = wavelengths
                normalized_sample.data[label]["normalized reflectance"] = reflectance

                # normalized_sample.add_spectrum(label, reflectance,sample.data[label]['wavelength'])
            normalized_samples.append(normalized_sample)
        self.samples = normalized_samples

        self.refresh(
            original=self.original_samples, xlim=self.xlim, y_axis="normalized reflectance"
        )  # Let the tab know this data has been modified and we want to hold on to a separate set of original
        # samples. If we're zoomed in, save the xlim but not the ylim (since y scale will be changing)

    @staticmethod
    def lift_widget(widget):
        widget.focus_set()
        widget.lift()

    def get_sample(self, sample_name):
        if ":" in sample_name:
            title = sample_name.split(":")[0]
            name = sample_name.split(":")[1]
        else:
            title = None
            name = sample_name
        for sample in self.samples:
            if name == sample.name:
                if title is None or sample.title == title:
                    return sample
        return None

    def set_color(self, sample_name, color):
        sample = self.get_sample(sample_name)
        if isinstance(color, int):  # If the user entered a custom hue value
            hue = color
        else:
            color_index = self.plot.color_names.index(color)
            hue = self.plot.hues[color_index]
        sample.set_colors(hue)
        self.plot.draw()

    def set_linestyle(self, sample_name, linestyle):
        sample = self.get_sample(sample_name)
        linestyles = {"Solid": "-", "Dash": "--", "Dot": ":", "Dot-dash": "-."}
        sample.set_linestyle(linestyles[linestyle])
        self.plot.draw()

    def set_markerstyle(self, sample_name, markerstyle):
        sample = self.get_sample(sample_name)
        markerstyles = {"Circle": "o", "X": "x", "Diamond": "D", "Triangle": "^"}
        sample.set_markerstyle(markerstyles[markerstyle])
        #         for sample in self.samples:
        #             sample.restart_color_cycle() #Makes sure that we start at the same point for replotting
        self.plot.draw()

    def set_legend_style(self, legend_style):
        self.plot.draw_legend(legend_style)

    #         self.refresh(original=self.original_samples, xlim=self.xlim, ylim=self.ylim, y_axis=self.y_axis)
    def set_title(self, title):
        self.plotter.titles.remove(self.notebook_title)
        self.title = title
        base = title
        i = 1
        while title in self.plotter.titles:
            title = base + " (" + str(i) + ")"
            i = i + 1
        self.notebook_title = title
        self.plotter.titles.append(self.notebook_title)
        self.plot.set_title(title)
        self.plotter.notebook.tab(self.top, text=title + " x")

    def reset(self):
        self.samples = self.original_samples
        self.exclude_artifacts = False
        self.refresh()

    def close_right_click_menu(self, event):
        # pylint: disable = unused-argument
        self.popup_menu.unpost()

    def open_analysis_tools(self):
        # Build up lists of strings telling available samples, which of those samples a currently plotted,
        # and a dictionary mapping those strings to the sample options.
        self.build_sample_lists()
        self.plotter.controller.open_analysis_tools(self)

    def open_plot_settings(self):
        self.build_sample_lists()
        self.plotter.controller.open_plot_settings(self)

    def build_sample_lists(self):
        # Sample options will be the list of strings to put in the listbox. It may include the sample title,
        # depending on whether there is more than one title.
        self.sample_options_dict = {}
        self.sample_options_list = []
        self.existing_indices = []

        # Each file got a title assigned to it when loaded, so each group of samples from a file will
        # have a title associated with them.
        # If there are multiple possible titles, list that in the listbox along with the sample name.
        if len(self.plotter.titles) > 1:
            for i, sample in enumerate(self.plotter.sample_objects):
                for plotted_sample in self.samples:
                    if sample.name == plotted_sample.name and sample.file == plotted_sample.file:
                        self.existing_indices.append(i)
                self.sample_options_dict[sample.title + ": " + sample.name] = sample
                self.sample_options_list.append(sample.title + ": " + sample.name)
        # Otherwise, the user knows what the title is (there is only one)
        else:
            for i, sample in enumerate(self.plotter.sample_objects):
                for plotted_sample in self.samples:
                    if sample.name == plotted_sample.name and sample.file == plotted_sample.file:
                        self.existing_indices.append(i)
                self.sample_options_dict[sample.name] = sample
                self.sample_options_list.append(sample.name)

        return self.sample_options_list

    # We want to pass a list of existing samples and a list of possible samples.
    def ask_which_samples(self):
        # Build up lists of strings telling available samples, which of those samples a currently plotted, and
        # a dictionary mapping those strings to the sample options.
        self.build_sample_lists()
        # We tell the controller which samples are already plotted so it can initiate the listbox with those
        # samples highlighted.
        self.plotter.controller.ask_plot_samples(
            self, self.existing_indices, self.sample_options_list, self.geoms, self.title
        )

    def set_samples(
        self, listbox_labels, title, incidences, emissions, azimuths, exclude_specular=False, tolerance=None
    ):
        # we made a dict mapping sample labels for a listbox to available samples to plot. This was passed back
        # when the user clicked ok. Reset this tab's samples to be those ones, then replot.
        self.samples = []
        if title == "":
            title = ", ".join(listbox_labels)
        for label in listbox_labels:
            self.samples.append(self.sample_options_dict[label])

        self.geoms = {"i": incidences, "e": emissions, "az": azimuths}
        print("azimuths: ")
        print(azimuths)
        self.exclude_specular = exclude_specular
        if self.exclude_specular:
            try:
                self.specularity_tolerance = int(tolerance)
            except ValueError:
                self.specularity_tolerance = 0
        winnowed_samples = (
            []
        )  # These will only have the data we are actually going to plot, which will only be from the
        # specificied geometries.

        for i, sample in enumerate(self.samples):
            winnowed_sample = Sample(sample.name, sample.file, sample.title)

            for geom in sample.geoms:  # For every spectrum associated with the sample,
                # check if it is for a geometry we are going to plot.
                # if it is, attach that spectrum to the winnowed sample data
                try:  # If there is no geometry information for this sample, this will throw an exception.
                    i = geom[0]
                    e = geom[1]
                    az = geom[2]
                    if self.check_geom(
                        i, e, az, exclude_specular, self.specularity_tolerance
                    ):  # If this is a geometry we are supposed to plot
                        winnowed_sample.add_spectrum(
                            geom, sample.data[geom]["reflectance"], sample.data[geom]["wavelength"]
                        )
                except (IndexError, KeyError):  # If there's no geometry information, plot the sample.
                    print("plotting spectrum with invalid geometry information")
                    winnowed_sample.add_spectrum(
                        geom, sample.data[geom]["reflectance"], sample.data[geom]["wavelength"]
                    )
            winnowed_samples.append(winnowed_sample)

        self.samples = winnowed_samples
        self.title = title
        self.refresh()

    def refresh(
        self, original=None, xlim=None, ylim=None, x_axis="wavelength", y_axis="reflectance"
    ):  # Gets called when data is updated, either from edit plot or analysis tools. We set original = False if
        # calling from normalize, that way we will still hold on to the unchanged data.
        tab_index = self.plotter.notebook.index(self.plotter.notebook.select())
        self.plotter.notebook.forget(self.plotter.notebook.select())
        self.__init__(
            self.plotter,
            self.title,
            self.samples,
            tab_index=tab_index,
            geoms=self.geoms,
            original=original,
            xlim=xlim,
            ylim=ylim,
            x_axis=x_axis,
            y_axis=y_axis,
            exclude_artifacts=self.exclude_artifacts,
            exclude_specular=self.exclude_specular,
            specularity_tolerance=self.specularity_tolerance,
        )

    def open_right_click_menu(self, event):
        self.popup_menu.post(event.x_root + 10, event.y_root + 1)
        self.popup_menu.grab_release()

    def close(self):
        tabid = self.plotter.notebook.select()
        self.plotter.notebook.forget(tabid)
        self.plotter.titles.remove(self.notebook_title)

    def check_geom(self, i, e, az, exclude_specular=False, tolerance=None):
        i = int(float(i))  # Get exception from int('0.0')
        e = int(float(e))
        if az is not None:
            az = int(float(az))

        if exclude_specular:
            if np.abs(int(i) - (-1 * int(e))) <= tolerance:
                return False

        good_i = False
        if i in self.geoms["i"] or self.geoms["i"] == []:
            good_i = True

        good_e = False
        if e in self.geoms["e"] or self.geoms["e"] == []:
            good_e = True

        good_az = False
        if az in self.geoms["az"] or self.geoms["az"] == []:
            good_az = True

        return good_i and good_e and good_az

    def adjust_x(self, left, right):
        left = float(left)
        right = float(right)
        self.xlim = [left, right]
        self.plot.adjust_x(left, right)

    def adjust_y(self, bottom, top):
        bottom = float(bottom)
        top = float(top)
        self.ylim = [bottom, top]
        self.plot.adjust_y(bottom, top)

    def adjust_z(self, low, high):  # only gets called for contour plot
        bottom = float(low)
        top = float(high)
        self.zlim = [low, high]
        self.plot.adjust_z(bottom, top)
