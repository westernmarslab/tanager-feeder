from tkinter import RIGHT, LEFT, Entry, Button, Label, Checkbutton, Toplevel, Frame, StringVar, IntVar

from tanager_feeder.dialogs.error_dialog import ErrorDialog

class ProcessManager():
    def __init__(self, controller):
        self.process_top = Toplevel(controller.master)
        self.process_top.wm_title("Process Data")
        self.process_frame = Frame(self.process_top, bg=self.bg, pady=15, padx=15)
        self.process_frame.pack()

        self.input_dir_label = Label(
            self.process_frame,
            padx=self.padx,
            pady=self.pady,
            bg=self.bg,
            fg=self.textcolor,
            text="Raw spectral data input directory:",
        )
        self.input_dir_label.pack(padx=self.padx, pady=(10, 5))

        self.input_frame = Frame(self.process_frame, bg=self.bg)
        self.input_frame.pack()

        self.process_input_browse_button = Button(
            self.input_frame, text="Browse", command=self.choose_process_input_dir
        )
        self.process_input_browse_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.process_input_browse_button.pack(side=RIGHT, padx=self.padx)
        self.tk_buttons.append(self.process_input_browse_button)

        self.input_dir_var = StringVar()
        self.input_dir_var.trace("w", self.validate_input_dir)

        self.input_dir_entry = Entry(
            self.input_frame,
            width=50,
            bd=self.bd,
            textvariable=self.input_dir_var,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.input_dir_entry.insert(0, self.process_input_dir)
        self.input_dir_entry.pack(side=RIGHT, padx=self.padx, pady=self.pady)
        self.entries.append(self.input_dir_entry)

        self.proc_local_remote_frame = Frame(self.process_frame, bg=self.bg)
        self.proc_local_remote_frame.pack()

        self.output_dir_label = Label(
            self.proc_local_remote_frame,
            padx=self.padx,
            pady=self.pady,
            bg=self.bg,
            fg=self.textcolor,
            text="Processed data output directory:",
        )
        self.output_dir_label.pack(padx=self.padx, pady=(10, 5), side=LEFT)

        self.proc_local_check = Checkbutton(
            self.proc_local_remote_frame,
            fg=self.textcolor,
            text=" Local",
            selectcolor=self.check_bg,
            bg=self.bg,
            pady=self.pady,
            variable=self.proc_local,
            highlightthickness=0,
            highlightbackground=self.bg,
            command=self.local_process_cmd,
        )
        self.proc_local_check.pack(side=LEFT, pady=(5, 0), padx=(5, 5))
        if self.proc_local_remote == "local":
            self.proc_local_check.select()
        self.tk_check_buttons.append(self.proc_local_check)

        self.proc_remote_check = Checkbutton(
            self.proc_local_remote_frame,
            fg=self.textcolor,
            text=" Remote",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.proc_remote,
            command=self.remote_process_cmd,
            selectcolor=self.check_bg,
        )
        self.proc_remote_check.pack(side=LEFT, pady=(5, 0), padx=(5, 5))
        if self.proc_local_remote == "remote":
            self.proc_remote_check.select()
        self.tk_check_buttons.append(self.proc_remote_check)

        self.process_output_frame = Frame(self.process_frame, bg=self.bg)
        self.process_output_frame.pack(pady=(5, 10))
        self.process_output_browse_button = Button(
            self.process_output_frame, text="Browse", command=self.choose_process_output_dir
        )
        self.process_output_browse_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.process_output_browse_button.pack(side=RIGHT, padx=self.padx)
        self.tk_buttons.append(self.process_output_browse_button)

        self.output_dir_entry = Entry(
            self.process_output_frame,
            width=50,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.output_dir_entry.insert(0, self.process_output_dir)
        self.output_dir_entry.pack(side=RIGHT, padx=self.padx, pady=self.pady)
        self.entries.append(self.output_dir_entry)

        self.output_file_label = Label(
            self.process_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="Output file name:"
        )
        self.output_file_label.pack(padx=self.padx, pady=self.pady)
        self.output_file_entry = Entry(
            self.process_frame,
            width=50,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.output_file_entry.pack()
        self.entries.append(self.output_file_entry)

        self.process_check_frame = Frame(self.process_frame, bg=self.bg)
        self.process_check_frame.pack(pady=(15, 5))
        self.process_save_dir = IntVar()
        self.process_save_dir_check = Checkbutton(
            self.process_check_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text="Save file configuration",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.process_save_dir,
        )
        self.process_save_dir_check.select()

        self.process_button_frame = Frame(self.process_frame, bg=self.bg)
        self.process_button_frame.pack()
        self.process_button = Button(
            self.process_button_frame,
            fg=self.textcolor,
            text="Process",
            padx=self.padx,
            pady=self.pady,
            width=int(self.button_width * 1.3),
            bg="light gray",
            command=self.process_cmd,
        )
        self.process_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.process_button.pack(padx=(15, 15), side=LEFT)
        self.tk_buttons.append(self.process_button)

        self.process_close_button = Button(
            self.process_button_frame,
            fg=self.buttontextcolor,
            highlightbackground=self.highlightbackgroundcolor,
            text="Close",
            padx=self.padx,
            pady=self.pady,
            width=int(self.button_width * 1.3),
            bg=self.buttonbackgroundcolor,
            command=self.close_process,
        )
        self.process_close_button.pack(padx=(15, 15), side=LEFT)
        self.tk_buttons.append(self.process_close_button)

    # Closes process frame
    def close_process(self):
        self.process_top.destroy()

    # Toggle back and forth between saving your processed data remotely or locally
    def local_process_cmd(self):
        if self.proc_local.get() and not self.proc_remote.get():
            return
        if self.proc_remote.get() and not self.proc_local.get():
            return
        if not self.proc_remote.get():
            self.proc_remote_check.select()
        else:
            self.proc_remote_check.deselect()
            self.proc_local_remote = "local"
            self.output_dir_entry.delete(0, "end")

    # Toggle back and forth between saving your processed data remotely or locally
    def remote_process_cmd(self):
        if self.proc_local.get() and not self.proc_remote.get():
            return
        elif self.proc_remote.get() and not self.proc_local.get():
            return
        elif not self.proc_local.get():
            self.proc_local_check.select()

        else:
            self.proc_local_check.deselect()
            self.proc_local_remote = "remote"
            self.output_dir_entry.delete(0, "end")

    def choose_process_output_dir(self):
        init_dir = self.output_dir_entry.get()
        if self.proc_remote.get():
            RemoteFileExplorer(
                self,
                target=self.output_dir_entry,
                title="Select a directory",
                label="Select an output directory for processed data.",
                directories_only=True,
            )
        else:
            self.process_top.lift()
            if os.path.isdir(init_dir):
                dir = askdirectory(initialdir=init_dir, title="Select an output directory")
            else:
                dir = askdirectory(initialdir=os.getcwd(), title="Select an output directory")
            if dir != ():
                self.output_dir_entry.delete(0, "end")
                self.output_dir_entry.insert(0, dir)
        self.process_top.lift()

    def setup_process(self):

        output_file = self.output_file_entry.get()

        if output_file == "":
            ErrorDialog(self, label="Error: Enter an output file name")
            raise ProcessFileError

        if output_file[-4:] != ".csv":
            output_file = output_file + ".csv"
            self.output_file_entry.insert("end", ".csv")

        input_directory = self.input_dir_entry.get()
        if input_directory[-1] == "\\":
            input_directory = input_directory[:-1]

        if self.process_save_dir.get():
            file = open(self.local_config_loc + "process_directories.txt", "w")
            file.write(self.plot_local_remote + "\n")
            file.write(self.input_dir_entry.get() + "\n")
            file.write(self.output_dir_entry.get() + "\n")
            file.write(output_file + "\n")
            file.close()

        if self.proc_local.get() == 1:
            self.plot_local_remote = "local"
            check = self.check_local_file(self.output_dir_entry.get(), output_file, self.process_cmd)
            if not check:
                raise ProcessFileError  # If the file exists, controller.check_local_file_exists gives the user the option to overwrite,
                # in which case process_cmd gets called again.
            check = self.check_local_folder(self.output_dir_entry.get(), self.process_cmd)
            if not check:
                raise ProcessFileError  # Same deal for the folder (except existing is good).

            #TODO: Figure out temp loc for remote data
            return input_directory, "temp loc", "proc_temp.csv"

        else:
            self.plot_local_remote = "remote"
            output_directory = self.output_dir_entry.get()
            check = self.check_remote_folder(output_directory, self.process_cmd)
            if not check:
                raise ProcessFileError
            #TODO: Figure out temp loc for remote data
            return input_directory, output_directory, output_file

    def finish_processing(self):
        final_data_destination = self.output_file_entry.get()
        if "." not in final_data_destination:
            final_data_destination = final_data_destination + ".csv"
        data_base = ".".join(final_data_destination.split(".")[0:-1])

        if self.opsys == "Linux" or self.opsys == "Mac":
            final_data_destination = self.output_dir_entry.get() + "/" + final_data_destination
            log_base = self.output_dir_entry.get() + "/" + data_base + "_log"
        else:
            final_data_destination = self.output_dir_entry.get() + "\\" + final_data_destination
            log_base = self.output_dir_entry.get() + "\\" + data_base + "_log"

        final_log_destination = log_base
        i = 1
        while os.path.isfile(final_log_destination + ".txt"):
            final_log_destination = log_base + "_" + str(i)
            i += 1
        final_log_destination += ".txt"

        return final_data_destination, final_log_destination

