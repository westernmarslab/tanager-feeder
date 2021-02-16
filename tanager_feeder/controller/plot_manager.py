import os
from tkinter import Entry, Button, Label, Checkbutton, Toplevel, Frame, LEFT, RIGHT
from tkinter.filedialog import askopenfilename


class PlotManager():
    def __init__(self, master):
        self.plot_top = Toplevel(master)
        self.plot_top.wm_title("Plot")
        self.plot_frame = Frame(self.plot_top, bg=self.bg, pady=2 * self.pady, padx=15)
        self.plot_frame.pack()

        self.plot_title_label = Label(
            self.plot_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="Plot title:"
        )
        self.plot_title_label.pack(padx=self.padx, pady=(15, 5))
        self.plot_title_entry = Entry(
            self.plot_frame,
            width=50,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.plot_title_entry.insert(0, self.plot_title)
        self.plot_title_entry.pack(pady=(5, 20))
        self.plot_local_remote_frame = Frame(self.plot_frame, bg=self.bg)
        self.plot_local_remote_frame.pack()

        self.plot_input_dir_label = Label(
            self.plot_local_remote_frame,
            padx=self.padx,
            pady=self.pady,
            bg=self.bg,
            fg=self.textcolor,
            text="Path to .csv file:",
        )
        self.plot_input_dir_label.pack(side=LEFT, padx=self.padx, pady=self.pady)

        self.plot_local_check = Checkbutton(
            self.plot_local_remote_frame,
            fg=self.textcolor,
            text=" Local",
            selectcolor=self.check_bg,
            bg=self.bg,
            pady=self.pady,
            variable=self.plot_local,
            highlightthickness=0,
            highlightbackground=self.bg,
            command=self.local_plot_cmd,
        )
        self.plot_local_check.pack(side=LEFT, pady=(5, 5), padx=(5, 5))

        self.plot_remote_check = Checkbutton(
            self.plot_local_remote_frame,
            fg=self.textcolor,
            text=" Remote",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.plot_remote,
            command=self.remote_plot_cmd,
            selectcolor=self.check_bg,
        )
        self.plot_remote_check.pack(side=LEFT, pady=(5, 5), padx=(5, 5))

        # controls whether the file being plotted is looked for locally or on the spectrometer computer
        if self.plot_local_remote == "remote":
            self.plot_remote_check.select()
            self.plot_local_check.deselect()
        if self.plot_local_remote == "local":
            self.plot_local_check.select()
            self.plot_remote_check.deselect()

        self.plot_file_frame = Frame(self.plot_frame, bg=self.bg)
        self.plot_file_frame.pack(pady=(5, 10))
        self.plot_file_browse_button = Button(self.plot_file_frame, text="Browse", command=self.choose_plot_file)
        self.plot_file_browse_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.plot_file_browse_button.pack(side=RIGHT, padx=self.padx)

        self.plot_input_dir_entry = Entry(
            self.plot_file_frame,
            width=50,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.plot_input_dir_entry.insert(0, self.plot_input_file)
        self.plot_input_dir_entry.pack(side=RIGHT)

        self.plot_button_frame = Frame(self.plot_frame, bg=self.bg)
        self.plot_button_frame.pack()

        self.plot_button = Button(
            self.plot_button_frame,
            fg=self.textcolor,
            text="Plot",
            padx=self.padx,
            pady=self.pady,
            width=int(self.button_width * 1.3),
            bg="light gray",
            command=self.plot,
        )
        self.plot_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.plot_button.pack(side=LEFT, pady=(20, 20), padx=(15, 15))

        self.process_close_button = Button(
            self.plot_button_frame,
            fg=self.buttontextcolor,
            highlightbackground=self.highlightbackgroundcolor,
            text="Close",
            padx=self.padx,
            pady=self.pady,
            width=int(self.button_width * 1.3),
            bg=self.buttonbackgroundcolor,
            command=self.close_plot,
        )
        self.process_close_button.pack(pady=(20, 20), padx=(15, 15), side=LEFT)


    def close_plot(self):
        self.plot_top.destroy()

    # Toggle back and forth between plotting your data from a remote or local file
    def local_plot_cmd(self):
        if self.plot_local.get() and not self.plot_remote.get():
            return
        elif self.plot_remote.get() and not self.plot_local.get():
            return
        elif not self.plot_remote.get():
            self.plot_remote_check.select()
        else:
            self.plot_remote_check.deselect()

    # Toggle back and forth between plotting your data from a remote or local file
    def remote_plot_cmd(self):
        if self.plot_local.get() and not self.plot_remote.get():
            return
        elif self.plot_remote.get() and not self.plot_local.get():
            return
        elif not self.plot_local.get():
            self.plot_local_check.select()
        else:
            self.plot_local_check.deselect()

    def choose_plot_file(self):
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


    def plot(self, filename):
        if len(self.queue) > 0:
            print("There is a queue here if and only if we are transferring data from a remote location.")
            self.complete_queue_item()
        title = self.plot_title_entry.get()
        caption = ""  # self.plot_caption_entry.get()

        try:
            self.plot_input_file = self.plot_input_dir_entry.get()
            self.plot_title = self.plot_title_entry.get()
            if self.plot_remote.get():
                self.plot_local_remote = "remote"
            elif self.plot_local.get():
                self.plot_local_remote = "local"

            with open(self.local_config_loc + "plot_config.txt", "w") as plot_config:
                plot_config.write(self.plot_local_remote + "\n")
                plot_config.write(self.plot_input_file + "\n")
                plot_config.write(self.plot_title + "\n")

            self.plot_top.destroy()

            if self.plotter.controller.plot_local_remote == "remote":
                self.plotter.plot_spectra(title, filename, caption, exclude_wr=False, draw=False)
                self.plotter.tabs[-1].ask_which_samples()
            else:
                self.plotter.plot_spectra(title, filename, caption, exclude_wr=False, draw=True)
                self.plotter.tabs[-1].ask_which_samples()

            self.goniometer_view.flip()

            last = len(self.view_notebook.tabs()) - 1

            self.view_notebook.select(last)
            if (
                self.plotter.save_dir is None
            ):  # If the user hasn't specified a folder where they want to save plots yet, set the default folder to be
                # the same one they got the data from. Otherwise, leave it as is.
                if self.opsys == "Windows":
                    self.plotter.save_dir = "\\".join(filename.split("\\")[0:-1])
                else:
                    self.plotter.save_dir = "/".join(filename.split("/")[0:-1])

        except Exception as e:
            print(e)

            Dialog(
                self,
                "Plotting Error",
                "Error: Plotting failed.\n\nDoes file exist? Is data formatted correctly?\nIf plotting a remote file,"
                " is the server accessible?",
                {"ok": {}},
            )
            raise e