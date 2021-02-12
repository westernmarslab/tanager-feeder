from threading import Thread
import time

import playsound

from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.wait_dialog import WaitDialog


class CommandHandler:
    def __init__(self, controller, title="Working...", label="Working...", buttons=None, timeout=30):
        if buttons is None:
            buttons = {}
        self.controller = controller
        self.text_only = self.controller.text_only
        self.label = label
        self.title = title
        # Either update the existing wait dialog, or make a new one.
        try:
            self.controller.wait_dialog.reset(title=title, label=label, buttons=buttons)
        # pylint: disable = broad-except
        except Exception as e:
            print(e)
            # TODO: figure out what kind of exception happens if there is no wait dialog.
            self.controller.wait_dialog = WaitDialog(controller, title, label)
        self.wait_dialog = self.controller.wait_dialog
        self.controller.freeze()

        if len(self.controller.queue) > 1:
            buttons = {"pause": {self.pause_function: []}, "cancel_queue": {self.cancel_function: []}}
            self.wait_dialog.set_buttons(buttons)
        else:
            self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))

        # We'll keep track of elapsed time so we can cancel the operation if it takes too long

        self.timeout_s = timeout

        # The user can pause or cancel if we're executing a list of commands.
        self.pause = False
        self.cancel = False

        # A Listener object is always running a loop in a separate thread. It  listens for files dropped into a
        # command folder and changes its attributes based on what it finds.
        self.timeout_s = timeout

        # Start the wait function, which will watch the listener to see what attributes change and react accordingly.
        # If this isn't in its own thread, the dialog box doesn't pop up until after it completes.
        self.thread = Thread(target=self.wait)
        self.thread.start()

    @property
    def timeout_s(self):
        return self.__timeout_s

    @timeout_s.setter
    def timeout_s(self, val):
        self.__timeout_s = val

    def wait(self):
        while True:
            print("waiting in super...")
            self.timeout_s -= 1
            if self.timeout_s < 0:
                self.timeout()
            time.sleep(1)

    def timeout(self, log_string=None, retry=True, dialog=True, dialog_string="Error: Operation timed out"):
        if self.text_only:
            self.controller.script_failed = True
        if log_string is None:
            self.controller.log("Error: Operation timed out")
        else:
            self.controller.log(log_string)
        if dialog:
            self.wait_dialog.interrupt(dialog_string)
            if retry:
                buttons = {"retry": {self.controller.next_in_queue: []}, "cancel": {self.finish: []}}
                self.wait_dialog.set_buttons(buttons)

    def finish(self):
        self.controller.reset()
        self.wait_dialog.close()

    def pause_function(self):
        self.pause = True
        self.wait_dialog.label = "Pausing after command completes..."

    def cancel_function(self):
        self.cancel = True
        self.controller.reset()
        self.wait_dialog.label = "Canceling..."

    def interrupt(self, label, info_string=None, retry=False):
        self.wait_dialog.interrupt(label)
        if info_string != None:
            self.controller.log(info_string)
        if retry:
            buttons = {"retry": {self.controller.next_in_queue: []}, "cancel": {self.finish: []}}
            self.wait_dialog.set_buttons(buttons)
        self.controller.freeze()
        try:
            self.wait_dialog.ok_button.focus_set()
        # pylint: disable=broad-except
        except Exception as e:
            # TODO: figure out type of exception.
            print(e)
            self.wait_dialog.top.focus_set()

        if self.controller.audio_signals:
            if "Success" in label:
                playsound.playsound("beep.wav")
            else:
                playsound.playsound("broken.wav")

    def remove_retry(self, need_new=True):
        if need_new:
            self.controller.wait_dialog = None
        removed = self.controller.rm_current()
        if removed:
            numstr = str(self.controller.spec_num)
            if numstr == "None":
                numstr = self.controller.spec_startnum_entry.get()
            while len(numstr) < utils.NUMLEN:
                numstr = "0" + numstr
            self.controller.log(
                "Warning: overwriting "
                + self.controller.spec_save_path
                + "\\"
                + self.controller.spec_basename
                + numstr
                + ".asd."
            )

            # If we are retrying taking a spectrum or white references, don't do input checks again.
            if self.controller.take_spectrum in self.controller.queue[0]:
                garbage = self.controller.queue[0][self.controller.take_spectrum][2]
                self.controller.queue[0] = {self.controller.take_spectrum: [True, True, garbage]}

            elif self.controller.wr in self.controller.queue[0]:
                self.controller.queue[0] = {self.controller.wr: [True, True]}
            self.controller.next_in_queue()
        else:
            ErrorDialog(
                self.controller,
                label="Error: Failed to remove file. Choose a different base name,\nspectrum number, or save"
                 " directory and try again.",
            )

    def success(self, close=True):
        try:
            self.controller.complete_queue_item()
        except Exception as e:
            print(e)
            print("canceled by user?")

        if self.cancel:
            self.interrupt("Canceled.")
            self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))
            self.controller.reset()
        elif self.pause:
            buttons = {"continue": {self.controller.next_in_queue: []}, "cancel": {self.finish: []}}
            self.interrupt("Paused.")
            self.wait_dialog.set_buttons(buttons)
        elif len(self.controller.queue) > 0:
            print(self.controller.queue)
            self.controller.next_in_queue()
        elif self.controller.script_running:
            self.controller.log("Success!")
            self.controller.script_running = False
            self.finish()
        else:
            self.controller.reset()
            self.interrupt("Success!")

    def set_text(self, widget, text):
        state = widget.cget("state")
        widget.configure(state="normal")
        widget.delete(0, "end")
        widget.insert(0, text)
        widget.configure(state=state)
