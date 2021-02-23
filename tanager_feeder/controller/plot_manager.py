import os
from tkinter import Entry, Button, Label, Checkbutton, Toplevel, Frame, LEFT, RIGHT, IntVar
from tkinter.filedialog import askopenfilename

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.remote_file_explorer import RemoteFileExplorer
from tanager_feeder import utils


class PlotManager:
    def __init__(self, controller: utils.ControllerType):
        self.controller = controller
        self.plotter = self.controller.plotter
        self.config_info = controller.config_info
        self.tk_format = utils.TkFormat(self.controller.config_info)

        try:
            with open(self.config_info.local_config_loc + "plot_config.txt", "r") as plot_config:
                self.plot_local_remote = plot_config.readline().strip("\n")
                self.plot_input_file = plot_config.readline().strip("\n")
                self.plot_title = plot_config.readline().strip("\n")
        except OSError:
            print("No past plotting location found. Using default.")
            with open(self.config_info.local_config_loc + "plot_config.txt", "w+") as f:
                f.write("remote")
                f.write("C:\\Users\n")
                f.write("C:\\Users\n")

            self.plot_local_remote = "remote"
            self.plot_title = ""
            self.plot_input_file = "C:\\Users"

        self.plot_remote = IntVar()
        self.plot_local = IntVar()
        if self.plot_local_remote == "remote":
            self.plot_remote.set(1)
            self.plot_local.set(0)
        else:
            self.plot_local.set(1)
            self.plot_remote.set(0)

        self.plot_local_check = None
        self.plot_remote_check = None
        self.plot_title_entry = None
        self.plot_input_dir_entry = None
        self.plot_top = None

    def show(self) -> None:
        self.plot_top = Toplevel(self.controller.master)
        self.plot_top.wm_title("Plot")
        plot_frame = Frame(self.plot_top, bg=self.tk_format.bg, pady=2 * self.tk_format.pady, padx=15)
        plot_frame.pack()

        plot_title_label = Label(
            plot_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Plot title:",
        )
        plot_title_label.pack(padx=self.tk_format.padx, pady=(15, 5))
        self.plot_title_entry = Entry(
            plot_frame,
            width=50,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.plot_title_entry.insert(0, self.plot_title)
        self.plot_title_entry.pack(pady=(5, 20))
        plot_local_remote_frame = Frame(plot_frame, bg=self.tk_format.bg)
        plot_local_remote_frame.pack()

        plot_input_dir_label = Label(
            plot_local_remote_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Path to .csv file:",
        )
        plot_input_dir_label.pack(side=LEFT, padx=self.tk_format.padx, pady=self.tk_format.pady)

        self.plot_local_check = Checkbutton(
            plot_local_remote_frame,
            fg=self.tk_format.textcolor,
            text=" Local",
            selectcolor=self.tk_format.check_bg,
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            variable=self.plot_local,
            highlightthickness=0,
            highlightbackground=self.tk_format.bg,
            command=self.local_plot_cmd,
        )
        self.plot_local_check.pack(side=LEFT, pady=(5, 5), padx=(5, 5))

        self.plot_remote_check = Checkbutton(
            plot_local_remote_frame,
            fg=self.tk_format.textcolor,
            text=" Remote",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.plot_remote,
            command=self.remote_plot_cmd,
            selectcolor=self.tk_format.check_bg,
        )
        self.plot_remote_check.pack(side=LEFT, pady=(5, 5), padx=(5, 5))

        # controls whether the file being plotted is looked for locally or on the spectrometer computer
        if self.plot_local_remote == "remote":
            self.plot_remote_check.select()
            self.plot_local_check.deselect()
        if self.plot_local_remote == "local":
            self.plot_local_check.select()
            self.plot_remote_check.deselect()

        plot_file_frame = Frame(plot_frame, bg=self.tk_format.bg)
        plot_file_frame.pack(pady=(5, 10))
        plot_file_browse_button = Button(plot_file_frame, text="Browse", command=self.choose_plot_file)
        plot_file_browse_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        plot_file_browse_button.pack(side=RIGHT, padx=self.tk_format.padx)

        self.plot_input_dir_entry = Entry(
            plot_file_frame,
            width=50,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.plot_input_dir_entry.insert(0, self.plot_input_file)
        self.plot_input_dir_entry.pack(side=RIGHT)

        plot_button_frame = Frame(plot_frame, bg=self.tk_format.bg)
        plot_button_frame.pack()

        plot_button = Button(
            plot_button_frame,
            fg=self.tk_format.textcolor,
            text="Plot",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=int(self.tk_format.button_width * 1.3),
            bg="light gray",
            command=self.controller.plot,
        )
        plot_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        plot_button.pack(side=LEFT, pady=(20, 20), padx=(15, 15))

        process_close_button = Button(
            plot_button_frame,
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            text="Close",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=int(self.tk_format.button_width * 1.3),
            bg=self.tk_format.buttonbackgroundcolor,
            command=self.close_plot,
        )
        process_close_button.pack(pady=(20, 20), padx=(15, 15), side=LEFT)

    def close_plot(self) -> None:
        self.plot_top.destroy()

    # Toggle back and forth between plotting your data from a remote or local file
    def local_plot_cmd(self) -> None:
        if self.plot_local.get() and not self.plot_remote.get():
            return
        if self.plot_remote.get() and not self.plot_local.get():
            return
        if not self.plot_remote.get():
            self.plot_remote_check.select()
        else:
            self.plot_remote_check.deselect()

    # Toggle back and forth between plotting your data from a remote or local file
    def remote_plot_cmd(self) -> None:
        if self.plot_local.get() and not self.plot_remote.get():
            return
        if self.plot_remote.get() and not self.plot_local.get():
            return
        if not self.plot_local.get():
            self.plot_local_check.select()
        else:
            self.plot_local_check.deselect()

    def choose_plot_file(self) -> None:
        init_file = self.plot_input_dir_entry.get()
        relative_file = init_file.split("/")[-1].split("\\")[-1]
        init_dir = init_file.strip(relative_file)
        if self.plot_remote.get():
            RemoteFileExplorer(
                self,
                target=self.plot_input_dir_entry,
                title="Select a file",
                label="Select a file to plot",
                directories_only=False,
            )
        else:
            if os.path.isdir(init_dir):
                file = askopenfilename(initialdir=init_dir, title="Select a file to plot")
            else:
                file = askopenfilename(initialdir=os.getcwd(), title="Select a file to plot")
            if file != ():
                self.plot_input_dir_entry.delete(0, "end")
                self.plot_input_dir_entry.insert(0, file)
        self.plot_top.lift()

    def plot(self) -> None:
        plot_input_file = self.plot_input_dir_entry.get()
        plot_title = self.plot_title_entry.get()
        if self.plot_remote.get():
            self.plot_local_remote = "remote"
        elif self.plot_local.get():
            self.plot_local_remote = "local"

        try:
            with open(self.config_info.local_config_loc + "plot_config.txt", "w") as plot_config:
                plot_config.write(self.plot_local_remote + "\n")
                plot_config.write(plot_input_file + "\n")
                plot_config.write(plot_title + "\n")
        except OSError:
            print("Error saving data location for plots.")

        self.plot_top.destroy()
        try:
            if self.plot_local_remote == "remote":
                self.plotter.plot_spectra(plot_title, plot_input_file)
                self.plotter.tabs[-1].ask_which_samples()
            else:
                self.plotter.plot_spectra(plot_title, plot_input_file)
                self.plotter.tabs[-1].ask_which_samples()

            self.controller.goniometer_view.flip()

            last = len(self.controller.view_notebook.tabs()) - 1

            self.controller.view_notebook.select(last)
            if (
                self.plotter.save_dir is None
            ):  # If the user hasn't specified a folder where they want to save plots yet, set the default folder to be
                # the same one they got the data from. Otherwise, leave it as is.
                if self.config_info.opsys == "Windows":
                    self.plotter.save_dir = "\\".join(plot_input_file.split("\\")[0:-1])
                else:
                    self.plotter.save_dir = "/".join(plot_input_file.split("/")[0:-1])

        except Exception as e:
            #TODO: figure out options for exceptions.
            print(e)
            Dialog(
                self.controller,
                "Plotting Error",
                "Error: Plotting failed.\n\nDoes file exist? Is data formatted correctly?\nIf plotting a remote file,"
                " is the server accessible?",
                {"ok": {}},
            )
            raise e

        # if self.config_info.opsys == "Windows" or self.plot_remote.get():
        #     filename = filename.replace("\\", "/")
        #
        # if self.plot_remote.get():
        #     self.controller.plot_remote()
        #
        # else:
        #     if os.path.exists(filename):
        #         self.plot(filename)
        #     else:
        #         ErrorDialog(
        #             self,
        #             title="Error: File not found",
        #             label="Error: File not found.\n\n" + filename + "\n\ndoes not exist.",
        #         )
