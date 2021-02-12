import time
from typing import Optional

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class ProcessHandler(CommandHandler):
    def __init__(self, controller, title: str = "Processing...", label: str = "Processing..."):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=20000 + utils.BUFFER)
        self.outputfile = self.controller.output_file_entry.get()
        output_dir = self.controller.output_dir_entry.get()
        if (
            self.controller.opsys == "Linux" or self.controller.opsys == "Mac"
        ) and self.controller.plot_local_remote == "local":
            if output_dir[-1] != "/":
                output_dir += "/"
        else:
            output_dir = output_dir.replace("/", "\\")
            if output_dir[-1] != "\\":
                output_dir += "\\"
        self.outputfile = output_dir + self.outputfile
        self.wait_dialog.set_buttons({})
        self.wait_dialog.top.wm_geometry("376x130")
        # Normally we have a pause and a cancel option if there are additional items in the queue, but it doesn't
        # make much sense to pause processing halfway through, so let's just not have the option.

    def wait(self):
        # TODO: add cancel option to processing.
        while True:  # self.timeout_s>0: Never going to timeout

            if (
                "processsuccess" in self.listener.queue
                or "processsuccessnocorrection" in self.listener.queue
                or "processsuccessnolog" in self.listener.queue
            ):
                warnings: Optional[str] = None
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

                self.controller.log("Files processed. " + warnings.replace("\n", " ") + "\n\t" + self.outputfile)
                if (
                    self.controller.proc_local_remote == "local"
                ):  # Move on to finishing the process by writing the data to its final destination
                    self.controller.complete_queue_item()
                    self.controller.next_in_queue()
                    self.success()
                    if warnings != "":
                        self.wait_dialog.top.wm_geometry("376x185")

                else:  # if the final destination was remote then we're already done.

                    if warnings != "":
                        self.success(warnings=warnings)
                        self.wait_dialog.top.wm_geometry("376x185")
                    else:
                        self.success()
                return

            if "processerrorfileexists" in self.listener.queue:

                self.listener.queue.remove("processerrorfileexists")
                self.interrupt("Error processing files: Output file already exists")
                self.controller.log("Error processing files: output file exists.")
                return

            if "processerrornodirectory" in self.listener.queue:

                self.listener.queue.remove("processerrornodirectory")
                self.interrupt("Error processing files:\nInput directory does not exist.")
                self.controller.log("Error processing files: Input directory does not exist.")
                return

            if "processerrorwropt" in self.listener.queue:

                self.listener.queue.remove("processerrorwropt")
                self.interrupt(
                    "Error processing files.\n\nDid you optimize and white reference before collecting data?"
                )
                self.wait_dialog.top.wm_geometry("376x150")
                self.controller.log("Error processing files")
                return

            if "processerror" in self.listener.queue:

                self.listener.queue.remove("processerror")
                self.wait_dialog.top.wm_geometry("376x175")
                self.interrupt("Error processing files.\n\nIs ViewSpecPro running? Do directories exist?", retry=True)
                self.controller.log("Error processing files")
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.timeout()

    def success(self, warnings: Optional[str] = None):

        interrupt_string = "Data processed successfully"
        if warnings:
            interrupt_string += "\n\n" + warnings
        self.interrupt(interrupt_string)
        self.controller.plot_input_file = self.outputfile

        if self.controller.proc_local_remote == "remote":
            self.controller.plot_local_remote = "remote"
        else:
            self.controller.plot_local_remote = "local"

        if warnings != "":
            self.wait_dialog.top.wm_geometry("376x130")
        else:
            self.wait_dialog.top.wm_geometry("376x100")

        while len(self.controller.queue) > 0:
            self.controller.complete_queue_item()
        self.controller.process_top.destroy()
        self.wait_dialog.top.lift()
