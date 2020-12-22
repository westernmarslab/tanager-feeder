class RemoteFileExplorer(Dialog):
    def __init__(self, controller, target=None, title='Select a directory', label='Select a directory',
                 buttons={'ok': {}, 'cancel': {}}, directories_only=True):

        super().__init__(controller, title=title, buttons=buttons, label=label, button_width=20)

        self.timeout_s = BUFFER
        self.controller = controller
        self.remote_directory_worker = self.controller.remote_directory_worker
        self.listener = self.controller.spec_listener
        self.target = target
        self.current_parent = None
        self.directories_only = directories_only

        self.nav_frame = Frame(self.top, bg=self.bg)
        self.nav_frame.pack()
        self.new_button = Button(self.nav_frame, fg=self.textcolor, text='New Folder', command=self.askfornewdir,
                                 width=10)
        self.new_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                               bg=self.buttonbackgroundcolor)
        self.new_button.pack(side=RIGHT, pady=(5, 5), padx=(0, 10))

        self.path_entry_var = StringVar()
        self.path_entry_var.trace('w', self.validate_path_entry_input)
        self.path_entry = Entry(self.nav_frame, width=50, bg=self.entry_background, textvariable=self.path_entry_var,
                                selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.path_entry.pack(padx=(5, 5), pady=(5, 5), side=RIGHT)
        self.back_button = Button(self.nav_frame, fg=self.textcolor, text='<-', command=self.back, width=1)
        self.back_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                bg=self.buttonbackgroundcolor)
        self.back_button.pack(side=RIGHT, pady=(5, 5), padx=(10, 0))

        self.listbox = ScrollableListbox(self.top, self.bg, self.entry_background, self.listboxhighlightcolor, )
        self.listbox.bind("<Double-Button-1>", self.expand)
        self.path_entry.bind('<Return>', self.go_to_path)

        if target.get() == '':
            self.expand(newparent='C:\\Users')
            self.current_parent = 'C:\\Users'
        else:
            if directories_only:
                self.expand(newparent=target.get().replace('/', '\\'))
            else:
                path = target.get().replace('/', '\\')
                if '\\' in path:
                    path_el = path.split('\\')
                    if '.' in path_el[-1]:
                        path = '\\'.join(path_el[:-1])
                    self.expand(newparent=path)
                else:
                    self.expand(newparent=path)

    def validate_path_entry_input(self, *args):
        text = self.path_entry.get()
        text = rm_reserved_chars(text)

        self.path_entry.delete(0, 'end')
        self.path_entry.insert(0, text)

    def askfornewdir(self):
        input_dialog = NewDirDialog(self.controller, self)

    def mkdir(self, newdir):
        status = self.remote_directory_worker.mkdir(newdir)

        if status == 'mkdirsuccess':
            self.expand(None, '\\'.join(newdir.split('\\')[0:-1]))
            self.select(newdir.split('\\')[-1])
        elif status == 'mkdirfailedfileexists':
            dialog = ErrorDialog(self.controller, title='Error',
                                 label='Could not create directory:\n\n' + newdir + '\n\nFile exists.')
            self.expand(newparent=self.current_parent)
        elif status == 'mkdirfailed':
            dialog = ErrorDialog(self.controller, title='Error', label='Could not create directory:\n\n' + newdir)
            self.expand(newparent=self.current_parent)

    def back(self):
        if len(self.current_parent) < 4:
            return
        parent = '\\'.join(self.current_parent.split('\\')[0:-1])
        self.expand(newparent=parent)

    def go_to_path(self, source):
        parent = self.path_entry.get().replace('/', '\\')
        self.path_entry.delete(0, 'end')
        self.expand(newparent=parent)

    def expand(self, source=None, newparent=None, buttons=None, select=None, timeout=5, destroy=False):

        if newparent == None:
            index = self.listbox.curselection()[0]
            if self.listbox.itemcget(index, 'foreground') == 'darkblue':
                return
            newparent = self.current_parent + '\\' + self.listbox.get(index)
        if newparent[1:2] != ':' or len(newparent) > 2 and newparent[1:3] != ':\\':
            dialog = ErrorDialog(self.controller, title='Error: Invalid input',
                                 label='Error: Invalid input.\n\n' + newparent + '\n\nis not a valid filename.')
            if self.current_parent == None:
                self.expand(newparent='C:\\Users')
            return
        if newparent[-1] == '\\':
            newparent = newparent[:-1]
        # Send a command to the spec compy asking it for directory contents
        if self.directories_only == True:
            status = self.remote_directory_worker.get_contents(newparent)
        else:
            status = self.remote_directory_worker.get_contents(newparent)

        # if we succeeded, the status will be a list of the contents of the directory
        if type(status) == list:

            self.listbox.delete(0, 'end')
            for dir in status:
                if dir[0:2] == '~:':
                    self.listbox.insert(END, dir[2:])
                    self.listbox.itemconfig(END, fg='darkblue')
                else:
                    self.listbox.insert(END, dir)
            self.current_parent = newparent

            self.path_entry.delete(0, 'end')
            self.path_entry.insert('end', newparent)
            if select != None:
                self.select(select)

            if destroy:
                self.close()


        elif status == 'listdirfailed':
            if self.current_parent == None:
                #                 print('setting to RiceData')
                #                 self.current_parent='R:\\RiceData'
                #                 self.expand(newparent='C:\\Users')
                self.current_parent = 'C:\\Users'
                # self.current_parent='\\'.join(newparent.split('\\')[:-1])
                # if self.current_parent=='':
                #     self.current_parent='C:\\Users'
            if buttons == None:
                buttons = {
                    'yes': {
                        self.mkdir: [newparent]
                    },
                    'no': {
                        self.expand: [None, self.current_parent]
                    }
                }
            dialog = ErrorDialog(self.controller, title='Error',
                                 label=newparent + '\ndoes not exist. Do you want to create this directory?',
                                 buttons=buttons)
            return
        elif status == 'listdirfailedpermission':
            dialog = ErrorDialog(self.controller, label='Error: Permission denied for\n' + newparent)
            return
        elif status == 'timeout':
            dialog = ErrorDialog(self.controller,
                                 label='Error: Operation timed out.\nCheck that the automation script is running on the spectrometer computer.')
            self.cancel()

    def select(self, text):
        if '\\' in text:
            text = text.split('\\')[0]

        try:
            index = self.listbox.get(0, 'end').index(text)
        except:
            # time.sleep(0.5)
            print('except')
            # self.select(text)
            index = 0

        self.listbox.selection_set(index)
        self.listbox.see(index)

    def ok(self):
        index = self.listbox.curselection()
        if len(index) > 0 and self.directories_only:
            if self.listbox.itemcget(index[0], 'foreground') == 'darkblue':
                index = []
        elif len(index) == 0 and not self.directories_only:
            return

        self.target.delete(0, 'end')

        if self.directories_only:
            if len(index) > 0 and self.path_entry.get() == self.current_parent:
                self.controller.unfreeze()
                self.target.delete(0, 'end')
                self.target.insert(0, self.current_parent + '\\' + self.listbox.get(index[0]))
                self.close()
            elif self.path_entry.get() == self.current_parent:
                self.controller.unfreeze()
                self.target.delete(0, 'end')
                self.target.insert(0, self.current_parent)
                self.close()
            else:
                buttons = {
                    'yes': {
                        self.mkdir: [self.path_entry.get()],
                        self.expand: [None, '\\'.join(self.path_entry.get().split('\\')[0:-1])],
                        self.select: [self.path_entry.get().split('\\')[-1]],
                        self.ok: []
                    },
                    'no': {
                    }
                }
                self.expand(newparent=self.path_entry.get(), buttons=buttons, destroy=True)
                self.controller.unfreeze()
                self.target.delete(0, 'end')
                self.target.insert(0, self.current_parent)

        else:
            if len(
                    self.listbox.curselection()) > 0 and self.path_entry.get() == self.current_parent and self.listbox.itemcget(
                    index[0], 'foreground') == 'darkblue':
                self.controller.unfreeze()
                self.target.delete(0, 'end')
                self.target.insert(0, self.current_parent + '\\' + self.listbox.get(index[0]))
                self.close()