

from tanager_feeder.command_handlers.command_handler import CommandHandler
from typing import Optional, Dict


class TriggerRestartHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title: str = "Working...",
        label: str = "Working...",
        buttons: Optional[Dict] = None,
        timeout: int = 30,
    ):
        super().__init__(controller, title, label, buttons, timeout)

    def timeout(self, operation_string):
        if self.pause:
            self.interrupt(f"Error: Failed to {operation_string}.\n\nPaused.", retry=True)
            self.wait_dialog.top.geometry("376x175")
            self.controller.log(f"Error: Failed to {operation_string}.")
        elif self.cancel:
            self.interrupt(f"Error: Failed to {operation_string}.\n\nData acquisition canceled.", retry=False)
            self.wait_dialog.top.geometry("376x175")
            # Does nothing in automatic mode
            self.controller.clear()
        else:
            self.controller.log(
                f"Error: Failed to {operation_string}. Restarting spectrometer computer and retrying."
            )
            self.controller.queue.insert(0, {self.controller.restart_computer: []})
            self.controller.next_in_queue()

