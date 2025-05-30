# Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.
from tkinter import TclError, filedialog

import matplotlib.pyplot as plt
import numpy as np

from tanager_feeder import utils
from tanager_feeder.plotter.sample import Sample
from tanager_feeder.plotter.tab import Tab
from tanager_data_io.data_io import DataIO


class PlotWorkbook(DataIO):
    def __init__(self, controller, dpi, style):
        super().__init__()
        self.num = 0
        self.num = 0
        self.controller = controller
        self.notebook = self.controller.view_notebook
        self.dpi = dpi
        self.titles = []  # Tab titles
        self.dataset_names = []  # 1 per file plotted
        self.style = style
        plt.style.use(style)

        self.tabs = []
        self.samples = {}
        self.sample_objects = []

        self.notebook.bind("<Button-1>", lambda event: self.notebook_click(event))
        self.notebook.bind("<Motion>", lambda event: self.mouseover_tab(event))
        self.menus = []

        self.save_dir = None  # This will get set 1)when the user plots data for the first time to be that folder. 2)
        # if the user saves a plot so that the next time they click save plot, the save dialog opens into the same
        # directory where they just saved.

    #called from Plot.save()
    def get_path(self):
        initialdir = self.save_dir
        if initialdir is not None:
            path = filedialog.asksaveasfilename(initialdir=initialdir)
        else:
            path = filedialog.asksaveasfilename()

        self.save_dir = path
        if "\\" in path:
            self.save_dir = "\\".join(path.split("\\")[0:-1])
        elif "/" in path:
            self.save_dir = "/".join(path.split("/")[0:-1])
        return path

    def notebook_click(self, event):
        self.close_right_click_menus(event)
        self.maybe_close_tab(event)

    def new_tab(self):
        tab = Tab(self, "New tab", [])
        self.tabs.append(tab)
        tab.ask_which_samples()

    def set_height(self, height):
        for tab in self.tabs:
            tab.top.configure(height=height)

    def maybe_close_tab(self, event):
        dist_to_edge = self.dist_to_edge(event)
        if dist_to_edge is None:  # not on a tab
            return

        if dist_to_edge < 18:
            index = self.notebook.index("@%d,%d" % (event.x, event.y))
            tab = self.notebook.tab("@%d,%d" % (event.x, event.y))
            name = tab["text"][:-2]
            if index != 0:
                self.notebook.forget(index)
                try:
                    self.titles.remove(name)
                except IndexError:
                    print(f"Warning: {name} not in titles.")
                self.notebook.event_generate("<<NotebookTabClosed>>")

    # This capitalizes Xs for closing tabs when you hover over them.
    def mouseover_tab(self, event):
        dist_to_edge = self.dist_to_edge(event)
        if dist_to_edge is None or dist_to_edge > 17:  # not on an X, or not on a tab at all.
            for i, tab in enumerate(self.notebook.tabs()):
                if i == 0:
                    continue  # Don't change text on Goniometer view tab
                text = self.notebook.tab(tab, option="text")
                self.notebook.tab(
                    tab, text=text[0:-1] + "x"
                )  # Otherwise, make sure you have a lowercase 'x' at the end of each tab name.

        else:
            tab = self.notebook.tab("@%d,%d" % (event.x, event.y))
            text = tab["text"][:-1]
            if "Goniometer" in text:
                return
            self.notebook.tab("@%d,%d" % (event.x, event.y), text=text + "X")

    def close_right_click_menus(self, event):
        # pylint: disable = unused-argument
        for menu in self.menus:
            menu.unpost()

    def dist_to_edge(self, event):
        id_str = "@" + str(event.x) + "," + str(event.y)  # This is the id for the tab that was just clicked on.
        try:
            tab0 = self.notebook.tab(id_str)
            tab = self.notebook.tab(id_str)
        # There might not actually be any tab here at all.
        except TclError:
            return None
        dist_to_edge = 0
        while (
            tab == tab0
        ):  # While not leaving the current tab, walk pixel by pixel toward the tab edge to count how far it is.
            dist_to_edge += 1
            id_str = "@" + str(event.x + dist_to_edge) + "," + str(event.y)
            try:
                tab = self.notebook.tab(id_str)
            except TclError:  # If this didn't work, we were off the right edge of any tabs.
                break

        return dist_to_edge

    # @staticmethod
    # def get_e_i_g(label):  # Extract e, i, and g from a label.
    #     i = int(label.split("i=")[1].split(" ")[0])
    #     e = int(label.split("e=")[1].strip(")"))
    #     az = int(label.split("az=")[1].strip(")"))
    #     g = utils.get_phase_angle(i, e, az)
    #     return e, i, g

    @staticmethod
    def get_winnowed_samples(geoms, all_samples, exclude_specular, specularity_tolerance):
        winnowed_samples = (
            []
        )  # These will only have the data we are actually going to plot, which will only be from the
        # specified geometries.

        for i, sample in enumerate(all_samples):
            winnowed_sample = Sample(sample.name, sample.file, sample.title)

            for geom in sample.geoms:  # For every spectrum associated with the sample,
                # check if it is for a geometry we are going to plot.
                # if it is, attach that spectrum to the winnowed sample data
                try:  # If there is no geometry information for this sample, this will throw an exception.
                    i, e, az = utils.get_i_e_az(geom)
                    if PlotWorkbook.check_geom(
                            geoms, i, e, az, exclude_specular, specularity_tolerance
                    ):  # If this is a geometry we are supposed to plot
                        winnowed_sample.add_spectrum(
                            geom, sample.data[geom]["reflectance"], sample.data[geom]["wavelength"]
                        )
                except (IndexError, KeyError):  # If there's no geometry information, plot the sample.
                    print("Warning: Plotting spectrum with invalid geometry information")
                    winnowed_sample.add_spectrum(
                        geom, sample.data[geom]["reflectance"], sample.data[geom]["wavelength"]
                    )
            winnowed_samples.append(winnowed_sample)

        return winnowed_samples

    @staticmethod
    def check_geom(geoms, i, e, az, exclude_specular=False, tolerance=None):
        i = int(float(i))  # Get exception from int('0.0')
        e = int(float(e))
        if az is not None:
            az = int(float(az))

        if exclude_specular:
            if np.abs(int(i) - (-1 * int(e))) <= tolerance:
                return False

        good_i = False
        if i in geoms["i"] or geoms["i"] == []:
            good_i = True

        good_e = False
        if e in geoms["e"] or geoms["e"] == []:
            good_e = True

        good_az = False
        if az in geoms["az"] or geoms["az"] == []:
            good_az = True

        return good_i and good_e and good_az

    @staticmethod
    def artifact_danger(g, left=0, right=100000000000000000000):
        if (
            g < utils.MIN_G_ARTIFACT_FREE or g > utils.MAX_G_ARTIFACT_FREE
        ):  # If the phase angle is outside the safe region, we might have potential artifacts, but only at specific
            # wavelengths.
            if (
                utils.MIN_WAVELENGTH_ARTIFACT_FREE < left < utils.MAX_WAVELENGTH_ARTIFACT_FREE
            ):  # if the left wavelength is in the artifact zone
                return True
            if (
                utils.MIN_WAVELENGTH_ARTIFACT_FREE < right < utils.MAX_WAVELENGTH_ARTIFACT_FREE
            ):  # if the right wavelength is in the artifact zone
                return True
            if (
                left < utils.MIN_WAVELENGTH_ARTIFACT_FREE and right > utils.MAX_WAVELENGTH_ARTIFACT_FREE
            ):  # If the region spans the artifact zone
                return True
        return False
