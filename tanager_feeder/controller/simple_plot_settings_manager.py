
        def open_options(self, tab, current_title):

            def select_tab():
                self.view_notebook.select(tab.top)

            buttons = {
                'ok': {
                    select_tab: [],
                    lambda: tab.set_title(self.new_plot_title_entry.get()): []
                }
            }

            def apply_x():
                self.view_notebook.select(tab.top)

                try:
                    x1 = float(self.left_zoom_entry.get())
                    x2 = float(self.right_zoom_entry.get())
                    tab.adjust_x(x1, x2)
                except:
                    ErrorDialog(self, title='Invalid Zoom Range',
                                label='Error: Invalid x limits: ' + self.left_zoom_entry.get() + ', ' + self.right_zoom_entry.get())

            def apply_y():
                self.view_notebook.select(tab.top)
                try:
                    y1 = float(self.left_zoom_entry2.get())
                    y2 = float(self.right_zoom_entry2.get())
                    tab.adjust_y(y1, y2)
                except Exception as e:
                    print(e)
                    ErrorDialog(self, title='Invalid Zoom Range',
                                label='Error! Invalid y limits: ' + self.left_zoom_entry2.get() + ', ' + self.right_zoom_entry2.get())

            def apply_z():
                self.view_notebook.select(tab.top)

                try:
                    z1 = float(self.left_zoom_entry_z.get())
                    z2 = float(self.right_zoom_entry_z.get())
                    tab.adjust_z(z1, z2)
                except Exception as e:
                    print(e)
                    ErrorDialog(self, title='Invalid Zoom Range',
                                label='Error: Invalid z limits: ' + self.left_zoom_entry.get() + ', ' + self.right_zoom_entry.get())

            self.plot_options_dialog = Dialog(self, 'Plot Options', '\nPlot title:', buttons=buttons)
            self.new_plot_title_entry = Entry(self.plot_options_dialog.top, width=20, bd=self.bd,
                                              bg=self.entry_background, selectbackground=self.selectbackground,
                                              selectforeground=self.selectforeground)
            self.new_plot_title_entry.insert(0, current_title)
            self.new_plot_title_entry.pack()

            self.outer_outer_zoom_frame = Frame(self.plot_options_dialog.top, bg=self.bg, padx=self.padx, pady=15)
            self.outer_outer_zoom_frame.pack(expand=True, fill=BOTH)

            self.zoom_title_frame = Frame(self.outer_outer_zoom_frame, bg=self.bg)
            self.zoom_title_frame.pack(pady=(5, 10))
            self.zoom_title_label = Label(self.zoom_title_frame, text='Adjust plot x and y limits:', bg=self.bg,
                                          fg=self.textcolor)
            self.zoom_title_label.pack(side=LEFT, pady=(0, 4))

            self.outer_zoom_frame = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
            self.outer_zoom_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
            self.zoom_frame = Frame(self.outer_zoom_frame, bg=self.bg, padx=self.padx)
            self.zoom_frame.pack()

            self.zoom_label = Label(self.zoom_frame, text='x1:', bg=self.bg, fg=self.textcolor)
            self.left_zoom_entry = Entry(self.zoom_frame, width=7, bd=self.bd, bg=self.entry_background,
                                         selectbackground=self.selectbackground, selectforeground=self.selectforeground)
            self.zoom_label2 = Label(self.zoom_frame, text='x2:', bg=self.bg, fg=self.textcolor)
            self.right_zoom_entry = Entry(self.zoom_frame, width=7, bd=self.bd, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground)
            self.zoom_button = Button(self.zoom_frame, text='Apply', command=apply_x, width=7, fg=self.buttontextcolor,
                                      bg=self.buttonbackgroundcolor, bd=self.bd)
            self.zoom_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                    bg=self.buttonbackgroundcolor)
            self.zoom_button.pack(side=RIGHT, padx=(10, 10))
            self.right_zoom_entry.pack(side=RIGHT, padx=self.padx)
            self.zoom_label2.pack(side=RIGHT, padx=self.padx)
            self.left_zoom_entry.pack(side=RIGHT, padx=self.padx)
            self.zoom_label.pack(side=RIGHT, padx=self.padx)

            self.outer_zoom_frame2 = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
            self.outer_zoom_frame2.pack(expand=True, fill=BOTH, pady=(0, 10))
            self.zoom_frame2 = Frame(self.outer_zoom_frame2, bg=self.bg, padx=self.padx)
            self.zoom_frame2.pack()
            self.zoom_label3 = Label(self.zoom_frame2, text='y1:', bg=self.bg, fg=self.textcolor)
            self.left_zoom_entry2 = Entry(self.zoom_frame2, width=7, bd=self.bd, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground)
            self.zoom_label4 = Label(self.zoom_frame2, text='y2:', bg=self.bg, fg=self.textcolor)
            self.right_zoom_entry2 = Entry(self.zoom_frame2, width=7, bd=self.bd, bg=self.entry_background,
                                           selectbackground=self.selectbackground,
                                           selectforeground=self.selectforeground)
            self.zoom_button2 = Button(self.zoom_frame2, text='Apply', command=apply_y, width=7,
                                       fg=self.buttontextcolor, bg=self.buttonbackgroundcolor, bd=self.bd)
            self.zoom_button2.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                     bg=self.buttonbackgroundcolor)

            self.zoom_button2.pack(side=RIGHT, padx=(10, 10))
            self.right_zoom_entry2.pack(side=RIGHT, padx=self.padx)
            self.zoom_label4.pack(side=RIGHT, padx=self.padx)
            self.left_zoom_entry2.pack(side=RIGHT, padx=self.padx)
            self.zoom_label3.pack(side=RIGHT, padx=self.padx)

            self.outer_zoom_frame_z = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
            self.outer_zoom_frame_z.pack(expand=True, fill=BOTH, pady=(0, 10))
            self.zoom_frame_z = Frame(self.outer_zoom_frame_z, bg=self.bg, padx=self.padx)
            self.zoom_frame_z.pack()
            self.zoom_label_z1 = Label(self.zoom_frame_z, text='z1:', bg=self.bg, fg=self.textcolor)
            self.left_zoom_entry_z = Entry(self.zoom_frame_z, width=7, bd=self.bd, bg=self.entry_background,
                                           selectbackground=self.selectbackground,
                                           selectforeground=self.selectforeground)
            self.zoom_label_z2 = Label(self.zoom_frame_z, text='z2:', bg=self.bg, fg=self.textcolor)
            self.right_zoom_entry_z = Entry(self.zoom_frame_z, width=7, bd=self.bd, bg=self.entry_background,
                                            selectbackground=self.selectbackground,
                                            selectforeground=self.selectforeground)
            self.zoom_button_z = Button(self.zoom_frame_z, text='Apply', command=apply_z, width=7,
                                        fg=self.buttontextcolor, bg=self.buttonbackgroundcolor, bd=self.bd)
            self.zoom_button_z.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                      bg=self.buttonbackgroundcolor)

            self.zoom_button_z.pack(side=RIGHT, padx=(10, 10))
            self.right_zoom_entry_z.pack(side=RIGHT, padx=self.padx)
            self.zoom_label_z2.pack(side=RIGHT, padx=self.padx)
            self.left_zoom_entry_z.pack(side=RIGHT, padx=self.padx)
            self.zoom_label_z1.pack(side=RIGHT, padx=self.padx)