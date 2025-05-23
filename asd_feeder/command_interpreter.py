import datetime
import shutil
import traceback
import os
import time

from asd_feeder import utils

class CommandInterpreter:
    def __init__(self, client, server, spec_controller, process_controller, computer, logger, corrector, temp_data_loc, RS3_config_loc):
        self.client = client
        self.local_server = server
        self.spec_controller = spec_controller
        self.process_controller = process_controller
        self.computer = computer
        self.logger = logger
        self.corrector = corrector
        self.temp_data_loc = temp_data_loc
        self.RS3_config_loc = RS3_config_loc
        self.data_files_to_ignore = []


    def check_writeable(self, params):
        try:
            try:
                os.mkdir(params[0] + "\\autospec_temp")
            except OSError:
                pass # This could happen if an autospec temp file was left hanging
                # (created but not deleted) earlier.
            os.rmdir(params[0] + "\\autospec_temp")
            utils.send(self.client, "yeswriteable", [])
        except (NotADirectoryError, PermissionError, OSError) as e:
            utils.send(self.client, "notwriteable", [])

    def restart(self, params, run_time):
        if run_time < 20:
            time.sleep(20)
        utils.send(self.client, "restarting", [])
        if run_time > 20:
            time.sleep(10)
            os.system("shutdown /r /t 1")
        else:
            print("Just restarted. Doing nothing.")

    def take_spectrum(self, params):
        if (
            self.spec_controller.save_dir == ""
        ):
            # If there's no save configuration set on this computer, tell the control computer you need
            # one. This comes up if the script restarts on the spec compy but there is no restart on
            # the control compy.
            utils.send(self.client, "noconfig", [])
            return
        if (
            self.spec_controller.numspectra is None or self.spec_controller.calfile is None
        ):  # Same as above, but for instrument configuration (number of spectra to average)
            utils.send(self.client, "nonumspectra", [])
            return

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
            utils.send(self.client, "savespecfailedfileexists", [])
            return

        try:
            self.spec_controller.take_spectrum(filename)
        except:
            traceback.print_exc()
            utils.send(self.client, "specfailed", [])
            return

        # Now wait for the data file to turn up where it belongs.
        saved = False
        timeout = int(self.spec_controller.numspectra) * 2
        while (
            timeout > 0 and saved is False
        ):  # Depending on the number of spectra we are averaging, this might take a while.
            saved = os.path.isfile(filename)
            time.sleep(0.2)
            timeout -= 0.2

        if saved:
            self.logger.log_spectrum(self.spec_controller.numspectra, i, e, az, filename, self.spec_controller.calfile, label)
            utils.send(self.client, "savedfile", [filename])
            print("Spectrum saved")
        else:
            self.spec_controller.hopefully_saved_files.pop(-1)
            self.spec_controller.nextnum = str(int(self.spec_controller.nextnum) - 1)
            utils.send(self.client, "failedtosavefile", [filename])

    def listdir(self, params):
        dir = params[0]
        if not os.path.isdir(dir):
            utils.send(self.client, "listdirfailed", [])
        else:
            try:
                if dir[-1] != "\\":
                    dir += "\\"
                cmdfilename = utils.cmd_to_filename("listdir", [params[0]])
                files = os.listdir(dir)
                message = cmdfilename
                for file in files:
                    if os.path.isdir(dir + file) and file[0] != ".":
                        message += "&" + file
                utils.send(self.client, message, [])
            except (PermissionError):
                utils.send(self.client, "listdirfailedpermission", [])
            except:
                utils.send(self.client, "listdirfailed", [])

    def mkdir(self, params):
        try:
            print(params[0])
            os.makedirs(params[0])
            if self.spec_controller.save_dir is not None and self.spec_controller.save_dir != "":
                print("setting spec save directory to new directory")
                if "\\".join(params[0].split("\\")[:-1]) == self.spec_controller.save_dir:
                    expected = params[0].split(self.spec_controller.save_dir)[1].split("\\")[1]
                    self.spec_controller.hopefully_saved_files.append(expected)
            utils.send(self.client, "mkdirsuccess", [])
        except (FileExistsError):
            utils.send(self.client, "mkdirfailedfileexists", [])

        except (PermissionError):
            utils.send(self.client, "mkdirfailedpermission", [])
        except:
            utils.send(self.client, "mkdirfailed", [])

    def rmdir(self, params):
        try:
            shutil.rmtree(params[0])
            if self.spec_controller.save_dir is not None and self.spec_controller.save_dir != "":
                if params[0] in self.spec_controller.save_dir:
                    self.spec_controller.save_dir = None

            utils.send(self.client, "rmdirsuccess", [])

        except (PermissionError):
            utils.send(self.client, "rmdirfailedpermission", [])

        except:
            utils.send(self.client, "rmdirfailed", [])

    def listcontents(self, params):
        try:
            dir = params[0]
            if dir[-1] != "\\":
                dir += "\\"
            cmdfilename = utils.cmd_to_filename("listcontents", [params[0]])
            # even though things aren't case sensitive here, they will be later when processing files.
            # because of this, it's best to idenfity it now if the user has input a path where the case
            # does not match the real path case.
            case_correct = os.path.realpath(dir) + "\\"
            if dir != case_correct:
                utils.send(self.client, "listdirfailedcase", [case_correct[:-1]])
                return

            files = os.listdir(dir)
            sorted_files = []
            for i, file in enumerate(files):
                if os.path.isdir(dir + file) and file[0] != ".":
                    sorted_files.append(file)
                elif file[0] != ".":
                    # This is a way for the control compy to differentiate files from directories
                    sorted_files.append("~:" + file)
            sorted_files.sort()
            utils.send(self.client, cmdfilename, sorted_files)
        except (PermissionError):
            utils.send(self.client, "listdirfailedpermission", [])

        except:
            traceback.print_exc()
            utils.send(self.client, "listdirfailed", [])

    def transferdata(self, params):
        source = params[0]
        if "spec_temp_data_loc" in source:
            source = source.replace("spec_temp_data_loc", self.temp_data_loc)
            print(source)
        try:
            with open(source, "r") as file:
                data = file.readlines()
                if len(data[10]) < 5000:
                    print("Smallish!")
                    batch_size = 100
                elif len(data[10]) < 10000:
                    print("Biggish!")
                    batch_size = 50
                else:
                    print("Big!")
                    batch_size = 10
                utils.send(self.client, f"datatransferstarted{len(data)/batch_size}", [])

                batch = 0
                next_message = ""
                for i, line in enumerate(data):
                    next_message += line
                    if i != 0 and i % batch_size == 0:
                        utils.send(self.client, f"batch{batch}+", [next_message])
                        batch += 1
                        next_message = ""

                utils.send(self.client, f"batch{batch}+", [next_message])

                batch += 1
                utils.send(self.client, f"datatransfercomplete{batch}", [])

        except OSError:
            utils.send(self.client, "datafailure", [])
    def rmfile(self, params):
        try:
            delme = params[0] + "\\" + params[1] + params[2] + ".asd"
            os.remove(delme)
            utils.send(self.client, "rmsuccess", [])
        except:
            utils.send(self.client, "rmfailure", [])

    def instrumentconfig(self, params):
        instrument_config_num = params[0]
        calfile_num = params[1]

        if calfile_num in ['3" Puck', '5" Square']:
            self.set_calfile_path(calfile_num)

        try:
            self.spec_controller.instrument_config(instrument_config_num, calfile_num)
            utils.send(self.client, "iconfigsuccess", [])
        except:
            utils.send(self.client, "iconfigfailure", [])

    def set_calfile_path(self, calfile_num):
        if calfile_num == '3" Puck':
            calfile_path = r"C:\ProgramData\ASD\RS3\abs184831_3.ref"
        elif calfile_num == '5" Square':
            calfile_path = r"C:\ProgramData\ASD\RS3\abs184831_5.ref"
        buffer = []
        with open(self.RS3_config_loc, 'r') as RS3_config:
            buffer.append(RS3_config.readline())
            while buffer[-1]:
                buffer.append(RS3_config.readline())
        for line in buffer:
            if "AbsoluteReflectanceFile" in line:
                if calfile_path in line:
                    return

        self.spec_controller.quit_RS3()
        time.sleep(10) #Make sure it's fully quit before re-writing the file

        with open(self.RS3_config_loc, "w") as RS3_config:
            for line in buffer:
                if "AbsoluteReflectanceFile" not in line:
                    RS3_config.write(line)
                else:
                    RS3_config.write(f"AbsoluteReflectanceFile={calfile_path}\n")
        self.spec_controller.start_RS3()
        time.sleep(3)

        self.spec_controller.spectrum_save(
            self.spec_controller.save_dir,
            self.spec_controller.basename,
            self.spec_controller.nextnum
        )


    def restartrs3(self, params):
        try:
            self.spec_controller.restart()
            utils.send(self.client, "rs3restarted", [])
        except:
            traceback.print_exc()
            utils.send(self.client, "rs3restartfailed", [])


    def saveconfig(self, params):
        save_path = params[0]
        print("Checking for unexpected files")
        self.routine_file_check(save_path)
        print("Done.")
        utils.send(self.client, "donelookingforunexpected", [])


        basename = params[1]
        startnum = params[2]
        filename = ""
        if self.computer == "old":
            filename = save_path + "\\" + basename + "." + startnum
        elif self.computer == "new" or self.computer == "desktop":
            filename = save_path + "\\" + basename + startnum + ".asd"

        if os.path.isfile(filename):
            utils.send(self.client, "saveconfigfailedfileexists", [])
            self.skip_spectrum()
            return
        try:
            self.spec_controller.spectrum_save(save_path, basename, startnum)
            if self.spec_controller.failed_to_open:
                self.spec_controller.failed_to_open = False
                utils.send(self.client, "saveconfigerror", [])
                self.skip_spectrum()
            else:
                self.logger.logfile = self.find_logfile(save_path)
                if self.logger.logfile is None:
                    self.logger.logfile = self.make_logfile(save_path)
                    self.data_files_to_ignore.append(self.logger.logfile.split("\\")[-1])
                print("saveconfigsuccess")
                utils.send(self.client, "saveconfigsuccess", [])
        except Exception as e:
            self.spec_controller.failed_to_open = False
            utils.send(self.client, "saveconfigerror", [])
            self.skip_spectrum()
            instrument_config_num = None
            traceback.print_exc()

    def routine_file_check(self, path=None):
        if path is None:
            path = self.spec_controller.save_dir

        file = self.check_for_unexpected(
            path, self.spec_controller.hopefully_saved_files, self.data_files_to_ignore
        )
        unexpected_files = []
        while file is not None:
            self.data_files_to_ignore.append(file)
            unexpected_files.append(file)
            file = self.check_for_unexpected(
                path, self.spec_controller.hopefully_saved_files, self.data_files_to_ignore
            )
        if len(unexpected_files) > 0:
            utils.send(self.client, "unexpectedfile", unexpected_files)

    def white_reference(self, params):
        if self.spec_controller.save_dir == "":
            utils.send(self.client, "noconfig", [])
            print("noconfig")
            return
        print("In white reference")
        print(self.spec_controller.numspectra)
        print(self.spec_controller.calfile)
        print(type(self.spec_controller.calfile))
        if self.spec_controller.numspectra is None or self.spec_controller.calfile is None:
            utils.send(self.client, "nonumspectra", [])
            print("nonumspectectra")
            return

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
            print("Warning: File exists. Overwriting.")
        try:
            self.spec_controller.white_reference()
        except:
            print("Exception during white reference")
            utils.send(self.client, "wrfailed", [])

        if self.spec_controller.wr_success == True:
            utils.send(self.client, "wrsuccess", [])
        else:
            utils.send(self.client, "wrfailed", [])
        self.spec_controller.wr_success = False
        self.spec_controller.wr_failure = False
    def opt(self, params):
        # This makes sure that there was always a save configuration set before optimizing. Data files
        # don't get saved during optimization, but this needs to happen anyway because we need to know
        # where to put the log file when we record that we optimized.
        if self.spec_controller.save_dir == "":
            print("Sending noconfig")
            utils.send(self.client, "noconfig", [])
            return

        # And, we do need to know how many spectra we are averaging so we know when to time out
        if self.spec_controller.numspectra is None:
            utils.send(self.client, "nonumspectra", [])
            return
        try:
            self.spec_controller.optimize()
            if self.spec_controller.opt_complete == True:
                self.logger.log_opt()
                utils.send(self.client, "optsuccess", [])
            else:
                utils.send(self.client, "optfailure", [])
        except:
            print("Exception occurred and optimization failed.")
            utils.send(self.client, "optfailure", [])

    def process(self, params):
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
            utils.send(self.client, "processerrornodirectory", [])
            return

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
                    traceback.print_exc()

        if logfile_for_reading is None:
            print("ERROR: No logfile found in data directory")

        if os.path.isfile(output_path + "\\" + csv_name) and csv_name != "proc_temp.csv":
            utils.send(self.client, "processerrorfileexists", [])
            return

        elif os.path.isfile(output_path + "\\" + csv_name):
            writeable = os.access(output_path, os.W_OK)
            if not writeable:
                utils.send(self.client, "processerrorcannotwrite", [])
                return

            os.remove(output_path + "\\" + csv_name)

        writeable = os.access(output_path, os.W_OK)
        if not writeable:
            utils.send(self.client, "processerrorcannotwrite", [])
            return

        else:
            # If the specified output path is in the C drive, we can write straight to it. Otherwise,
            # we're going to temporarily store the file in the temp data location
            if output_path[0:3] != "C:\\":
                temp_output_path = self.temp_data_loc
            else:
                temp_output_path = output_path

            datafile = temp_output_path + "\\" + csv_name

            #Don't give warnings about all the temp files that get dropped into the save directroy
            print("*************************************************")
            print(input_path)
            print(self.spec_controller.save_dir)
            if input_path == self.spec_controller.save_dir:
                self.data_files_to_ignore.append(csv_name)
                batches = int(len(self.data_files_to_ignore)/self.process_controller.batch_size)+1
                base = csv_name.split(".csv")[0]
                for i in range(batches):
                    ignore_file = f"{base}_{i}.csv"
                    print(ignore_file)
                    self.data_files_to_ignore.append(ignore_file)

            try:
                self.process_controller.process(input_path, temp_output_path, csv_name, self.watchdog_monitor)
            except Exception as e:
                self.process_controller.reset()
                utils.send(self.client, "processerror", [])
                traceback.print_exc()
                print("Sent processerror back to control compy")
                return


            # Check that the expected file arrived fine after processing.
            # This sometimes wasn't happening if you fed ViewSpecPro data without
            # taking a white referencetra or optimizing.
            saved = False
            t0 = time.perf_counter()
            t = time.perf_counter()
            while t - t0 < 200 and not saved:
                saved = os.path.isfile(datafile)
                time.sleep(0.2)
                t = time.perf_counter()
            corrected = False
            if not saved:
                print("Datafile not saved.")
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
                    except Exception as e:
                        traceback.print_exc()
                        print("Warning! correction not applied")
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

                if corrected == True and logfile_for_reading is not None and warnings == "":
                    utils.send(self.client, "processsuccess", [])

                elif not corrected:
                    utils.send(self.client, "processsuccessnocorrection", [])

                elif warnings != "":
                    utils.send(self.client, "processsuccessnolabels", [])

                else:
                    utils.send(self.client, "processsuccessnolog", [])
            # We don't actually know for sure that processing failed because of failing
            # to optimize or white reference, but ViewSpecPro sometimes silently fails if
            # you haven't been doing those things.
            else:
                utils.send(self.client, "processerrorwropt", [])

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

    def watchdog_monitor(self):
        with open(os.path.join(self.temp_data_loc, "watchdog"), "w+") as f:
            pass  # This file is looked for by the watchdog.

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
                            nextnote = nextnote + " e=" + line.split("e: ")[-1].strip("\n")
                        except:
                            nextnote = nextnote + " e=?"
                    while "az: " not in line and line != "":
                        line = log.readline()
                    if "az:" in line:
                        try:
                            nextnote = nextnote + " az=" + line.split("az: ")[-1].strip("\n") + ")"
                        except:
                            nextnote = nextnote + " az=?)"
                    while "filename" not in line and "Data file" not in line and line != "":
                        line = log.readline()
                    if "filename" in line or "Data file" in line:
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
                            print("Could not find label for spectrum")
                            print(filename)
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