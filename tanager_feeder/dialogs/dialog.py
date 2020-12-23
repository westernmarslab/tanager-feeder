import tkinter as tk
from tkinter import Frame
from tkinter import Button
from tkinter import Tk

class Dialog:
    def __init__(self, controller, title, label, buttons, width=None, height=None, allow_exit=True, button_width=20,
                 info_string=None, grab=True, start_mainloop=True):

        self.controller = controller
        self.grab = grab
        if True:  # self.grab:
            try:
                self.controller.freeze()
            except:
                pass
        try:
            self.textcolor = self.controller.textcolor
            self.bg = self.controller.bg
            self.buttonbackgroundcolor = self.controller.buttonbackgroundcolor
            self.highlightbackgroundcolor = self.controller.highlightbackgroundcolor
            self.entry_background = self.controller.entry_background
            self.buttontextcolor = self.controller.buttontextcolor
            self.console_log = self.controller.console_log
            self.listboxhighlightcolor = self.controller.listboxhighlightcolor
            self.selectbackground = self.controller.selectbackground
            self.selectforeground = self.controller.selectforeground
        except:
            self.textcolor = 'black'
            self.bg = 'white'
            self.buttonbackgroundcolor = 'light gray'
            self.highlightbackgroundcolor = 'white'
            self.entry_background = 'white'
            self.buttontextcolor = 'black'
            self.console_log = None
            self.listboxhighlightcolor = 'light gray'
            self.selectbackground = 'light gray'
            self.selectforeground = 'black'

        if controller == None:
            self.top = Tk()
            self.top.configure(background=self.bg)
        else:
            if width == None or height == None:
                self.top = tk.Toplevel(controller.master, bg=self.bg)
            else:
                self.top = tk.Toplevel(controller.master, width=width, height=height, bg=self.bg)

        self.top.attributes('-topmost', 1)
        self.top.attributes('-topmost', 0)

        self.label_frame = Frame(self.top, bg=self.bg)
        self.label_frame.pack(side=tk.TOP)
        self.__label = tk.Label(self.label_frame, fg=self.textcolor, text=label, bg=self.bg)
        self.set_label_text(label, log_string=info_string)
        if label != '':
            self.__label.pack(pady=(10, 10), padx=(10, 10))

        self.button_width = button_width
        self.buttons = buttons
        self.set_buttons(buttons)

        self.top.wm_title(title)
        self.allow_exit = allow_exit
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

        if controller != None and info_string != None:
            self.log(info_string)

        if self.controller == None and start_mainloop == True:  # If there's no controller and this is the Tk object, might want to start the mainloop here, or might want to make additional modifications first in a subclass.
            self.top.mainloop()

    @property
    def label(self):
        return self.__label.cget('text')

    @label.setter
    def label(self, val):
        self.__label.configure(text=val)

    def set_title(self, newtitle):
        self.top.wm_title(newtitle)

    def set_label_text(self, newlabel, log_string=None):
        self.__label.config(fg=self.textcolor, text=newlabel)
        if log_string != None and self.controller != None:
            self.log(log_string)

    def set_buttons(self, buttons, button_width=None):
        self.buttons = buttons
        if button_width == None:
            button_width = self.button_width
        else:
            self.button_width = button_width
        # Sloppy way to check if button_frame already exists and reset it if it does.
        try:
            self.button_frame.destroy()
        except:
            pass
        self.button_frame = Frame(self.top, bg=self.bg)
        self.button_frame.pack(side=tk.BOTTOM)
        self.tk_buttons = []

        for button in buttons:
            if 'ok' in button.lower():
                self.ok_button = Button(self.button_frame, fg=self.textcolor, text='OK', command=self.ok,
                                        width=self.button_width)
                self.ok_button.bind('<Return>', self.ok)
                self.tk_buttons.append(self.ok_button)
                self.ok_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
            elif 'yes to all' in button.lower():
                self.yes_to_all_button = Button(self.button_frame, fg=self.textcolor, text='Yes to all',
                                                command=self.yes_to_all, width=self.button_width)
                self.yes_to_all_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.yes_to_all_button)
            elif 'yes' in button.lower():
                self.yes_button = Button(self.button_frame, fg=self.textcolor, text='Yes', bg='light gray',
                                         command=self.yes, width=self.button_width)
                self.tk_buttons.append(self.yes_button)
                self.yes_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
            elif 'no' in button.lower():
                self.no_button = Button(self.button_frame, fg=self.textcolor, text='No', command=self.no,
                                        width=self.button_width)
                self.no_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.no_button)
            elif 'cancel_queue' in button.lower():
                self.cancel_queue_button = Button(self.button_frame, fg=self.textcolor, text='Cancel',
                                                  command=self.cancel_queue, width=self.button_width)
                self.cancel_queue_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.cancel_queue_button)
            elif 'cancel' in button.lower():
                self.cancel_button = Button(self.button_frame, fg=self.textcolor, text='Cancel', command=self.cancel,
                                            width=self.button_width)
                self.cancel_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.cancel_button)
            elif 'retry' in button.lower():
                self.retry_button = Button(self.button_frame, fg=self.textcolor, text='Retry', command=self.retry,
                                           width=self.button_width)
                self.retry_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.retry_button)
            elif 'exit' in button.lower():
                self.exit_button = Button(self.button_frame, fg=self.textcolor, text='Exit', command=self.exit,
                                          width=self.button_width)
                self.exit_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.exit_button)
            elif 'work offline' in button.lower():
                self.offline_button = Button(self.button_frame, fg=self.textcolor, text='Work offline',
                                             command=self.work_offline, width=self.button_width)
                self.offline_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.offline_button)
            elif 'pause' in button.lower():
                self.pause_button = Button(self.button_frame, fg=self.textcolor, text='Pause', command=self.pause,
                                           width=self.button_width)
                self.pause_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.pause_button)
            elif 'continue' in button.lower():
                self.continue_button = Button(self.button_frame, fg=self.textcolor, text='Continue', command=self.cont,
                                              width=self.button_width)
                self.continue_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.continue_button)
            elif 'close' in button.lower():
                self.close_button = Button(self.button_frame, fg=self.textcolor, text='Close', command=self.close,
                                           width=self.button_width)
                self.close_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.close_button)
            elif 'reset' in button.lower():
                self.reset_button = Button(self.button_frame, fg=self.textcolor, text='Reset', command=self.reset,
                                           width=self.button_width)
                self.reset_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.reset_button)
            elif 'change ip' in button.lower():
                self.ip_button = Button(self.button_frame, fg=self.textcolor, text='Change IP', command=self.change_ip,
                                        width=self.button_width)
                self.ip_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.ip_button)
            for button in self.tk_buttons:
                button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                              bg=self.buttonbackgroundcolor)

    def on_closing(self):
        if self.allow_exit:
            if self.controller != None: self.controller.unfreeze()
            self.top.destroy()

    def reset(self):
        dict = self.buttons['reset']
        self.execute(dict, close=False)

    def change_ip(self):
        dict = self.buttons['Change IP']
        self.execute(dict)

    def close(self):
        if self.controller != None:
            self.controller.unfreeze()
        try:
            self.top.destroy()
        except:
            pass

    def retry(self):
        self.close()
        dict = self.buttons['retry']
        self.execute(dict, False)

    def exit(self):
        self.top.destroy()
        exit()

    def cont(self):
        dict = self.buttons['continue']
        self.execute(dict, close=False)

    def pause(self):
        dict = self.buttons['pause']
        self.execute(dict, close=False)

    def ok(self, event=None):
        dict = self.buttons['ok']
        self.execute(dict)

    def yes(self):
        dict = self.buttons['yes']
        self.execute(dict)

    def yes_to_all(self):
        dict = self.buttons['yes to all']
        self.execute(dict)

    def no(self):
        dict = self.buttons['no']
        self.execute(dict)

    def cancel(self):
        dict = self.buttons['cancel']
        self.execute(dict)

    def cancel_queue(self):
        dict = self.buttons['cancel_queue']
        self.execute(dict, close=False)

    def execute(self, dict, close=True):
        for func in dict:
            args = dict[func]
            func(*args)

        if close:
            self.close()

    def work_offline(self):
        self.close()
        dict = self.buttons['work offline']
        self.execute(dict, close=False)