from tanager_feeder import utils


class RemoteDirectoryWorker:
    def __init__(self, spec_commander, listener):
        self.spec_commander = spec_commander
        self.listener = listener
        self.timeout_s = utils.BUFFER

    def reset_timeout(self):
        self.timeout_s = utils.BUFFER

    def wait_for_contents(self, cmdfilename):
        #         if self.wait_dialog==None

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

                elif "listdirfailed" in self.listener.queue:
                    self.listener.queue.remove("listdirfailed")
                    return "listdirfailed"

                elif "listdirfailedpermission" in self.listener.queue:
                    self.listener.queue.remove("listdirfailedpermission")
                    return "listdirfailedpermission"

                elif "listfilesfailed" in self.listener.queue:
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

        while True:
            if "mkdirsuccess" in self.listener.queue:
                self.listener.queue.remove("mkdirsuccess")
                return "mkdirsuccess"
            elif "mkdirfailedfileexists" in self.listener.queue:
                self.listener.queue.remove("mkdirfailedfileexists")
                return "mkdirfailedfileexists"
            elif "mkdirfailed" in self.listener.queue:
                self.listener.queue.remove("mkdirfailed")
                return "mkdirfailed"

        time.sleep(utils.INTERVAL)
