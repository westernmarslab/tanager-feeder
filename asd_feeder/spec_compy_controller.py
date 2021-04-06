import datetime
import shutil
import traceback
import os
import time
from threading import Thread
from multiprocessing import Process

from tanager_tcp import TanagerClient, TanagerServer

from asd_feeder.asd_controls import RS3Controller, ViewSpecProController
from asd_feeder.logger import Logger
from asd_feeder.spectralon_corrector import SpectralonCorrector
from asd_feeder.command_interpreter import CommandInterpreter

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
        self.command_interpreter = CommandInterpreter(self.client, self.local_server, self.spec_controller, self.computer, self.logger, self.corrector)
        self.time_since_cycled = 0

        watchdog = Watchdog(self.temp_data_loc)
        process = Process(target=watchdog.watch)
        process.start()

    def listen(self):
        print_connection_announcement = None
        count = 0
        while True:
            count += 1

            if count%10==0:
                with open(os.path.join(self.temp_data_loc, "watchdog"), "w+") as f:
                    pass # This file is looked for by the watchdog.

            # check connectivity with spectrometer
            print("checking connection")
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
            print("Looking for unexpected files")
            # check for unexpected files in data directory
            self.command_interpreter.routine_file_check()
            print("handling commands")


            # check for new commands in the tcp server queue
            while len(self.local_server.queue) > 0:
                print(".")
                if self.local_server.remote_server_address != self.client.server_address:
                    print("Setting control computer address:")
                    self.client.server_address = self.local_server.remote_server_address
                    print(self.client.server_address)
                message = self.local_server.queue.pop(0)
                if message == "test":
                    continue
                print(f"Message received: {message}")

                cmd, params = self.filename_to_cmd(message)
#                 if cmd != "test":
#                     print("***************")
#                     print("Command received: " + cmd)

                if cmd == "restartcomputer":
                    self.command_interpreter.restart(params)

                elif cmd == "restartrs3":
                    self.command_interpreter.restartrs3(params)

                elif "checkwriteable" in cmd:  # Check whether you can write to a given directory
                    self.command_interpreter.check_writeable(params)

                elif "spectrum" in cmd:  # Take a spectrum
                    self.command_interpreter.take_spectrum(params)

                elif cmd == "saveconfig":
                    self.command_interpreter.saveconfig(params)

                elif cmd == "wr":
                    self.command_interpreter.white_reference(params)

                elif cmd == "opt":
                    self.command_interpreter.opt(params)

                elif "process" in cmd:
                    self.command_interpreter.process(params)

                elif "instrumentconfig" in cmd:
                    self.command_interpreter.instrumentconfig(params)

                elif "rmfile" in cmd:
                    self.command_interpreter.rmfile(params)

                # Used for copying remote data over to the control compy for plotting, etc
                elif "transferdata" in cmd:
                    self.command_interpreter.transferdata(params)

                # List directories within a folder for the remote file explorer on the control compy
                elif "listdir" in cmd:
                    self.command_interpreter.listdir(params)

                # List directories and files in a folder for the remote file explorer on the control compy
                elif "listcontents" in cmd:
                    self.command_interpreter.listcontents(params)

                # make a directory
                elif cmd == "mkdir":
                    self.command_interpreter.mkdir(params)

                # Not implemented yet!
                elif "rmdir" in cmd:
                    self.command_interpreter.rmdir(params)

            time.sleep(0.25)
            print("Reset loop")

    # Copied in command interpreter, Should be in a utils file.
    def send(self, cmd, params):
        message = self.cmd_to_filename(cmd, params)
        sent = self.client.send(message)
        # the lostconnection message will get resent anyway, no need to clog up lanes by retrying here.
        while not sent and message != "lostconnection":
            print("Failed to send message, retrying.")
            print(message)
            sent = self.client.send(message)


    #Copied in command interpreter, Should be in a utils file.
    def filename_to_cmd(self, filename):
        cmd = filename.split("&")[0]
        params = filename.split("&")[1:]
        i = 0
        for param in params:
            params[i] = param
            i = i + 1
        return cmd, params

    #Copied in command interpreter, Should be in a utils file.
    def cmd_to_filename(self, cmd, params):
        filename = cmd
        i = 0
        for param in params:
            filename = filename + "&" + param
            i = i + 1
        return filename

class Watchdog:
    def __init__(self, folder):
        self.folder = folder
    def watch(self):
        announced_minute = []
        next_minute = 60
        time_since_cycled = 0
        while True:
            print("************************************************Watching")
            files = os.listdir(self.folder)
            for file in files:
                if "watchdog" in file:
                    try:
                        os.remove(os.path.join(self.folder, file))
                    except: # OSError?
                        print("Warning: Could not delete watchdog file.")
                    time_since_cycled = 0
            if next_minute < time_since_cycled and len(announced_minute) == next_minute/60-1:
                print(f"************************************************{time_since_cycled/60} minutes since watchdog reset. Restarting computer at 10 minutes.")
                announced_minute.append(1)
                next_minute += 60
            elif 20 < time_since_cycled:
                home = os.path.expanduser("~")
                with open(os.path.join(home, "watchdog_restart"), "w+") as f:
                    f.write("watched!")
                print("************************************************10 minutes since cycle, time for restart")
                time.sleep(30)
                os.system("shutdown /r /t 1")

            time.sleep(10)
            time_since_cycled += 10
