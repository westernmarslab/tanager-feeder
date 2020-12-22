class ChangeIPDialog(Dialog):


def __init__(self, controller, title, label, which_compy, config_loc, buttons={'ok': {}, 'cancel': {}},
             current_ip_address=''):
    super().__init__(controller, title, label, buttons, allow_exit=False, start_mainloop=False)
    self.entry_frame = Frame(self.top, bg=self.bg)
    self.entry_frame.pack(pady=(10, 20))

    frame = Frame(self.entry_frame, bg=self.bg)
    frame.pack(pady=(5, 5))
    change_label = Label(frame, text='IP address: ', fg=self.textcolor, bg=self.bg)
    change_label.pack(side=LEFT)
    self.ip_entry = Entry(frame, bg=self.entry_background, selectbackground=self.selectbackground,
                          selectforeground=self.selectforeground)
    if which_compy == 'spec compy':
        self.ip_entry.insert(0, SPEC_IP)
    else:
        self.ip_entry.insert(0, PI_IP)
    self.ip_entry.pack(side=LEFT)
    self.which_compy = which_compy
    self.config_loc = config_loc

    self.top.mainloop()


def ok(self):
    if self.which_compy == 'spec compy':
        if self.controller != None:
            self.controller.spec_server_ip = self.ip_entry.get()
        else:
            global SPEC_IP
            SPEC_IP = self.ip_entry.get()
    elif self.which_compy == 'pi':
        if self.controller != None:
            self.controller.pi_server_ip = self.ip_entry.get()
        else:
            global PI_IP
            PI_IP = self.ip_entry.get()

    with open(self.config_loc + 'ip_addresses.txt', 'w+') as f:
        print(self.config_loc)
        f.write(SPEC_IP + '\n')
        f.write(PI_IP)

    self.top.destroy()


def cancel(self):
    self.top.destroy()
