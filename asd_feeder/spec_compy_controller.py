import datetime
import shutil
import traceback
import os
import time
from threading import Thread

from tanager_tcp import TanagerClient, TanagerServer

from asd_feeder.asd_controls import RS3Controller, ViewSpecProController
from asd_feeder.logger import Logger
from asd_feeder.spectralon_corrector import SpectralonCorrector


class SpecCompyController:
    def __init__(self, temp_data_loc: str, spectralon_data_loc: str, RS3_loc: str, ViewSpecPro_loc: str, computer: str):
        self.computer = computer
        self.temp_data_loc = temp_data_loc
        self.corrector = SpectralonCorrector(spectralon_data_loc)

        print("Starting ASD Feeder...\n")
        print("Starting TCP server")
        self.local_server = TanagerServer(12345, wait_for_network=True)
        thread = Thread(target=self.local_server.listen)
        thread.start()
        self.client = TanagerClient(self.local_server.remote_server_address, 12345)

        print("Initializing ASD connections...")
        self.spec_controller = RS3Controller(temp_data_loc, RS3_loc)
        self.process_controller = ViewSpecProController(temp_data_loc, ViewSpecPro_loc)
        print("Done\n")

        self.logger = Logger()
        self.control_server_address = None  # Will be set when a control computer sends a message with its ip_address and the port it's listening on

    def listen(self):

        self.data_files_to_ignore = []
        print_connection_announcement = None

        while True:
            # check connectivity with spectrometer
            connected = self.spec_controller.check_connectivity()
            if not connected:
                try:
                    if (
                        print_connection_announcement is None or print_connection_announcement == False
                    ):  # If this is the first time we've realized we aren't connected. It will be None the first time through the loop and True or False afterward.
                        print("Waiting for RS³ to connect to the spectrometer...")
                        print_connection_announcement = (
                            True  # Use this to know to print an announcement if the spectrometer reconnects next time.
                        )

                    if self.client.server_address is not None:
                        self.send("lostconnection", [])

                except:
                    pass
                time.sleep(1)
            if (
                connected and print_connection_announcement == True
            ):  # If we weren't connected before, let everyone know we are now!
                print_connection_announcement = False
                print("RS³ connected to the spectrometer. Listening!")

            # check for unexpected files in data directory
            file = self.check_for_unexpected(
                self.spec_controller.save_dir, self.spec_controller.hopefully_saved_files, self.data_files_to_ignore
            )
            while file is not None:
                self.data_files_to_ignore.append(file)
                self.send("unexpectedfile", [file])
                file = self.check_for_unexpected(
                    self.spec_controller.save_dir, self.spec_controller.hopefully_saved_files, self.data_files_to_ignore
                )

            # check for new commands in the tcp server queue
            while len(self.local_server.queue) > 0:
                if self.local_server.remote_server_address != self.client.server_address:
                    print("Setting control computer address:")
                    self.client.server_address = self.local_server.remote_server_address
                    print(self.client.server_address)
                message = self.local_server.queue.pop(0)

                cmd, params = self.filename_to_cmd(message)
                if cmd != "test":
                    print("***************")
                    print("Command received: " + cmd)

                if cmd == "restartcomputer":
                    self.send("restarting", [])
                    os.system("shutdown /r /t 1")

                elif cmd == "restartrs3":
                    self.send("rs3restarted", [])

                elif "checkwriteable" in cmd:  # Check whether you can write to a given directory
                    try:
                        try:
                            os.mkdir(params[0] + "\\autospec_temp")
                        except OSError:
                            pass # This could happen if an autospec temp file was left hanging
                            # (created but not deleted) earlier.
                        os.rmdir(params[0] + "\\autospec_temp")
                        print("sending response to checkwriteable")
                        self.send("yeswriteable", [])
                    except (NotADirectoryError, PermissionError, OSError) as e:
                        self.send("notwriteable", [])

                elif "spectrum" in cmd:  # Take a spectrum

                    if (
                        self.spec_controller.save_dir == ""
                    ):
                        # If there's no save configuration set on this computer, tell the control computer you need
                        # one. This comes up if the script restarts on the spec compy but there is no restart on
                        # the control compy.
                        self.send("noconfig", [])
                        continue
                    if (
                        self.spec_controller.numspectra is None
                    ):  # Same as above, but for instrument configuration (number of spectra to average)
                        self.send("nonumspectra", [])
                        continue

                    # We're going to need to know what filename to expect to be saved so that we can 1) check if the
                    # file exists and warn the user beforehand and 2) confirm whether the spectrum was actually taken.
                    # This filename will be based on a basename and number, both passed from control compy
                    filename = ""
                    if self.computer == "old":  # There are different file formats for old and new RS3 versions.
                        filename = params[0] + "\\" + params[1] + "." + params[2]
                    elif self.computer == "new" or self.computer == "desktop":
                        filename = params[0] + "\\" + params[1] + params[2] + ".asd"

                    label = params[3]
                    i = params[4]
                    e = params[5]
                    az = params[6]

                    # Check if the file already exists. If it does, let the user know. They will have the option
                    # to remove and retry.
                    if os.path.isfile(filename):
                        self.send("savespecfailedfileexists", [])
                        continue

                    # After saving a spectrum, the spec_controller updates its list of expected files to include
                    # one more. Wait for this number to change before moving on.
                    # old=len(spec_controller.hopefully_saved_files)

                    spec_taken = self.spec_controller.take_spectrum(filename)
                    if not spec_taken:
                        self.spec_controller.hopefully_saved_files.pop(-1)
                        self.spec_controller.nextnum = str(int(self.spec_controller.nextnum) - 1)
                        self.send("failedtosavefile", [filename])
                        continue

                    # Now wait for the data file to turn up where it belongs.
                    saved = False
                    t0 = time.perf_counter()
                    t = time.perf_counter()
                    while (
                        t - t0 < int(self.spec_controller.numspectra) * 4 and saved == False
                    ):  # Depending on the number of spectra we are averaging, this might take a while.
                        saved = os.path.isfile(filename)
                        time.sleep(0.2)
                        t = time.perf_counter()

                    if saved:
                        self.logger.log_spectrum(self.spec_controller.numspectra, i, e, az, filename, label)
                        self.send("savedfile", [filename])
                    else:
                        self.spec_controller.hopefully_saved_files.pop(-1)
                        self.spec_controller.nextnum = str(int(self.spec_controller.nextnum) - 1)
                        self.send("failedtosavefile", [filename])

                elif cmd == "saveconfig":
                    self.spec_controller.save_dir = "test"
                    self.spec_controller.basename = "test"
                    self.spec_controller.nextnum = "test"
                    self.spec_controller.numspectra = 20
                    self.send("donelookingforunexpected", [])
                    self.send("saveconfigsuccess", [])
                    continue

                    save_path = params[0]

                    file = self.check_for_unexpected(
                        save_path, self.spec_controller.hopefully_saved_files, self.data_files_to_ignore
                    )
                    found_unexpected = False
                    while file is not None:
                        found_unexpected = True
                        self.data_files_to_ignore.append(file)
                        self.send("unexpectedfile", [file])
                        file = self.check_for_unexpected(
                            save_path, self.spec_controller.hopefully_saved_files, self.data_files_to_ignore
                        )
                    if found_unexpected == True:
                        time.sleep(2)
                    self.send("donelookingforunexpected", [])


                    basename = params[1]
                    startnum = params[2]
                    filename = ""
                    if self.computer == "old":
                        filename = save_path + "\\" + basename + "." + startnum
                    elif self.computer == "new" or self.computer == "desktop":
                        filename = save_path + "\\" + basename + startnum + ".asd"

                    if os.path.isfile(filename):
                        self.send("saveconfigfailedfileexists", [])
                        self.skip_spectrum()
                        continue
                    try:
                        self.spec_controller.spectrum_save(save_path, basename, startnum)
                        if self.spec_controller.failed_to_open:
                            self.spec_controller.failed_to_open = False
                            self.send("saveconfigerror", [])
                            self.skip_spectrum()
                        else:
                            self.logger.logfile = self.find_logfile(save_path)
                            if self.logger.logfile is None:
                                self.logger.logfile = self.make_logfile(save_path)
                                self.data_files_to_ignore.append(self.logger.logfile.split("\\")[-1])
                            print("saveconfigsuccess")
                            self.send("saveconfigsuccess", [])
                    except Exception as e:
                        print(e)
                        self.spec_controller.failed_to_open = False
                        self.send("saveconfigerror", [])
                        self.skip_spectrum()
                        instrument_config_num = None

                elif cmd == "wr":
                    if self.spec_controller.save_dir == "":
                        self.send("noconfig", [])
                        print("noconfig")
                        continue
                    if self.spec_controller.numspectra is None:
                        self.send("nonumspectra", [])
                        print("nonumspectectra")
                        continue

                    if self.computer == "old":
                        filename = (
                            self.spec_controller.save_dir
                            + "\\"
                            + self.spec_controller.basename
                            + "."
                            + self.spec_controller.nextnum
                        )
                    elif self.computer == "new" or self.computer == "desktop":
                        filename = (
                            self.spec_controller.save_dir
                            + "\\"
                            + self.spec_controller.basename
                            + self.spec_controller.nextnum
                            + ".asd"
                        )

                    if os.path.isfile(filename):
                        continue
                    self.spec_controller.white_reference()
                    if self.spec_controller.wr_success == True:
                        self.send("wrsuccess", [])
                    else:
                        self.send("wrfailed", [])
                    self.spec_controller.wr_success = False
                    self.spec_controller.wr_failure = False

                elif cmd == "opt":

                    # This makes sure that there was always a save configuration set before optimizing. Data files
                    # don't get saved during optimization, but this needs to happen anyway because we need to know
                    # where to put the log file when we record that we optimized.
                    if self.spec_controller.save_dir == "":
                        print("Sending noconfig")
                        self.send("noconfig", [])
                        continue

                    # And, we do need to know how many spectra we are averaging so we know when to time out
                    if self.spec_controller.numspectra is None:
                        self.send("nonumspectra", [])
                        continue
                    try:
                        self.spec_controller.optimize()
                        if self.spec_controller.opt_complete == True:
                            self.logger.log_opt()
                            self.send("optsuccess", [])
                        else:
                            self.send("optfailure", [])
                    except:
                        print("Exception occurred and optimization failed.")
                        self.send("optfailure", [])

                elif "process" in cmd:
                    input_path = params[0]
                    output_path = params[1]
                    csv_name = params[2]
                    print("**********")
                    print(input_path)
                    print(output_path)
                    print(csv_name)
                    logfile_for_reading = None  # We'll find it in the data folder.

                    if input_path == "spec_temp_data_loc":
                        input_path = self.temp_data_loc
                    if output_path == "spec_temp_data_loc":
                        for file in os.listdir(self.temp_data_loc):
                            os.remove(os.path.join(self.temp_data_loc, file))
                        output_path = self.temp_data_loc

                    # check if the input directory exists. if not, send an error back
                    if not os.path.exists(input_path):
                        self.send("processerrornodirectory", [])
                        continue

                    # Look through files in data directory until you find a log file
                    for potential_log in os.listdir(input_path):
                        if ".txt" in potential_log:
                            try:
                                with open(input_path + "\\" + potential_log, "r") as f:
                                    firstline = f.readline()
                                    if "#AutoSpec log" in firstline or "# Tanager log" in firstline:
                                        logfile_for_reading = input_path + "\\" + potential_log
                                        break
                            except OSError as e:
                                print(e)

                    if logfile_for_reading is None:
                        print("ERROR: No logfile found in data directory")

                    if os.path.isfile(output_path + "\\" + csv_name) and csv_name != "proc_temp.csv":
                        self.send("processerrorfileexists", [])
                        continue

                    elif os.path.isfile(output_path + "\\" + csv_name):
                        writeable = os.access(output_path, os.W_OK)
                        if not writeable:
                            self.send("processerrorcannotwrite", [])
                            continue

                        os.remove(output_path + "\\" + csv_name)

                    writeable = os.access(output_path, os.W_OK)
                    if not writeable:
                        self.send("processerrorcannotwrite", [])
                        continue

                    else:
                        # If the specified output path is in the C drive, we can write straight to it. Otherwise,
                        # we're going to temporarily store the file in the temp data location
                        if output_path[0:3] != "C:\\":
                            temp_output_path = self.temp_data_loc
                        else:
                            temp_output_path = output_path

                        datafile = temp_output_path + "\\" + csv_name

                        try:
                            self.process_controller.process(input_path, temp_output_path, csv_name)
                        except Exception as e:
                            self.process_controller.reset()
                            self.send("processerror", [])
                            traceback.print_exc()
                            continue
                        # Check that the expected file arrived fine after processing.
                        # This sometimes wasn't happening if you fed ViewSpecPro data without
                        # taking a white reference or optimizing.
                        saved = False
                        t0 = time.perf_counter()
                        t = time.perf_counter()
                        while t - t0 < 20 and not saved:
                            saved = os.path.isfile(datafile)
                            time.sleep(0.2)
                            t = time.perf_counter()
                        corrected = False
                        if not saved:
                            print("not saved??")
                            print(datafile)
                        if saved:
                            # Load headers from the logfile, then apply correction
                            if logfile_for_reading is not None:
                                print("Loading headers from log file")
                                warnings = self.set_headers(datafile, logfile_for_reading)
                                print("Applying correction for non-Lambertian behavior of Spectralon")
                                try:
                                    self.corrector.correct(
                                        datafile
                                    )  # applies a correction based on measured BRDF for spectralon
                                    corrected = True
                                except:
                                    print("warning! correction not applied")
                            else:
                                print("Warning! No log file found!")
                                self.tsv_to_csv(datafile)  # still replace tabs with commas
                                warnings = "no log found"

                            print("done")
                            final_datafile = (
                                output_path + "\\" + csv_name
                            )  # May or may not be the same loc as temporary.
                            data_base = ".".join(
                                csv_name.split(".")[0:-1]
                            )  # E.g. for a csv name of foo.csv, returns foo
                            final_logfile = (
                                output_path + "\\" + data_base + "_log"
                            )  # We're going to copy the logfile along with it,
                            # givnig it a sensible name e.g. foo_log.txt

                            # But first we have to make sure there isn't an existing file with that name.
                            i = 1
                            logfile_base = final_logfile
                            while os.path.isfile(final_logfile + ".txt"):
                                final_logfile = logfile_base + "_" + str(i)
                                i += 1
                            final_logfile += ".txt"
                            # Ok, now copy!
                            if logfile_for_reading is not None:
                                os.system("copy " + logfile_for_reading + " " + final_logfile)
                                if output_path == self.spec_controller.save_dir:
                                    self.data_files_to_ignore.append(final_logfile.split("\\")[-1])
                                # If we need to move the data to get it to its final destination, do it!

                            if temp_output_path != output_path:
                                tempfilename = datafile
                                os.system("move " + tempfilename + " " + final_datafile)

                            # Read data to send to control computer
                            spec_data = ""
                            with open(final_datafile, "r") as f:
                                spec_data = f.read()

                            log_data = ""
                            with open(final_logfile, "r") as f:
                                log_data = f.read()

                            # If the output directory is the same (or within) the data directory,
                            # there's no need to alert the user to an unexpected file being introduced
                            # since clearly it was expected.
                            if self.spec_controller.save_dir is not None and self.spec_controller.save_dir != "":
                                if self.spec_controller.save_dir in final_datafile:
                                    expected = final_datafile.split(self.spec_controller.save_dir)[1].split("\\")[1]
                                    self.spec_controller.hopefully_saved_files.append(expected)

                            if corrected == True and logfile_for_reading is not None:
                                self.send("spec_data", [spec_data])
                                self.send("log_data", [log_data])
                                self.send("processsuccess", [])

                            elif logfile_for_reading is not None:
                                self.send("spec_data", [spec_data])
                                self.send("log_data", [log_data])
                                self.send("processsuccessnocorrection", [])
                            else:
                                self.send("spec_data", [spec_data])
                                self.send("processsuccessnolog", [])
                        # We don't actually know for sure that processing failed because of failing
                        # to optimize or white reference, but ViewSpecPro sometimes silently fails if
                        # you haven't been doing those things.
                        else:
                            self.send("processerrorwropt", [])

                elif "instrumentconfig" in cmd:


                    instrument_config_num = params[0]
                    try:
                        self.spec_controller.instrument_config(instrument_config_num)
                        self.send("iconfigsuccess", [])
                    except:
                        self.send("iconfigfailure", [])

                elif "rmfile" in cmd:
                    try:
                        delme = params[0] + "\\" + params[1] + params[2] + ".asd"
                        os.remove(delme)
                        self.send("rmsuccess", [])
                    except:
                        self.send("rmfailure", [])

                # Used for copying remote data over to the control compy for plotting, etc
                elif "transferdata" in cmd:
                    source = params[0]
                    if "spec_temp_data_loc" in source:
                        source = source.replace("spec_temp_data_loc", self.temp_data_loc)
                        print(source)
                    try:
                        with open(source, "r") as file:
                            print("opened file")
                            data = file.readlines()
                            batch_size = 500
                            self.send(f"datatransferstarted{len(data)/500}", [])
                            batch = 0
                            next_message = ""
                            for i, line in enumerate(data):
                                next_message += line
                                if i != 0 and i % batch_size == 0:
                                    self.send(f"batch{batch}", [next_message])
                                    batch += 1
                                    next_message = ""
                            self.send(f"batch{batch}", [next_message])
                            batch += 1
                            self.send(f"datatransfercomplete{batch}", [])

                    except OSError:
                        self.send("datafailure", [])

                # List directories within a folder for the remote file explorer on the control compy
                elif "listdir" in cmd:
                    dir = params[0]
                    if not os.path.isdir(dir):
                        self.send("listdirfailed", [])
                    else:
                        try:
                            if dir[-1] != "\\":
                                dir += "\\"
                            cmdfilename = self.cmd_to_filename("listdir", [params[0]])
                            files = os.listdir(dir)
                            message = cmdfilename
                            for file in files:
                                if os.path.isdir(dir + file) and file[0] != ".":
                                    message += "&" + file
                            print("sending a response to listdir")
                            self.send(message, [])
                        except (PermissionError):
                            self.send("listdirfailedpermission", [])
                        except:
                            self.send("listdirfailed", [])

                # List directories and files in a folder for the remote file explorer on the control compy
                elif "listcontents" in cmd:
                    try:
                        dir = params[0]
                        if dir[-1] != "\\":
                            dir += "\\"
                        cmdfilename = self.cmd_to_filename(cmd, [params[0]])
                        files = os.listdir(dir)
                        sorted_files = []
                        for i, file in enumerate(files):
                            if os.path.isdir(dir + file) and file[0] != ".":
                                sorted_files.append(file)
                            elif file[0] != ".":
                                # This is a way for the control compy to differentiate files from directories
                                sorted_files.append("~:" + file)
                        sorted_files.sort()
                        self.send(cmdfilename, sorted_files)
                    except (PermissionError):
                        self.send("listdirfailedpermission", [])

                    except:
                        self.send("listdirfailed", [])

                # make a directory
                elif cmd == "mkdir":
                    try:
                        print(params[0])
                        os.makedirs(params[0])
                        if self.spec_controller.save_dir is not None and self.spec_controller.save_dir != "":
                            print("setting spec save directory to new directory")
                            if "\\".join(params[0].split("\\")[:-1]) == self.spec_controller.save_dir:
                                expected = params[0].split(self.spec_controller.save_dir)[1].split("\\")[1]
                                self.spec_controller.hopefully_saved_files.append(expected)
                        self.send("mkdirsuccess", [])
                    except (FileExistsError):
                        self.send("mkdirfailedfileexists", [])

                    except (PermissionError):
                        self.send("mkdirfailedpermission", [])
                    except:

                        self.send("mkdirfailed", [])

                # Not implemented yet!
                elif "rmdir" in cmd:
                    try:
                        shutil.rmtree(params[0])
                        if self.spec_controller.save_dir is not None and self.spec_controller.save_dir != "":
                            if params[0] in self.spec_controller.save_dir:
                                self.spec_controller.save_dir = None

                        self.send("rmdirsuccess", [])

                    except (PermissionError):

                        self.send("rmdirfailedpermission", [])

                    except:
                        self.send("rmdirfailed", [])

            time.sleep(0.25)

    def send(self, cmd, params):
        message = self.cmd_to_filename(cmd, params)
        sent = self.client.send(message)
        # the lostconnection message will get resent anyway, no need to clog up lanes by retrying here.
        while not sent and message != "lostconnection":
            print("Failed to send message, retrying.")
            print(message)
            sent = self.client.send(message)


    def filename_to_cmd(self, filename):
        cmd = filename.split("&")[0]
        # if (
        #     "listdir" not in cmd and "listcontents" not in cmd
        # ):  # For listdir, we need to remember the cmd number sent over - the control compy
        #     # will be watching for an exact filename match.
        #     while cmd[-1] in "1234567890":
        #         cmd = cmd[0:-1]
        params = filename.split("&")[1:]
        i = 0
        for param in params:
            params[i] = param
            i = i + 1
        return cmd, params

    def cmd_to_filename(self, cmd, params):
        filename = cmd
        i = 0
        for param in params:
            filename = filename + "&" + param
            i = i + 1
        return filename

    def skip_spectrum(self):
        time.sleep(2)
        for item in self.local_server.queue:
            if "spectrum" in item:
                self.local_server.queue.remove(item)
        time.sleep(1)

    def check_for_unexpected(self, save_dir, hopefully_saved_files, data_files_to_ignore):
        data_files = []
        try:
            data_files = os.listdir(save_dir)
        except:
            pass
        expected_files = []
        for file in hopefully_saved_files:
            expected_files.append(file.split("\\")[-1])
        for file in data_files:
            # print('This file is here:'+file)
            if file not in data_files_to_ignore:
                if file not in expected_files:
                    # print('And it is not expected.')
                    return file
        return None

    def find_logfile(self, directory):
        logfile = None
        for potential_log in os.listdir(directory):
            if ".txt" in potential_log:
                try:
                    with open(directory + "\\" + potential_log, "r") as f:
                        firstline = f.readline()
                        if "#AutoSpec log" in firstline:
                            logfile = directory + "\\" + potential_log
                            break
                except Exception as e:
                    print(e)
        if logfile is not None:
            with open(logfile, "a") as f:
                datestring = ""
                datestringlist = str(datetime.datetime.now()).split(".")[:-1]
                for d in datestringlist:
                    datestring = datestring + d
                f.write("#AutoSpec log re-opened on " + datestring + ".\n\n")
        return logfile

    def make_logfile(self, directory):
        files = os.listdir(directory)
        i = 1
        logfile = "log.txt"
        while logfile in files:
            logfile = "log" + str(i) + ".txt"
            i += 1
        with open(directory + "\\" + logfile, "w+") as f:
            datestring = ""
            datestringlist = str(datetime.datetime.now()).split(".")[:-1]
            for d in datestringlist:
                datestring = datestring + d
            f.write("#AutoSpec log initialized on " + datestring + ".\n\n")

        return directory + "\\" + logfile

    # convert to csv
    def tsv_to_csv(self, datafile):
        data = []
        with open(datafile, "r") as file:
            line = file.readline()
            while line != "":
                data.append(line.replace("\t", ","))
                line = file.readline()
            with open(datafile, "w+") as file:
                for i, line in enumerate(data):
                    if i == 0:
                        file.write("Sample Name:" + line.strip("Wavelength"))
                        w_line = "Wavelength"
                        for _ in range(len(line.split(",")) - 1):
                            w_line += ","
                        file.write(w_line + "\n")
                    else:
                        file.write(line)
        print("converted to .csv")

    def set_headers(self, datafile, logfile):

        labels = {}
        nextfile = None
        nextnote = None

        if os.path.exists(logfile):
            with open(logfile) as log:
                line = log.readline()
                while line != "":
                    while "i: " not in line and line != "":
                        line = log.readline()  # skip the first few lines until you get to viewing geometry
                    if "i:" in line:
                        try:
                            nextnote = " (i=" + line.split("i: ")[-1].strip("\n")
                        except:
                            nextnote = " (i=?"
                    while "e: " not in line and line != "":
                        line = log.readline()
                    if "e:" in line:
                        try:
                            nextnote = nextnote + " e=" + line.split("e: ")[-1].strip("\n") + ")"
                        except:
                            nextnote = nextnote + " e=?)"
                    while "az: " not in line and line != "":
                        line = log.readline()
                    if "az:" in line:
                        try:
                            nextnote = nextnote + " az=" + line.split("az: ")[-1].strip("\n") + ")"
                        except:
                            nextnote = nextnote + " az=?)"
                    while "filename" not in line and line != "":
                        line = log.readline()
                    if "filename" in line:
                        if "\\" in line:
                            line = line.split("\\")
                        else:
                            line = line.split("/")
                        nextfile = line[-1].strip("\n")
                        nextfile = nextfile.split(".")
                        nextfile = nextfile[0] + nextfile[1]

                    while "Label" not in line and line != "":
                        line = log.readline()
                    if "Label" in line:
                        nextnote = line.split("Label: ")[-1].strip("\n") + nextnote

                    if nextfile is not None and nextnote is not None:
                        nextnote = nextnote.strip("\n")
                        labels[nextfile] = nextnote

                        nextfile = None
                        nextnote = None
                    line = log.readline()
                if len(labels) != 0:

                    data_lines = []
                    with open(datafile, "r") as data:
                        line = data.readline().strip("\n")
                        data_lines.append(line)
                        while line != "":
                            line = data.readline().strip("\n")
                            data_lines.append(line)

                    datafiles = data_lines[0].split("\t")[
                        1:
                    ]  # The first header is 'Wavelengths', the rest are file names

                    spectrum_labels = []
                    unknown_num = (
                        0  # This is the number of files in the datafile headers that aren't listed in the log file.
                    )
                    for i, filename in enumerate(datafiles):
                        label_found = False
                        filename = filename.replace(".", "")
                        spectrum_label = filename
                        if filename in labels:
                            label_found = True
                            if labels[filename] != "":
                                spectrum_label = labels[filename]

                        # Sometimes the label in the file will have sco attached. Take off the sco
                        # and see if that is in the labels in the file.
                        filename_minus_sco = filename[0:-3]
                        if filename_minus_sco in labels:
                            label_found = True
                            if labels[filename_minus_sco] != "":
                                spectrum_label = labels[filename_minus_sco]

                        if label_found == False:
                            unknown_num += 1
                        spectrum_labels.append(spectrum_label)

                    header_line = data_lines[0].split("\t")[0]  # This will just be 'Wavelengths'
                    for i, label in enumerate(spectrum_labels):
                        header_line = header_line + "\t" + label

                    data_lines[0] = header_line

                    with open(datafile, "w") as data:
                        for line in data_lines:
                            data.write(line + "\n")

                # Now reformat data to fit WWU spectral library format.
                data = []
                metadata = [
                    "Database of origin:,Western Washington University Planetary Spectroscopy Lab",
                    "Sample Name",
                    "Viewing Geometry",
                ]

                for i, line in enumerate(data_lines):
                    if i == 0:
                        headers = line.split("\t")
                        headers[-1] = headers[-1].strip("\n")
                        for i, header in enumerate(headers):
                            if i == 0:
                                continue
                            # If sample names and geoms were read successfully from logfile, this should always
                            # work fine. But in case logfile is missing or badly formatted, don't break, just don't
                            # have geom info either.
                            try:
                                sample_name = header.split("(")[0]
                            except:
                                sample_name = header
                            try:
                                geom = header.split("(")[1].strip(")")
                            except:
                                geom = ""
                            metadata[1] += "," + sample_name
                            metadata[2] += "," + geom
                        metadata.append("")
                        metadata.append("Wavelength")

                    else:
                        data.append(line.replace("\t", ","))

                with open(datafile, "w+") as file:
                    for line in metadata:
                        file.write(line)
                        file.write("\n")
                    for line in data:
                        file.write(line)
                        file.write("\n")

                if len(labels) == 0:
                    return "nolabels"
                elif unknown_num == 0:
                    return ""  # No warnings
                elif unknown_num == 1:
                    return "1unknown"  # This will succeed but the control computer will print a warning that not all
                    # samples were labeled. Knowing if it was one or more than one just helps with grammar.

                elif unknown_num > 1:
                    return "unknowns"
        else:
            return "nolog"