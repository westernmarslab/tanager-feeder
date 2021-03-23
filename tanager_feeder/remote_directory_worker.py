import time

from tanager_feeder import utils


class RemoteDirectoryWorker:
    def __init__(self, spec_commander, listener):
        self.spec_commander = spec_commander
        self.listener = listener
        self.timeout_s = utils.BUFFER

    def reset_timeout(self):
        self.timeout_s = utils.BUFFER

    def wait_for_contents(self, cmdfilename):
        # Wait to hear what the listener finds
        self.reset_timeout()
        while self.timeout_s > 0:
            # print('looking for '+cmdfilename)
            # If we get a file back with a list of the contents, replace the old listbox contents with new ones.
            # The cmdfilename should be e.g. listdir&R=+RiceData+Kathleen+spectral_data
            for item in self.listener.queue:
                print(cmdfilename)
                if cmdfilename in item:
                    contents = (
                        item.replace(
                            "+",
                            "\\",
                        )
                        .replace("=", ":")
                        .split("&")[2:]
                    )  # 0 is the command listcontents, 1 is the top level folder
                    self.listener.queue.remove(item)
                    return contents

                if "listdirfailed" in self.listener.queue:
                    self.listener.queue.remove("listdirfailed")
                    return "listdirfailed"

                if "listdirfailedpermission" in self.listener.queue:
                    self.listener.queue.remove("listdirfailedpermission")
                    return "listdirfailedpermission"

                if "listfilesfailed" in self.listener.queue:
                    self.listener.queue.remove("listfilesfailed")
                    return "listfilesfailed"

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL
        return "timeout"

    # Assume parent has already been validated, but don't assume it exists
    def get_dirs(self, parent):

        cmdfilename = self.spec_commander.listdir(parent)
        status = self.wait_for_contents(cmdfilename)
        return status

    def get_contents(self, parent):

        cmdfilename = self.spec_commander.list_contents(parent)
        return self.wait_for_contents(cmdfilename)

    def mkdir(self, newdir):
        self.spec_commander.mkdir(newdir)
        timeout = 2 * utils.BUFFER
        t = 0
        while t < timeout:
            for item in self.listener.queue:
                if item == "mkdirsuccess":
                    self.listener.queue.remove("mkdirsuccess")
                    return "mkdirsuccess"
                if item == "mkdirfailedfileexists":
                    self.listener.queue.remove("mkdirfailedfileexists")
                    return "mkdirfailedfileexists"
                if item == "mkdirfailedpermission":
                    self.listener.queue.remove("mkdirfailedpermission")
                    return "mkdirfailedpermission"
                if "mkdirfailed" in item:
                    self.listener.queue.remove(item)
                    return "mkdirfailed"

            time.sleep(utils.INTERVAL)
            t += utils.INTERVAL
        return "mkdirfailed"
