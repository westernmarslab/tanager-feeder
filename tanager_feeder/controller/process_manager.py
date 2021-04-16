import os
import time
from tkinter import RIGHT, LEFT, Entry, Button, Label, Checkbutton, Toplevel, Frame, StringVar, IntVar, INSERT
from tkinter.filedialog import askdirectory
from typing import Tuple, Any

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.remote_file_explorer import RemoteFileExplorer
from tanager_feeder import utils


class ProcessManager:
    def __init__(self, controller: utils.ControllerType):
        # The commander is in charge of sending all the commands for the spec compy to read
        # If the user has saved spectra with this program before, load in their previously used directories.
        self.controller = controller
        self.config_info = controller.config_info
        self.remote_directory_worker = controller.remote_directory_worker

        self.tk_format = utils.TkFormat(self.controller.config_info)

        self.process_input_dir = ""
        self.process_output_dir = ""
        # TODO: saving a spectrum should result in that directory being set
        #  as the process directory next time the program opens.
        try:
            with open(self.config_info.local_config_loc + "process_directories.txt", "r") as process_config:
                self.proc_local_remote = process_config.readline().strip("\n")
                self.process_input_dir = process_config.readline().strip("\n")
                self.process_output_dir = process_config.readline().strip("\n")

        except OSError:
            with open(self.config_info.local_config_loc + "process_directories.txt", "w+") as f:
                f.write("remote")
                f.write("C:\\Users\n")
                f.write("C:\\Users\n")
                self.proc_local_remote = "remote"
                self.proc_input_dir = "C:\\Users"
                self.proc_output_dir = "C:\\Users"

        self.proc_remote = IntVar()
        self.proc_local = IntVar()
        if self.proc_local_remote == "remote":
            self.proc_remote.set(1)
            self.proc_local.set(0)
        else:
            self.proc_local.set(1)
            self.proc_remote.set(0)

        self.process_save_dir = IntVar()
        self.input_dir_var = StringVar()
        self.process_top = None
        self.input_dir_entry = None
        self.proc_local_check = None
        self.proc_remote_check = None
        self.output_dir_entry = None
        self.output_file_entry = None
        self.process_save_dir_check = None

    def show(self) -> None:
        self.process_top = Toplevel(self.controller.master)
        self.process_top.wm_title("Process Data")
        process_frame = Frame(self.process_top, bg=self.tk_format.bg, pady=15, padx=15)
        process_frame.pack()

        input_dir_label = Label(
            process_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Raw spectral data input directory:",
        )
        input_dir_label.pack(padx=self.tk_format.padx, pady=(10, 5))

        input_frame = Frame(process_frame, bg=self.tk_format.bg)
        input_frame.pack()

        process_input_browse_button = Button(input_frame, text="Browse", command=self.choose_process_input_dir)
        process_input_browse_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        process_input_browse_button.pack(side=RIGHT, padx=self.tk_format.padx)

        self.input_dir_var.trace("w", self.validate_input_dir)

        self.input_dir_entry = Entry(
            input_frame,
            width=50,
            bd=self.tk_format.bd,
            textvariable=self.input_dir_var,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        if len(self.input_dir_entry.get()) == 0:
            self.input_dir_entry.insert(0, self.process_input_dir)
        self.input_dir_entry.pack(side=RIGHT, padx=self.tk_format.padx, pady=self.tk_format.pady)

        proc_local_remote_frame = Frame(process_frame, bg=self.tk_format.bg)
        proc_local_remote_frame.pack()

        output_dir_label = Label(
            proc_local_remote_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Processed data output directory:",
        )
        output_dir_label.pack(padx=self.tk_format.padx, pady=(10, 5), side=LEFT)

        self.proc_local_check = Checkbutton(
            proc_local_remote_frame,
            fg=self.tk_format.textcolor,
            text=" Local",
            selectcolor=self.tk_format.check_bg,
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            variable=self.proc_local,
            highlightthickness=0,
            highlightbackground=self.tk_format.bg,
            command=self.local_process_cmd,
        )
        self.proc_local_check.pack(side=LEFT, pady=(5, 0), padx=(5, 5))
        if self.proc_local_remote == "local":
            self.proc_local_check.select()

        self.proc_remote_check = Checkbutton(
            proc_local_remote_frame,
            fg=self.tk_format.textcolor,
            text=" Remote",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.proc_remote,
            command=self.remote_process_cmd,
            selectcolor=self.tk_format.check_bg,
        )
        self.proc_remote_check.pack(side=LEFT, pady=(5, 0), padx=(5, 5))
        if self.proc_local_remote == "remote":
            self.proc_remote_check.select()

        process_output_frame = Frame(process_frame, bg=self.tk_format.bg)
        process_output_frame.pack(pady=(5, 10))
        process_output_browse_button = Button(
            process_output_frame, text="Browse", command=self.choose_process_output_dir
        )
        process_output_browse_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        process_output_browse_button.pack(side=RIGHT, padx=self.tk_format.padx)

        self.output_dir_entry = Entry(
            process_output_frame,
            width=50,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.output_dir_entry.insert(0, self.process_output_dir)
        self.output_dir_entry.pack(side=RIGHT, padx=self.tk_format.padx, pady=self.tk_format.pady)

        output_file_label = Label(
            process_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Output file name:",
        )
        output_file_label.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)
        self.output_file_entry = Entry(
            process_frame,
            width=50,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.output_file_entry.pack()

        process_check_frame = Frame(process_frame, bg=self.tk_format.bg)
        process_check_frame.pack(pady=(15, 5))

        self.process_save_dir_check = Checkbutton(
            process_check_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text="Save file configuration",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.process_save_dir,
        )
        self.process_save_dir_check.select()

        process_button_frame = Frame(process_frame, bg=self.tk_format.bg)
        process_button_frame.pack()
        process_button = Button(
            process_button_frame,
            fg=self.tk_format.textcolor,
            text="Process",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=int(self.tk_format.button_width * 1.3),
            bg="light gray",
            command=self.controller.process_cmd,
        )
        process_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        process_button.pack(padx=(15, 15), side=LEFT)

        process_close_button = Button(
            process_button_frame,
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            text="Close",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=int(self.tk_format.button_width * 1.3),
            bg=self.tk_format.buttonbackgroundcolor,
            command=self.close_process,
        )
        process_close_button.pack(padx=(15, 15), side=LEFT)

    # Closes process frame
    def close_process(self) -> None:
        self.process_top.destroy()

    # Toggle back and forth between saving your processed data remotely or locally
    def local_process_cmd(self) -> None:
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
    def remote_process_cmd(self) -> None:
        if self.proc_local.get() and not self.proc_remote.get():
            return
        if self.proc_remote.get() and not self.proc_local.get():
            return
        if not self.proc_local.get():
            self.proc_local_check.select()
        else:
            self.proc_local_check.deselect()
            self.proc_local_remote = "remote"
            self.output_dir_entry.delete(0, "end")

    def choose_process_output_dir(self) -> None:
        init_dir: str = self.output_dir_entry.get()
        if self.proc_remote.get():
            RemoteFileExplorer(
                self.controller,
                target=self.output_dir_entry,
                title="Select a directory",
                label="Select an output directory for processed data.",
                directories_only=True,
            )
        else:
            self.process_top.lift()
            if os.path.isdir(init_dir):
                output_dir = askdirectory(initialdir=init_dir, title="Select an output directory")
            else:
                output_dir = askdirectory(initialdir=os.getcwd(), title="Select an output directory")
            if output_dir != ():
                self.output_dir_entry.delete(0, "end")
                self.output_dir_entry.insert(0, output_dir)
        self.process_top.lift()

    def setup_process(self) -> Tuple[str, str, str]:
        output_file: str = self.output_file_entry.get()

        if output_file == "":
            ErrorDialog(self.controller, label="Error: Enter an output file name")
            raise ProcessFileError

        if output_file[-4:] != ".csv":
            output_file = output_file + ".csv"
            self.output_file_entry.insert("end", ".csv")

        input_directory = self.input_dir_entry.get()
        if input_directory[-1] == "\\":
            input_directory = input_directory[:-1]

        output_directory = self.output_dir_entry.get()

        if self.process_save_dir.get():
            file = open(self.config_info.local_config_loc + "process_directories.txt", "w+")
            file.write(self.proc_local_remote + "\n")
            file.write(input_directory + "\n")
            file.write(output_directory + "\n")
            file.write(output_file + "\n")
            file.close()

        if self.proc_local.get() == 1:
            self.controller.plot_manager.plot_local_remote = "local"
            check = self.check_local_file(self.output_dir_entry.get(), output_file, self.controller.process_cmd)
            if not check:
                raise ProcessFileError  # If the file exists, controller.check_local_file_exists
                # gives the user the option to overwrite, in which case process_cmd gets called again.
            check = self.check_local_folder(output_directory, self.controller.process_cmd)
            if not check:
                raise ProcessFileError  # Same deal for the folder (except existing is good).
            self.controller.plot_manager.plot_local_remote = "local"
            return input_directory, output_directory, output_file
        if self.proc_local.get() == 0:
            check = self.check_remote_folder(output_directory, self.controller.process_cmd)
            if not check:
                raise ProcessFileError
            self.controller.plot_manager.plot_local_remote = "remote"

        return input_directory, output_directory, output_file

    def finish_processing(self) -> Tuple[str, str]:
        return
        # #TODO: final_data_destination seems to just become log base?
        # final_data_destination: str = self.output_file_entry.get()
        # if "." not in final_data_destination:
        #     final_data_destination = final_data_destination + ".csv"
        # data_base: str = ".".join(final_data_destination.split(".")[0:-1])
        #
        # if self.config_info.opsys in ("Linux", "Mac"):
        #     final_data_destination: str = self.output_dir_entry.get() + "/" + final_data_destination
        #     log_base: str = self.output_dir_entry.get() + "/" + data_base + "_log"
        # else:
        #     final_data_destination: str = self.output_dir_entry.get() + "\\" + final_data_destination
        #     log_base: str = self.output_dir_entry.get() + "\\" + data_base + "_log"
        #
        # final_log_destination: str = log_base
        # i = 1
        # while os.path.isfile(final_log_destination + ".txt"):
        #     final_log_destination = log_base + "_" + str(i)
        #     i += 1
        # final_log_destination += ".txt"
        #
        # return final_data_destination, final_log_destination

    def check_local_file(self, directory: str, local_file: str, next_action: Any) -> bool:
        def remove_retry(file, action):
            try:
                os.remove(file)
                action()
            except OSError:
                ErrorDialog(
                    self.controller, title="Error overwriting file", label="Error: Could not delete file.\n\n" + file
                )

        if self.config_info.opsys in ("Linux", "Mac"):
            if directory[-1] != "/":
                directory += "/"
        else:
            if directory[-1] != "\\":
                directory += "\\"

        full_process_output_path = directory + local_file
        if os.path.exists(full_process_output_path):
            buttons = {"yes": {remove_retry: [full_process_output_path, next_action]}, "no": {}}
            dialog = Dialog(
                self.controller,
                title="Error: File Exists",
                label="Error: Specified output file already exists.\n\n"
                + full_process_output_path
                + "\n\nDo you want to overwrite this data?",
                buttons=buttons,
            )
            width = len(full_process_output_path) * 5 + 100
            dialog.top.wm_geometry(f"{width}x160")
            return False
        return True

    def check_local_folder(self, local_dir: str, next_action: Any) -> bool:
        def try_mk_dir(dir_to_make: str, action: Any) -> None:
            try:
                os.makedirs(dir_to_make)
                action()
            except OSError:
                ErrorDialog(
                    self.controller, title="Cannot create directory", label="Cannot create directory:\n\n" + dir_to_make
                )

        exists = os.path.exists(local_dir)
        if exists:
            # If the file exists, try creating and deleting a new file there to make sure we have permission.
            try:
                if self.config_info.opsys in ("Linux", "Mac"):
                    if local_dir[-1] != "/":
                        local_dir += "/"
                else:
                    if local_dir[-1] != "\\":
                        local_dir += "\\"

                existing = os.listdir(local_dir)
                i = 0
                delme = "delme" + str(i)
                while delme in existing:
                    i += 1
                    delme = "delme" + str(i)

                os.mkdir(local_dir + delme)
                os.rmdir(local_dir + delme)
                return True

            except OSError:
                ErrorDialog(
                    self.controller,
                    title="Error: Cannot write",
                    label="Error: Cannot write to specified directory.\n\n" + local_dir,
                )
                return False
        else:
            if (
                self.controller.script_running
            ):  # If we're running a script, just try making the directory automatically.
                try_mk_dir(local_dir, next_action)
            else:  # Otherwise, ask the user.
                buttons = {"yes": {try_mk_dir: [local_dir, next_action]}, "no": {}}
                ErrorDialog(
                    self.controller,
                    title="Directory does not exist",
                    label=local_dir + "\n\ndoes not exist. Do you want to create this directory?",
                    buttons=buttons,
                )
        # TODO: check these return statements make sense.
        return exists

    # Checks if the given directory exists and is writeable. If not writeable, gives user option to create.
    def check_remote_folder(self, remote_dir: str, next_action: Any) -> bool:
        print(remote_dir)

        def inner_mkdir(dir_to_make: str, action: Any):
            mkdir_status = self.remote_directory_worker.mkdir(dir_to_make)
            print("MKDIR STATUS!!")
            print(mkdir_status)
            if mkdir_status == "mkdirsuccess":
                action()
            elif mkdir_status == "mkdirfailedfileexists":
                ErrorDialog(
                    self.controller,
                    title="Error",
                    label="Could not create directory:\n\n" + dir_to_make + "\n\nFile exists.",
                )
            elif mkdir_status == "mkdirfailedpermission":
                ErrorDialog(
                    self.controller,
                    title="Error",
                    label="Could not create directory:\n\n" + dir_to_make + "\n\nPermission denied.",
                )
            elif "mkdirfailed" in mkdir_status:
                ErrorDialog(self.controller, title="Error", label="Could not create directory:\n\n" + dir_to_make)

        status = self.remote_directory_worker.get_dirs(remote_dir)

        if status == "listdirfailed":
            buttons = {"yes": {inner_mkdir: [remote_dir, next_action]}, "no": {}}
            ErrorDialog(
                self.controller,
                title="Directory does not exist",
                label=remote_dir + "\ndoes not exist. Do you want to create this directory?",
                buttons=buttons,
            )
            return False
        if status == "listdirfailedpermission":
            ErrorDialog(self.controller, label="Error: Permission denied for\n" + remote_dir)
            return False

        if status == "timeout":
            if not self.controller.text_only:
                buttons = {
                    "cancel": {},
                    "retry": {
                        self.controller.spec_commander.remove_from_listener_queue: [["timeout"]],
                        self.controller.next_in_queue: [],
                    },
                }
                dialog = ErrorDialog(
                    self.controller,
                    label="Error: Operation timed out.\n\nCheck that the automation script is running on the"
                    " spectrometer\n computer and the spectrometer is connected.",
                    buttons=buttons,
                )
                for button in dialog.tk_buttons:
                    button.config(width=15)
            else:
                self.controller.log("Error: Operation timed out.")
            return False

        self.controller.spec_commander.check_writeable(remote_dir)
        t = 3 * utils.BUFFER
        while t > 0:
            if "yeswriteable" in self.controller.spec_listener.queue:
                self.controller.spec_listener.queue.remove("yeswriteable")
                return True
            if "notwriteable" in self.controller.spec_listener.queue:
                self.controller.spec_listener.queue.remove("notwriteable")
                ErrorDialog(self.controller, label="Error: Permission denied.\nCannot write to specified directory.")
                return False
            time.sleep(utils.INTERVAL)
            t = t - utils.INTERVAL
        if t <= 0:
            ErrorDialog(self.controller, label="Error: Operation timed out.")
            return False

    def choose_process_input_dir(self) -> None:
        RemoteFileExplorer(
            self.controller,
            label="Select the directory containing the data you want to process.\nThis must be on a drive mounted on"
            " the spectrometer control computer.\n E.g. R:\\RiceData\\MarsGroup\\YourName\\spectral_data",
            target=self.input_dir_entry,
        )

    def validate_input_dir(self, *args) -> None:
        # TODO: understand mystery args.
        print(args)
        pos = self.input_dir_entry.index(INSERT)
        input_dir = utils.rm_reserved_chars(self.input_dir_entry.get())
        if len(input_dir) < len(self.input_dir_entry.get()):
            pos = pos - 1
        self.input_dir_entry.delete(0, "end")
        self.input_dir_entry.insert(0, input_dir)
        self.input_dir_entry.icursor(pos)


class ProcessFileError(Exception):
    def __init__(self, message="File error while processing."):
        super().__init__(self, message)
