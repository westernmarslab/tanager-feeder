# Plotter takes a Tk root object and uses it as a base to spawn Tk Toplevel plot windows.

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import numpy as np
from tkinter import BOTH, Menu, Frame
from tkinter import filedialog
import colorutils
import matplotlib.tri as mtri


from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from tanager_feeder.verticalscrolledframe import VerticalScrolledFrame  # slightly different than vsf defined in main
from tanager_feeder import utils


# These are related to the region of spectra that are sensitive to polarization artifacts. This is at high phase angles between 1000 and 1400 nm.
MIN_WAVELENGTH_ARTIFACT_FREE = 1000
MAX_WAVELENGTH_ARTIFACT_FREE = 1400
MIN_G_ARTIFACT_FREE = -20
MAX_G_ARTIFACT_FREE = 40


class Plotter:
    def __init__(self, controller, dpi, style):

        self.num = 0
        self.controller = controller
        self.notebook = self.controller.view_notebook
        self.dpi = dpi
        self.titles = []
        self.style = style
        plt.style.use(style)

        self.tabs = []
        self.samples = {}
        self.sample_objects = []

        self.notebook.bind("<Button-1>", lambda event: self.notebook_click(event))
        self.notebook.bind("<Motion>", lambda event: self.mouseover_tab(event))
        self.menus = []

        self.save_dir = None  # This will get set 1)when the user plots data for the first time to be that folder. 2) if the user saves a plot so that the next time they click save plot, the save dialog opens into the same directory where they just saved.

    def get_path(self):
        initialdir = self.save_dir

        path = None
        print("asksaveas")
        if initialdir != None:
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

    def get_index(self, array, val):
        index = (np.abs(array - val)).argmin()
        return index

    def notebook_click(self, event):
        self.close_right_click_menus(event)
        self.maybe_close_tab(event)

    def update_tab_names(self):
        pass

    def new_tab(self):
        tab = Tab(self, "New tab", [], title_override=True)
        self.tabs.append(tab)
        tab.ask_which_samples()

    def set_height(self, height):
        for tab in self.tabs:
            tab.top.configure(height=height)

    # caption should get
    def plot_spectra(self, title, file, caption, exclude_wr=True, draw=True):
        if title == "":
            title = "Plot " + str(self.num + 1)
            self.num += 1
        elif title in self.titles:
            j = 1
            new = title + " (" + str(j) + ")"
            while new in self.titles:
                j += 1
                new = title + " (" + str(j) + ")"
            title = new

        try:
            wavelengths, reflectance, labels = self.load_data(file)
        except:
            raise (Exception("Error loading data!"))
            return

        for i, spectrum_label in enumerate(labels):
            sample_label = spectrum_label.split(" (i")[0]

            # If we don't have any data from this file yet, add it to the samples dictionary, and place the first sample inside.
            if file not in self.samples:
                self.samples[file] = {}
                new = Sample(sample_label, file, title)
                self.samples[file][sample_label] = new
                self.sample_objects.append(new)

            # If there is already data associated with this file, check if we've already got the sample in question there. If it doesn't exist, make it. If it does, just add this spectrum and label into its data dictionary.
            else:
                sample_exists = False
                for sample in self.samples[file]:
                    if self.samples[file][sample].name == sample_label:
                        sample_exists = True

                if sample_exists == False:
                    new = Sample(sample_label, file, title)
                    self.samples[file][sample_label] = new
                    self.sample_objects.append(new)

            # if spectrum_label not in self.samples[file][sample_label].geoms: #This should do better and actually check that all the data is an exact duplicate, but that seems hard. Just don't label things exactly the same and save them in the same file with the same viewing geometry.
            # self.samples[file][sample_label].add_spectrum(spectrum_label, reflectance[i], wavelengths)
            spectrum_label = spectrum_label.replace(")", "").replace("(", "")
            if "i=" in spectrum_label.replace(" ", ""):
                incidence = spectrum_label.split("i=")[1].split(" ")[0]
            else:
                incidence = None
            if "e=" in spectrum_label.replace(" ", ""):
                emission = spectrum_label.split("e=")[1].split(" ")[0]
            else:
                emission = None
            if "az=" in spectrum_label.replace(" ", ""):
                azimuth = spectrum_label.split("az=")[1]
            else:
                azimuth = None
            geom = (incidence, emission, azimuth)
            self.samples[file][sample_label].add_spectrum(geom, reflectance[i], wavelengths)

        new_samples = []
        for sample in self.samples[file]:
            new_samples.append(self.samples[file][sample])

        #         tab=Tab(self,title+': '+new_samples[0].name,[new_samples[0]], draw=draw)
        #         tab=Tab(self,title+': '+new_samples[0].name,[new_samples[0]], draw=draw)
        self.new_tab()

    #         self.tabs.append(tab)

    def load_data(self, file, format="spectral_database_csv"):
        labels = []
        # This is the format I was initially using. It is a simple .tsv file with a single row of headers e.g. Wavelengths     Sample_1 (i=0 e=30)     Sample_2 (i=0 e=30).
        if format == "simple_tsv":
            data = np.genfromtxt(file, names=True, dtype=float, encoding=None, delimiter="\t", deletechars="")
            labels = list(data.dtype.names)[1:]  # the first label is wavelengths
            for i in range(len(labels)):
                labels[i] = labels[i].replace("_(i=", " (i=").replace("_e=", " e=").replace("( i", "(i")
        # This is the current format, which is compatible with the WWU spectral library format.
        elif format == "spectral_database_csv":
            skip_header = 1

            labels_found = False  # We want to use the Sample Name field for labels, but if we haven't found that yet we may use Data ID, Sample ID, or mineral name instead.
            with open(file, "r") as file2:
                line = file2.readline()
                i = 0
                while (
                    line.split(",")[0].lower() != "wavelength" and line != "" and line.lower() != "wavelength\n"
                ):  # Formatting can change slightly if you edit your .csv in libreoffice or some other editor, this captures different options. line will be '' only at the end of the file (it is \n for empty lines)
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
                        if (
                            labels_found == False
                        ):  # Only use Data ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    elif line[0:9].lower() == "sample id":
                        if (
                            labels_found == False
                        ):  # Only use Sample ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    elif line[0:12].lower() == "mineral name":
                        if (
                            labels_found == False
                        ):  # Only use mineral ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    skip_header += 1
                    line = file2.readline()

            data = np.genfromtxt(
                file, skip_header=skip_header, dtype=float, delimiter=",", encoding=None, deletechars=""
            )

        data = zip(*data)
        wavelengths = []
        reflectance = []
        for i, d in enumerate(data):
            if i == 0 and len(d) > 500:
                wavelengths = d[
                    60:
                ]  # the first column in my .csv (now first row) was wavelength in nm. Exclude the first 100 values because they are typically very noisy.
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
        if dist_to_edge == None:  # not on a tab
            return

        if dist_to_edge < 18:
            index = self.notebook.index("@%d,%d" % (event.x, event.y))
            tab = self.notebook.tab("@%d,%d" % (event.x, event.y))
            name = tab["text"][:-2]
            if index != 0:
                self.notebook.forget(index)
                try:
                    self.titles.remove(name)
                except:
                    print(name)
                    print("NOT IN TITLES!")
                self.notebook.event_generate("<<NotebookTabClosed>>")

    # This capitalizes Xs for closing tabs when you hover over them.
    def mouseover_tab(self, event):
        dist_to_edge = self.dist_to_edge(event)
        if dist_to_edge == None or dist_to_edge > 17:  # not on an X, or not on a tab at all.
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
            else:
                self.notebook.tab("@%d,%d" % (event.x, event.y), text=text + "X")

    def close_right_click_menus(self, event):
        for menu in self.menus:
            menu.unpost()

    def dist_to_edge(self, event):
        id_str = "@" + str(event.x) + "," + str(event.y)  # This is the id for the tab that was just clicked on.
        try:
            tab0 = self.notebook.tab(id_str)
            tab = self.notebook.tab(id_str)
        # There might not actually be any tab here at all.
        except:
            return None
        dist_to_edge = 0
        while (
            tab == tab0
        ):  # While not leaving the current tab, walk pixel by pixel toward the tab edge to count how far it is.
            dist_to_edge += 1
            id_str = "@" + str(event.x + dist_to_edge) + "," + str(event.y)
            try:
                tab = self.notebook.tab(id_str)
            except:  # If this didn't work, we were off the right edge of any tabs.
                break

        return dist_to_edge

    def get_e_i_g(self, label):  # Extract e, i, and g from a label.
        i = int(label.split("i=")[1].split(" ")[0])
        e = int(label.split("e=")[1].strip(")"))
        if i <= 0:
            g = e - i
        else:
            g = -1 * (e - i)
        return e, i, g

    def artifact_danger(self, g, left=0, right=100000000000000000000):
        if (
            g < MIN_G_ARTIFACT_FREE or g > MAX_G_ARTIFACT_FREE
        ):  # If the phase angle is outside the safe region, we might have potential artifacts, but only at specific wavelengths.
            if (
                left > MIN_WAVELENGTH_ARTIFACT_FREE and left < MAX_WAVELENGTH_ARTIFACT_FREE
            ):  # if the left wavelength is in the artifact zone
                return True
            elif (
                right > MIN_WAVELENGTH_ARTIFACT_FREE and right < MAX_WAVELENGTH_ARTIFACT_FREE
            ):  # if the right wavelength is in the artifact zone
                return True
            elif (
                left < MIN_WAVELENGTH_ARTIFACT_FREE and right > MAX_WAVELENGTH_ARTIFACT_FREE
            ):  # If the region spans the artifact zone
                return True
            else:
                return False
        else:  # If we're at a safe phase angle
            return False


class NotScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        self.interior = self
        self.scrollbar = NotScrollbar()


class NotScrollbar:
    def __init__(self):
        pass

    def pack_forget(self):
        pass