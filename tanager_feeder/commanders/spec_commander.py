from typing import Optional

from tanager_feeder.commanders.commander import Commander


class SpecCommander(Commander):
    def __init__(self, connection_tracker, listener):
        super().__init__(connection_tracker.spec_ip, listener)
        self.connection_tracker = connection_tracker

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

    def transfer_data(self, source: str, temp_destination_dir: str, temp_destination_file: str):
        self.remove_from_listener_queue(["datacopied", "datafailure"])
        filename = self.encrypt("transferdata", parameters=[source, temp_destination_dir, temp_destination_file])
        self.send(filename)
        return filename

    # TODO: does this need to be deleted or implemented?
    # def send_data(self, source,destination)
    #     self.remove_from_listener_queue(['datareceived','datafailure'])
    #     filename=self.encrypt('getdata',parameters=[source,destination])
    #     self.send(filename)
    #     return filename

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

    def send(self, filename):
        return super().send(filename, self.connection_tracker.SPEC_PORT, self.connection_tracker.spec_offline)
