import time

from tkinter import TclError

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class ProcessHandler(CommandHandler):
    def __init__(self, controller, destination: str, title: str = "Processing...", label: str = "Processing..."):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=20000 + utils.BUFFER)
        self.outputfile = destination
        # self.wait_dialog.set_buttons({"cancel": {self.cancel_process: []}})
        self.wait_dialog.top.wm_geometry("376x130")
        # Normally we have a pause and a cancel option if there are additional items in the queue, but it doesn't
        # make much sense to pause processing halfway through, so let's just not have the option.

    def cancel_process(self):
        print("cancel function!")
        self.interrupt("Operation canceled.")
        self.controller.reset()
        print(self.controller.queue)

    def cancel_function(self):
        self.cancel = True
        self.interrupt("Operation canceled.")
        self.controller.reset()
        self.wait_dialog.label = "Canceled."

    def wait(self):
        while True:  # self.timeout_s>0: Never going to timeout
            if (
                "processsuccess" in self.listener.queue
                or "processsuccessnocorrection" in self.listener.queue
                or "processsuccessnolog" in self.listener.queue
            ):
                warnings: str = ""
                if "processsuccess" in self.listener.queue:
                    self.listener.queue.remove("processsuccess")
                if "processsuccessnolog" in self.listener.queue:
                    self.listener.queue.remove("processsuccessnolog")
                    warnings = "No log found in data directory.\n First line of log file should be  #AutoSpec log"
                if "processsuccessnocorrection" in self.listener.queue:
                    self.listener.queue.remove("processsuccessnocorrection")
                    warnings = "Correction for non-Lambertian properties of\nSpectralon was not applied."
                if "." not in self.outputfile:
                    self.outputfile += ".csv"

                if self.controller.process_manager.proc_local_remote == "local":
                    # Move on to finishing the process by transferring the data from remote to local
                    if warnings != "":
                        self.controller.log("Files processed. \n" + warnings.replace("\n", " "))
                    else:
                        self.controller.log("Files processed.")
                else:  # if the final destination was remote then we're already done.
                    if warnings != "":
                        self.controller.log(
                            "Files processed. \n" + warnings.replace("\n", " ") + "\n" + self.outputfile
                        )
                    else:
                        self.controller.log("Files processed.\n" + self.outputfile)
                self.success(warnings)
                return

            if "processerrorfileexists" in self.listener.queue:

                self.listener.queue.remove("processerrorfileexists")
                self.interrupt("Error processing files: Output file already exists")
                self.controller.log("Error processing files: output file exists.")
                self.complete_queue_items()
                return

            if "processerrornodirectory" in self.listener.queue:

                self.listener.queue.remove("processerrornodirectory")
                self.interrupt("Error processing files.\n\nInput directory does not exist.")
                self.wait_dialog.top.wm_geometry("376x165")
                self.controller.log("Error processing files: Input directory does not exist.")
                self.complete_queue_items()
                return

            if "processerrorwropt" in self.listener.queue:

                self.listener.queue.remove("processerrorwropt")
                self.wait_dialog.top.wm_geometry("376x165")
                self.interrupt(
                    "Error processing files.\n\nDid you optimize and white reference before collecting data?"
                )
                self.controller.log("Error processing files")
                self.complete_queue_items()
                return
            if "processerrorcannotwrite" in self.listener.queue:
                self.listener.queue.remove("processerrorcannotwrite")
                self.wait_dialog.top.wm_geometry("376x165")
                self.wait_dialog.top.wm_geometry("376x165")
                self.interrupt("Error processing files.\n\nDo you have access to the source folder?")
                self.controller.log("Error processing files")
                self.complete_queue_items()

                return
            if "processerror" in self.listener.queue:
                self.listener.queue.remove("processerror")
                try:
                    self.wait_dialog.top.wm_geometry("376x175")
                except TclError:
                    print("TclError")
                    pass
                self.interrupt("Error processing files.\n\nIs ViewSpecPro running? Do directories exist?")
                self.controller.log("Error processing files")
                self.complete_queue_items()
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.timeout()

    def complete_queue_items(self):
        for i, item in enumerate(self.controller.queue):
            if i > 1:
                break
            elif item in [self.controller.process_cmd, self.controller.finish_process]:
                self.controller.complete_queue_item()
        print(self.controller.queue)


    def success(self, warnings: str = ""):
        self.controller.plot_manager.plot_input_file = self.outputfile

        if self.controller.process_manager.proc_local_remote == "remote":
            self.controller.process_manager.plot_local_remote = "remote"
        else:
            self.controller.plot_manager.plot_local_remote = "local"
        try:
            if warnings != "":
                self.wait_dialog.top.wm_geometry("376x130")
            else:
                self.wait_dialog.top.wm_geometry("376x100")
        except TclError:
            pass

        self.controller.process_manager.process_top.destroy()

        interrupt_string = "Data processed successfully"
        if warnings:
            interrupt_string += "\n\n" + warnings

        super().success(interrupt_string)
