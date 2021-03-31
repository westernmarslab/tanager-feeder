from tkinter import (
    Entry,
    Button,
    Label,
    Frame,
    BOTH,
    RIGHT,
    LEFT,
)

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder import utils

class SimplePlotSettingsManager:
    def __init__(self, controller: utils.ControllerType):
        self.controller = controller
        self.view_notebook = controller.view_notebook
        self.tk_format = utils.TkFormat(controller.config_info)

        self.plot_options_dialog = None
        self.new_plot_title_entry = None
        self.tab = None
        self.left_zoom_entry = None
        self.right_zoom_entry = None
        self.left_zoom_entry2 = None
        self.right_zoom_entry2 = None
        self.left_zoom_entry_z = None
        self.right_zoom_entry_z = None
    
    def show(self, tab, current_title):
        self.tab = tab
        buttons = {
            'ok': {
                self.select_tab: [],
                lambda: tab.set_title(self.new_plot_title_entry.get()): []
            }
        }

        self.plot_options_dialog = Dialog(self, 'Plot Options', '\nPlot title:', buttons=buttons)
        self.new_plot_title_entry = Entry(self.plot_options_dialog.top, width=20, bd=self.tk_format.bd,
                                          bg=self.tk_format.entry_background, selectbackground=self.tk_format.selectbackground,
                                          selectforeground=self.tk_format.selectforeground)
        self.new_plot_title_entry.insert(0, current_title)
        self.new_plot_title_entry.pack()

        outer_outer_zoom_frame = Frame(self.plot_options_dialog.top, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15)
        outer_outer_zoom_frame.pack(expand=True, fill=BOTH)

        zoom_title_frame = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg)
        zoom_title_frame.pack(pady=(5, 10))
        zoom_title_label = Label(zoom_title_frame, text='Adjust plot x and y limits:', bg=self.tk_format.bg,
                                      fg=self.tk_format.textcolor)
        zoom_title_label.pack(side=LEFT, pady=(0, 4))

        outer_zoom_frame = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        outer_zoom_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        zoom_frame = Frame(outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        zoom_frame.pack()

        zoom_label = Label(zoom_frame, text='x1:', bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_zoom_entry = Entry(zoom_frame, width=7, bd=self.tk_format.bd, bg=self.tk_format.entry_background,
                                     selectbackground=self.tk_format.selectbackground, selectforeground=self.tk_format.selectforeground)
        zoom_label2 = Label(zoom_frame, text='x2:', bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry = Entry(zoom_frame, width=7, bd=self.tk_format.bd, bg=self.tk_format.entry_background,
                                      selectbackground=self.tk_format.selectbackground,
                                      selectforeground=self.tk_format.selectforeground)
        zoom_button = Button(zoom_frame, text='Apply', command=self.apply_x, width=7, fg=self.tk_format.buttontextcolor,
                                  bg=self.tk_format.buttonbackgroundcolor, bd=self.tk_format.bd)
        zoom_button.config(fg=self.tk_format.buttontextcolor, highlightbackground=self.tk_format.highlightbackgroundcolor,
                                bg=self.tk_format.buttonbackgroundcolor)
        zoom_button.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label2.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_zoom_frame2 = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        outer_zoom_frame2.pack(expand=True, fill=BOTH, pady=(0, 10))
        zoom_frame2 = Frame(outer_zoom_frame2, bg=self.tk_format.bg, padx=self.tk_format.padx)
        zoom_frame2.pack()
        zoom_label3 = Label(zoom_frame2, text='y1:', bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_zoom_entry2 = Entry(zoom_frame2, width=7, bd=self.tk_format.bd, bg=self.tk_format.entry_background,
                                      selectbackground=self.tk_format.selectbackground,
                                      selectforeground=self.tk_format.selectforeground)
        zoom_label4 = Label(zoom_frame2, text='y2:', bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry2 = Entry(zoom_frame2, width=7, bd=self.tk_format.bd, bg=self.tk_format.entry_background,
                                       selectbackground=self.tk_format.selectbackground,
                                       selectforeground=self.tk_format.selectforeground)
        zoom_button2 = Button(zoom_frame2, text='Apply', command=self.apply_y, width=7,
                                   fg=self.tk_format.buttontextcolor, bg=self.tk_format.buttonbackgroundcolor, bd=self.tk_format.bd)
        zoom_button2.config(fg=self.tk_format.buttontextcolor, highlightbackground=self.tk_format.highlightbackgroundcolor,
                                 bg=self.tk_format.buttonbackgroundcolor)

        zoom_button2.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry2.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label4.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry2.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label3.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_zoom_frame_z = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        outer_zoom_frame_z.pack(expand=True, fill=BOTH, pady=(0, 10))
        zoom_frame_z = Frame(outer_zoom_frame_z, bg=self.tk_format.bg, padx=self.tk_format.padx)
        zoom_frame_z.pack()
        zoom_label_z1 = Label(zoom_frame_z, text='z1:', bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_zoom_entry_z = Entry(zoom_frame_z, width=7, bd=self.tk_format.bd, bg=self.tk_format.entry_background,
                                       selectbackground=self.tk_format.selectbackground,
                                       selectforeground=self.tk_format.selectforeground)
        zoom_label_z2 = Label(zoom_frame_z, text='z2:', bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry_z = Entry(zoom_frame_z, width=7, bd=self.tk_format.bd, bg=self.tk_format.entry_background,
                                        selectbackground=self.tk_format.selectbackground,
                                        selectforeground=self.tk_format.selectforeground)
        zoom_button_z = Button(zoom_frame_z, text='Apply', command=self.apply_z, width=7,
                                    fg=self.tk_format.buttontextcolor, bg=self.tk_format.buttonbackgroundcolor, bd=self.tk_format.bd)
        zoom_button_z.config(fg=self.tk_format.buttontextcolor, highlightbackground=self.tk_format.highlightbackgroundcolor,
                                  bg=self.tk_format.buttonbackgroundcolor)

        zoom_button_z.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry_z.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label_z2.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry_z.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label_z1.pack(side=RIGHT, padx=self.tk_format.padx)
        
    def select_tab(self):
        self.view_notebook.select(self.tab.top)

    def apply_x(self):
        self.view_notebook.select(self.tab.top)

        try:
            x1 = float(self.left_zoom_entry.get())
            x2 = float(self.right_zoom_entry.get())
            self.tab.adjust_x(x1, x2)
        except:
            ErrorDialog(self, title='Invalid Zoom Range',
                        label='Error: Invalid x limits: ' + self.left_zoom_entry.get() + ', ' + self.right_zoom_entry.get())

    def apply_y(self):
        self.view_notebook.select(self.tab.top)
        try:
            y1 = float(self.left_zoom_entry2.get())
            y2 = float(self.right_zoom_entry2.get())
            self.tab.adjust_y(y1, y2)
        except Exception as e:
            print(e)
            ErrorDialog(self, title='Invalid Zoom Range',
                        label='Error! Invalid y limits: ' + self.left_zoom_entry2.get() + ', ' + self.right_zoom_entry2.get())

    def apply_z(self):
        self.view_notebook.select(self.tab.top)

        try:
            z1 = float(self.left_zoom_entry_z.get())
            z2 = float(self.right_zoom_entry_z.get())
            self.tab.adjust_z(z1, z2)
        except Exception as e:
            print(e)
            ErrorDialog(self, title='Invalid Zoom Range',
                        label='Error: Invalid z limits: ' + self.left_zoom_entry.get() + ', ' + self.right_zoom_entry.get())