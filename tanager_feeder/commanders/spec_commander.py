import time
from typing import Optional

from tanager_feeder.commanders.commander import Commander


class SpecCommander(Commander):
    def take_spectrum(
        self, path: str, basename: str, num: int, label: str, i: Optional[int], e: Optional[int], az: Optional[int]
    ):
        self.remove_from_listener_queue(
            ["nonumspectra", "noconfig", "savedfile", "failedtosavefile", "savespecfailedfileexists"]
        )

        if i is None:
            i = ""
        if e is None:
            e = ""
        if az is None:
            az = ""

        filename = self.encrypt("spectrum", [path, basename, num, label, i, e, az])
        self.send(filename)
        return filename

    def white_reference(self):
        self.remove_from_listener_queue(["nonumspectra", "noconfig", "wrsuccess", "wrfailedfileexists", "wrfailed"])
        filename = self.encrypt("wr")
        self.send(filename)
        return filename

    def optimize(self):
        self.remove_from_listener_queue(["nonumspectra", "optsuccess", "optfailure"])
        filename = self.encrypt("opt")
        self.send(filename)
        return filename

    def restart_computer(self):
        self.remove_from_listener_queue(["restarting"])
        filename = self.encrypt("restartcomputer")
        self.send(filename)
        return filename

    def restart_rs3(self):
        self.remove_from_listener_queue(["rs3restarted"])
        filename = self.encrypt("restartrs3")
        self.send(filename)
        return filename

    def set_save_path(self, path: str, basename: str, startnum: int):
        self.remove_from_listener_queue(
            [
                "saveconfigsuccess",
                "donelookingforunexpected",
                "saveconfigfailed",
                "saveconfigfailedfileexists",
                "saveconfigerror",
            ]
        )
        filename = self.encrypt("saveconfig", [path, basename, startnum])
        self.send(filename)
        return filename

    def configure_instrument(self, number: int):
        self.remove_from_listener_queue(["iconfigsuccess", "iconfigfailure"])
        filename = self.encrypt("instrumentconfig", [number])
        self.send(filename)
        return filename

    def listdir(self, parent: str):
        self.remove_from_listener_queue(["listdirfailedpermission", "listdirfailed"])
        filename = self.encrypt("listdir", parameters=[parent])
        self.send(filename)
        return filename

    def list_contents(self, parent: str):
        self.remove_from_listener_queue(["listdirfailedpermission", "listfilesfailed", "listdirfailed"])
        filename = self.encrypt("listcontents", parameters=[parent])
        self.send(filename)
        return filename

    def check_writeable(self, check_dir: str):
        self.remove_from_listener_queue(["yeswriteable", "notwriteable"])
        filename = self.encrypt("checkwriteable", [check_dir])
        self.send(filename)
        return filename

    def mkdir(self, newdir: str):
        self.remove_from_listener_queue(["mkdirsuccess", "mkdirfailedfileexists", "mkdirfailed"])
        filename = self.encrypt("mkdir", [newdir])
        self.send(filename)
        return filename

    def delete_spec(self, savedir: str, basename: str, num: int):
        self.remove_from_listener_queue(["rmsuccess", "rmfailure"])
        filename = self.encrypt("rmfile", [savedir, basename, num])
        self.send(filename)
        return filename

    def transfer_data(self, source: str):
        self.remove_from_listener_queue(["datatransfercomplete", "datafailure", "batch"])
        filename = self.encrypt("transferdata", parameters=[source])
        self.send(filename)
        return filename

    def process(self, input_dir: str, output_dir: str, output_file: str):
        self.remove_from_listener_queue(
            [
                "processsuccess",
                "processerrorfileexists",
                "processerrorwropt",
                "processerror",
                "processsuccess1unknownsample",
                "processsuccessunknownsamples",
                "spec_data",
                "log_data",
            ]
        )
        filename = self.encrypt("process", [input_dir, output_dir, output_file])
        self.send(filename)
        return filename

    def send(self, message: str):
        sent = False
        attempt = 1
        while sent is False and attempt < 10:
            sent = self.connection_manager.send_to_spec(message)
            attempt += 1
            if not sent:
                print(f"Retrying command {message}")
                time.sleep(4)
        if not sent:
            print(f"Failed to send command {message}")
        else:
            print(f"Sent {message}")
        return sent