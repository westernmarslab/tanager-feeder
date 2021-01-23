import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class MotionHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title="Moving...",
        label="Moving...",
        buttons={"cancel": {}},
        timeout=90,
        new_sample_loc="foo",
        steps=False,
        destination=None,
    ):
        self.steps = steps
        self.listener = controller.pi_listener
        self.new_sample_loc = new_sample_loc
        self.destination = destination
        super().__init__(controller, title, label, timeout=timeout)

    def wait(self):
        print(self.listener)
        while self.timeout_s > 0:
            for item in self.listener.queue:
                if "donemoving" in item:
                    print("DONE MOVING!")
                    self.listener.queue.remove(item)
                    self.success()
                    return
                elif "failuremoving" in item:
                    self.listener.queue.remove(item)
                    self.interrupt("Failure moving...")
                    return
            if "nopiconfig" in self.listener.queue:
                print("nopiconfig")
                self.listener.queue.remove("nopiconfig")
                self.controller.set_manual_automatic(force=0)
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.timeout()

    def interrupt(self, label):
        if label == "Failure moving...":
            if "incidence" in self.label:
                super().interrupt("Error moving incidence.", retry=True)
            elif "emission" in self.label:
                super().interrupt("Error moving emission.", retry=True)
            elif "azimuth" in self.label:
                super().interrupt("Error moving azimuth.", retry=True)
            elif "tray" in self.label:
                super().interrupt("Error moving the sample tray.", retry=True)
        else:
            super().interrupt(label)

    def success(self):
        print("SUCCESS!")
        if "emission" in self.label:
            print("emission!")
            self.controller.angles_change_time = time.time()
            self.controller.motor_e = self.destination
            try:
                self.controller.log(
                    "Goniometer moved to an emission angle of " + str(self.controller.science_e) + " degrees."
                )
            except:
                self.controller.log("Emission set")
        elif "incidence" in self.label:
            self.controller.angles_change_time = time.time()
            self.controller.motor_i = self.destination
            try:
                self.controller.log(
                    "Goniometer moved to an incidence angle of " + str(self.controller.science_i) + " degrees."
                )
            except:
                self.controller.log("Incidence set")

        elif "azimuth" in self.label:
            self.controller.angles_change_time = time.time()
            self.controller.motor_az = self.destination
            try:
                self.controller.log(
                    "Goniometer moved to an azimuth angle of " + str(self.controller.science_az) + " degrees."
                )
            except:
                self.controller.log("Azimuth set")

        elif "tray" in self.label:
            try:
                x = (
                    self.steps
                )  # For some reason sometimes get an error saying MotionHandler has no attribute self.steps
            except:
                self.steps = False
            if self.steps == False:  # If we're specifying a position, not a number of motor steps
                self.controller.log("Sample tray moved to " + str(self.new_sample_loc) + " position.")
                try:
                    self.controller.sample_tray_index = self.controller.available_sample_positions.index(
                        self.new_sample_loc
                    )
                    self.controller.goniometer_view.set_current_sample(
                        self.controller.available_sample_positions[self.controller.sample_tray_index]
                    )

                except:
                    self.controller.sample_tray_index = -1  # White reference
                    self.controller.goniometer_view.set_current_sample("WR")
                samples_in_gui_order = []
                for var in self.controller.sample_pos_vars:
                    samples_in_gui_order.append(var.get())

                try:
                    i = samples_in_gui_order.index(self.new_sample_loc)
                    self.controller.current_sample_gui_index = i
                except:
                    self.controller.current_sample_gui_index = 0
                self.controller.current_label = self.controller.sample_label_entries[
                    self.controller.current_sample_gui_index
                ].get()
            else:  # If we specified steps, don't change the tray index, but still tell the goniometer view to change back from 'Moving'
                if self.controller.sample_tray_index > -1:
                    self.controller.goniometer_view.set_current_sample(
                        self.controller.available_sample_positions[self.controller.sample_tray_index]
                    )
                else:
                    self.controller.goniometer_view.set_current_sample("WR")

                self.controller.log("Sample tray moved " + str(self.new_sample_loc) + " steps.")
        else:
            self.controller.log("Something moved! Who knows what?")

        super().success()
