# Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.
from tkinter import filedialog, TclError

import matplotlib.pyplot as plt
import numpy as np

from tanager_feeder import utils
from tanager_feeder.plotter.tab import Tab
from tanager_feeder.plotter.sample import Sample
from tanager_feeder.dialogs.error_dialog  import ErrorDialog


class Plotter:
    def __init__(self, controller, dpi, style):

        self.num = 0
        self.controller = controller
        self.notebook = self.controller.view_notebook
        self.dpi = dpi
        self.titles = [] # Tab titles
        self.dataset_names = [] # 1 per file plotted
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

    def get_path(self):
        initialdir = self.save_dir
        if initialdir is not None:
            print("initial dir set to " + self.save_dir)
            path = filedialog.asksaveasfilename(initialdir=initialdir)
        else:
            path = filedialog.asksaveasfilename()

        self.save_dir = path
        if "\\" in path:
            self.save_dir = "\\".join(path.split("\\")[0:-1])
        elif "/" in path:
            self.save_dir = "/".join(path.split("/")[0:-1])
        print("return")
        return path

    @staticmethod
    def get_index(array, val):
        index = (np.abs(array - val)).argmin()
        return index

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

    def load_samples(self, dataset_name, file):

        try:
            wavelengths, reflectance, labels = self.read_csv(file)
        except OSError:
            ErrorDialog(self.controller, "Error", "Error: Could not load data.")
            print("Error: Could not load data.")
            return

        if dataset_name not in self.samples:
            self.samples[dataset_name] = {}

        for i, spectrum_label in enumerate(labels):
            sample_label = spectrum_label.split(" (i")[0]

            # Check if we've already got the sample in question in the dataset.
            # If it doesn't exist, make it. If it does, just add this spectrum and label into its data
            # dictionary.
            sample_exists = False
            for sample in self.samples[dataset_name]:
                if self.samples[dataset_name][sample].name == sample_label:
                    sample_exists = True

            if not sample_exists:
                new = Sample(sample_label, file, dataset_name)
                self.samples[dataset_name][sample_label] = new
                self.sample_objects.append(new)

            # if spectrum_label not in self.samples[dataset_name][sample_label].geoms: #This should do better and actually
            # check that all the data is an exact duplicate, but that seems hard. Just don't label things exactly the
            # same and save them in the same file with the same viewing geometry.
            spectrum_label = spectrum_label.replace(")", "").replace("(", "")
            if "i=" in spectrum_label.replace(" ", ""):
                incidence = float(spectrum_label.split("i=")[1].split(" ")[0])
            else:
                incidence = None
            if "e=" in spectrum_label.replace(" ", ""):
                emission = float(spectrum_label.split("e=")[1].split(" ")[0])
            else:
                emission = None
            if "az=" in spectrum_label.replace(" ", ""):
                azimuth = float(spectrum_label.split("az=")[1])
            else:
                azimuth = None
            geom = (incidence, emission, azimuth)
            self.samples[dataset_name][sample_label].add_spectrum(geom, reflectance[i], wavelengths)

        self.new_tab()

    @staticmethod
    def read_csv(file, file_format="spectral_database_csv"):
        labels = []
        # This is the format I was initially using. It is a simple .tsv file with a single row of headers
        # e.g. Wavelengths     Sample_1 (i=0 e=30)     Sample_2 (i=0 e=30).
        if file_format == "simple_tsv":
            data = np.genfromtxt(file, names=True, dtype=float, encoding=None, delimiter="\t", deletechars="")
            labels = list(data.dtype.names)[1:]  # the first label is wavelengths
            for i, label in enumerate(labels):
                labels[i] = label.replace("_(i=", " (i=").replace("_e=", " e=").replace("( i", "(i")
        # This is the current format, which is compatible with the WWU spectral library format.
        elif file_format == "spectral_database_csv":
            skip_header = 1

            labels_found = False  # We want to use the Sample Name field for labels, but if we haven't found
            # that yet we may use Data ID, Sample ID, or mineral name instead.
            with open(file, "r") as file2:
                line = file2.readline()
                i = 0
                while (
                    line.split(",")[0].lower() != "wavelength" and line != "" and line.lower() != "wavelength\n"
                ):  # Formatting can change slightly if you edit your .csv in libreoffice or some other editor,
                    # this captures different options. line will be '' only at the end of the file (it is \n for
                    # empty lines)
                    i += 1
                    if line[0:11].lower() == "sample name":
                        labels = line.split(",")[1:]
                        labels[-1] = labels[-1].strip("\n")
                        labels_found = True  #
                    elif line[0:16].lower() == "viewing geometry":
                        for i, geom in enumerate(line.split(",")[1:]):
                            geom = geom.strip("\n").replace(" i", "i")
                            labels[i] += " (" + geom + ")"
                    elif line[0:7].lower() == "data id":
                        if not labels_found:  # Only use Data ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    elif line[0:9].lower() == "sample id":
                        if not labels_found:  # Only use Sample ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    elif line[0:12].lower() == "mineral name":
                        if not labels_found:  # Only use mineral ID for labels if we haven't found
                            # the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    skip_header += 1
                    line = file2.readline()
        try:
            data = np.genfromtxt(
                file, skip_header=skip_header, dtype=float, delimiter=",", encoding=None, deletechars=""
            )
        except ValueError as e:
            raise e

        data = zip(*data)
        wavelengths = []
        reflectance = []
        for i, d in enumerate(data):
            if i == 0 and len(d) > 500:
                wavelengths = d[
                    60:
                ]  # the first column in my .csv (now first row) was wavelength in nm. Exclude the first 60 values
                # because they are typically very noisy.
            elif i == 0:
                wavelengths = d
            elif len(d) > 500:  # the other columns are all reflectance values
                d = np.array(d)
                reflectance.append(d[60:])
            else:
                d = np.array(d)
                reflectance.append(d)
        return wavelengths, reflectance, labels

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
                    print(name)
                    print("NOT IN TITLES!")
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

    @staticmethod
    def get_e_i_g(label):  # Extract e, i, and g from a label.
        i = int(label.split("i=")[1].split(" ")[0])
        e = int(label.split("e=")[1].strip(")"))
        az = int(label.split("az=")[1].strip(")"))
        # TODO: make this work for both 2D and 3D geometries.
        g = utils.get_phase_angle(i, e, az)
        return e, i, g

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
