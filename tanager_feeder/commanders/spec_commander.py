class SpecCommander(Commander):
    def __init__(self, server_ip, listener):
        super().__init__(server_ip, listener)

    def take_spectrum(self, path, basename, num, label, i, e, az):
        self.remove_from_listener_queue(
            ['nonumspectra', 'noconfig', 'savedfile', 'failedtosavefile', 'savespecfailedfileexists'])

        if i == None: i = ''
        if e == None: e = ''
        filename = self.encrypt('spectrum', [path, basename, num, label, i, e, az])
        self.send(filename)
        return filename

    def white_reference(self):
        self.remove_from_listener_queue(['nonumspectra', 'noconfig', 'wrsuccess', 'wrfailedfileexists', 'wrfailed'])
        filename = self.encrypt('wr')
        self.send(filename)
        return filename

    def optimize(self):
        self.remove_from_listener_queue(['nonumspectra', 'optsuccess', 'optfailure'])
        filename = self.encrypt('opt')
        self.send(filename)
        return filename

    def set_save_path(self, path, basename, startnum):
        self.remove_from_listener_queue(
            ['saveconfigsuccess', 'donelookingforunexpected', 'saveconfigfailed', 'saveconfigfailedfileexists',
             'saveconfigerror'])
        filename = self.encrypt('saveconfig', [path, basename, startnum])
        self.send(filename)
        return filename

    def configure_instrument(self, number):
        self.remove_from_listener_queue(['iconfigsuccess', 'iconfigfailure'])
        filename = self.encrypt('instrumentconfig', [number])
        self.send(filename)
        return filename

    def listdir(self, parent):
        self.remove_from_listener_queue(['listdirfailedpermission', 'listdirfailed'])
        filename = self.encrypt('listdir', parameters=[parent])
        self.send(filename)
        return filename

    def list_contents(self, parent):
        self.remove_from_listener_queue(['listdirfailedpermission', 'listfilesfailed', 'listdirfailed'])
        filename = self.encrypt('listcontents', parameters=[parent])
        self.send(filename)
        return filename

    def check_writeable(self, dir):
        self.remove_from_listener_queue(['yeswriteable', 'notwriteable'])
        filename = self.encrypt('checkwriteable', [dir])
        self.send(filename)
        return filename

    def mkdir(self, newdir):
        self.remove_from_listener_queue(['mkdirsuccess', 'mkdirfailedfileexists', 'mkdirfailed'])
        filename = self.encrypt('mkdir', [newdir])
        self.send(filename)
        return filename

    def delete_spec(self, savedir, basename, num):
        self.remove_from_listener_queue(['rmsuccess', 'rmfailure'])
        filename = self.encrypt('rmfile', [savedir, basename, num])
        self.send(filename)
        return filename

    def transfer_data(self, source, temp_destination_dir, temp_destination_file):
        self.remove_from_listener_queue(['datacopied', 'datafailure'])
        filename = self.encrypt('transferdata', parameters=[source, temp_destination_dir, temp_destination_file])
        self.send(filename)
        return filename

    # def send_data(self, source,destination)
    #     self.remove_from_listener_queue(['datareceived','datafailure'])
    #     filename=self.encrypt('getdata',parameters=[source,destination])
    #     self.send(filename)
    #     return filename

    def process(self, input_dir, output_dir, output_file):
        self.remove_from_listener_queue(
            ['processsuccess', 'processerrorfileexists', 'processerrorwropt', 'processerror',
             'processsuccess1unknownsample', 'processsuccessunknownsamples', 'spec_data', 'log_data'])
        filename = self.encrypt('process', [input_dir, output_dir, output_file])
        self.send(filename)
        return filename

    def send(self, filename):
        super().send(filename, SPEC_PORT)