#The controller runs the main thread controlling the program.
#It opens a Tkinter GUI with options for instrument control parameters and sample configuration
#The user can use the GUI to operate the goniometer motors and the spectrometer software.
from test._test_multiprocessing import baz

dev=False

import os
import sys
import platform

global SPEC_OFFLINE
SPEC_OFFLINE=False

global PI_OFFLINE
PI_OFFLINE=False

from tkinter import *
from tkinter import messagebox

try:
    import importlib #used to reload modules during development so changes actually update
except:
    pass
    
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import datetime
import time
from threading import Thread
from tkinter.filedialog import *

import http.client as httplib
import shutil

#Which spectrometer computer are you using? This should probably be desktop, but could be 'new' for the new lappy or 'old' for the ancient laptop.
computer='desktop'
computer='new'

#Figure out where this file is hanging out and tell python to look there for custom modules. This will depend on what operating system you are using.

global opsys
opsys=platform.system()
if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.

global package_loc
package_loc=''

global CMDNUM
CMDNUM=0

global INTERVAL
INTERVAL=0.25

if opsys=='Windows':
    #If I am running this script from my IDE, __file__ is not defined. In that case, I'll get an exception, and I'll go with my own hard-coded file location instead.
    try:
        rel_package_loc='\\'.join(__file__.split('\\')[:-1])+'\\'
        if 'C:' in rel_package_loc:
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'\\'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='C:\\AutoSpec\\autospec\\'

elif opsys=='Linux':
    #If I am running this script from my IDE, __file__ is not defined. In that case, I'll get an exception, and I'll go with my own hard-coded file location instead.
    try:
        rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
        if rel_package_loc[0]=='/':
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'/'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='/home/khoza/Python/AutoSpec/autospec/'
elif opsys=='Mac':
    try:
        rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
        if rel_package_loc[0]=='/':
            package_loc=rel_package_loc
        else: package_loc=os.getcwd()+'/'+rel_package_loc
    except:
        print('Developer mode!')
        dev=True
        package_loc='/home/khoza/Python/AutoSpec/autospec/'

sys.path.append(package_loc)

import goniometer_view
from goniometer_view import GoniometerView
import plotter
from plotter import Plotter
#import verticalscrolledframe

#This is needed because otherwise changes won't show up until you restart the shell. Not needed if you aren't changing the modules.
if dev:
    try:
        importlib.reload(goniometer_view)
        from goniometer_view import GoniometerView
        importlib.reload(plotter)
        from plotter import Plotter
    except:
        print('Not reloading modules')
#Server and share location. Can change if spectroscopy computer changes.
server=''
global NUMLEN #number of digits in the raw data filename. Could change from one version of software to next.

global tk_master
tk_master=None

NUMLEN=500
if computer=='old':
    #Number of digits in spectrum number for spec save config
    NUMLEN=3
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    PI_BUFFER=20
    server='melissa' #old computer
elif computer=='new':
    #Number of digits in spectrum number for spec save config
    NUMLEN=5
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    PI_BUFFER=20
    server='geol-chzc5q2' #new computer
    
elif computer=='desktop':
    #Number of digits in spectrum number for spec save config
    NUMLEN=5
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    PI_BUFFER=20
    server='marsinsight' #new computer

pi_server='raspberrypi'
spec_share='specshare'
spec_share_Mac='SpecShare'

pi_share='pishare'
pi_share_Mac='PiShare'
home_loc=os.path.expanduser('~')

if opsys=='Linux':
    import ctypes
    x11 = ctypes.cdll.LoadLibrary('libX11.so')
    x11.XInitThreads()
    
    home_loc+='/'
    spec_share_loc='/run/user/1000/gvfs/smb-share:server='+server+',share='+spec_share+'/'
    pi_share_loc='/run/user/1000/gvfs/smb-share:server='+pi_server+',share='+pi_share+'/'
    delimiter='/'
    spec_write_loc=spec_share_loc+'commands/from_control/'
    spec_temp_loc=spec_share_loc+'temp/'
    
    pi_write_loc=pi_share_loc+'commands/from_control/'
    spec_read_loc=spec_share_loc+'commands/from_spec/'
    pi_read_loc=pi_share_loc+'/commands/from_pi/'
    local_config_loc=home_loc+'.autospec_config/' #package_loc+'local_config/'
    global_config_loc=package_loc+'global_config/'
    log_loc=package_loc+'log/'
    
elif opsys=='Windows':
    home_loc+='\\'
    spec_share_loc='\\\\'+server.upper()+'\\'+spec_share+'\\'
    pi_share_loc='\\\\'+pi_server.upper()+'\\'+pi_share.upper()+'\\'

    spec_write_loc=spec_share_loc+'commands\\from_control\\'
    spec_temp_loc=spec_share_loc+'temp\\'
    
    pi_write_loc=pi_share_loc+'commands\\from_control\\'
    spec_read_loc=spec_share_loc+'commands\\from_spec\\'
    pi_read_loc=pi_share_loc+'commands\\from_pi\\'
    local_config_loc=home_loc+'.autospec_config\\' #package_loc+'local_config\\'
    global_config_loc=package_loc+'global_config\\'
    log_loc=package_loc+'log\\'
    
elif opsys=='Mac':
    home_loc+='/'
    spec_share_loc='/Volumes/'+spec_share_Mac+'/'
    pi_share_loc='/Volumes/'+pi_share_Mac+'/'
    delimiter='/'
    spec_write_loc=spec_share_loc+'commands/from_control/'
    spec_temp_loc=spec_share_loc+'temp/'
    
    pi_write_loc=pi_share_loc+'commands/from_control/'
    spec_read_loc=spec_share_loc+'commands/from_spec/'
    pi_read_loc=pi_share_loc+'commands/from_spec/'
    local_config_loc=home_loc+'.autospec_config/' #package_loc+'local_config/'
    global_config_loc=package_loc+'global_config/'
    log_loc=package_loc+'log/'
    
if not os.path.isdir(local_config_loc):
    print('Attempting to make config directory:')
    print(local_config_loc)
    os.mkdir(local_config_loc)

def exit_func():
    print('exit!')
    exit()

def main():
    #Check if you are connected to the server. If not, put up dialog box and wait. If you are connected, go on to main part 2.
    spec_connection_checker=SpecConnectionChecker(spec_read_loc, func=main_part_2)
    print('Checking spectrometer computer connection...')
    connected = spec_connection_checker.check_connection(True)
    if connected:
        print('Connected.')
    else:
        print('Not connected.')

#repeat check for raspi
def main_part_2():
    pi_connection_checker=PiConnectionChecker(pi_read_loc, func=main_part_3)
    print('Checking raspberry pi connection...')
    connected=pi_connection_checker.check_connection(True)
    if connected:
        print('Connected.')
    else:
        print('Not connected.')

def main_part_3():
    #Clean out your read and write directories for commands. Prevents confusion based on past instances of the program.
    if not SPEC_OFFLINE:
        print('Emptying spec command folder...')
        delme=os.listdir(spec_write_loc)
        delme2=os.listdir(spec_read_loc)
        print(str(len(delme)+len(delme2))+' files to delete')
        for file in delme:
            os.remove(spec_write_loc+file)
        for file in delme2:
            os.remove(spec_read_loc+file)

        print('Emptying spec temporary data folder...')
        delme=os.listdir(spec_temp_loc)
        print(str(len(delme))+' files to delete')
        for file in delme:
            os.remove(spec_temp_loc+file)
            
    if not PI_OFFLINE:
        print('Emptying pi command folder...')
        delme=os.listdir(pi_write_loc)
        print(str(len(delme))+' files to delete')
        for file in delme:
            os.remove(pi_write_loc+file)
        delme=os.listdir(pi_read_loc)
        print(str(len(delme))+' files to delete')
        for file in delme:
            try:
                os.remove(pi_read_loc+file)
            except:
                time.sleep(2)
                try:
                    os.remove(pi_read_loc+file)
                except(FileNotFoundError):
                    pass
    
    #Create a listener, which listens for commands, and a controller, which manages the model (which writes commands) and the view.
    spec_listener=SpecListener(spec_read_loc)
    pi_listener=PiListener(pi_read_loc)

    icon_loc=package_loc+'exception'#eventually someone should make this icon thing work. I haven't!
    
    control=Controller(spec_listener, pi_listener,spec_share_loc, spec_read_loc,spec_write_loc, spec_temp_loc, pi_write_loc, local_config_loc,global_config_loc, opsys, icon_loc)

class Controller():
    def __init__(self, spec_listener, pi_listener,spec_share_loc, spec_read_loc, spec_write_loc,spec_temp_loc, pi_write_loc,local_config_loc, global_config_loc,opsys,icon):
        self.spec_listener=spec_listener
        self.spec_listener.set_controller(self)
        self.spec_listener.start()
        
        self.pi_listener=pi_listener
        self.pi_listener.set_controller(self)
        self.pi_listener.start()
        
        self.spec_read_loc=spec_read_loc
        self.spec_share_loc=spec_share_loc
        self.spec_write_loc=spec_write_loc
        self.spec_temp_loc=spec_temp_loc
        
        self.pi_write_loc=pi_write_loc
        self.spec_commander=SpecCommander(self.spec_write_loc,self.spec_listener)
        self.pi_commander=PiCommander(self.pi_write_loc,self.pi_listener)
        
        self.remote_directory_worker=RemoteDirectoryWorker(self.spec_commander, self.spec_read_loc, self.spec_listener)
        
        self.local_config_loc=local_config_loc
        self.global_config_loc=global_config_loc
        self.opsys=opsys
        
        #The queue is a list of dictionaries commands:parameters
        #The commands are supposed to be executed in order, assuming each one succeeds.
        #CommandHandlers tell the controller when it's time to do the next one
        self.queue=[]
        
        #One wait dialog open at a time. CommandHandlers check whether to use an existing one or make a new one.
        self.wait_dialog=None
        
        self.min_i=-70
        self.max_i=70
        self.i=None
        self.final_i=None
        self.i_interval=None
        
        self.min_e=-70
        self.max_e=70
        self.e=None #current emission angle
        self.final_e=None
        self.e_interval=None
        
        self.min_az=0
        self.max_az=260
        self.az=None #current azimuth angle
        self.final_az=None
        self.az_interval=None
        
        self.required_angular_separation=10
        self.reversed_goniometer=False
        self.text_only=False #for running scripts.
        
        #cmds the user has entered into the console. Allows scrolling back and forth through commands by using up and down arrows.
        self.user_cmds=[] 
        self.user_cmd_index=0 
        #self.cmd_complete=False 
        self.script_failed=False 
        self.num_samples=5
        
        self.script_running=False
        self.white_referencing=False
        self.overwrite_all=False #User can say yes to all for overwriting files.
        
        
        #These will get set via user input.
        self.spec_save_path=''
        self.spec_basename=''
        self.spec_num=None
        self.spec_config_count=None
        self.take_spectrum_with_bad_i_or_e=False
        self.wr_time=None
        self.opt_time=None
        self.angles_change_time=None
        self.current_label=''
        
        self.incidence_entries=[]
        self.incidence_labels=[]
        self.emission_entries=[]
        self.emission_labels=[]
        self.azimuth_entries=[]
        self.azimuth_labels=[]
        
        self.active_incidence_entries=[] #list of geometries where data is currently being collected
        self.active_emission_entries=[]
        self.active_azimuth_entries=[]
        
        self.geometry_frames=[]
        self.active_geometry_frames=[]
        self.geometry_removal_buttons=[] #buttons for removing geometries from GUI
        
        self.sample_removal_buttons=[] #As each sample is added, it also gets an associated button for removing it.

        self.sample_label_entries=[] #Entries for holding sample names
        self.sample_labels=[] #Labels next to those entries
        self.pos_menus=[] #Option menus for each sample telling which position to put it in
        self.sample_pos_vars=[] #Variables associated with each menu telling its current value
        self.sample_frames=[] #Frames holding all of these things. New one gets created each time a sample is added to the GUI.
        
        self.sample_tray_index=None #The location of the physical sample tray. This will be an integer -1 to 4 corresponding to wr (-1) or an index in the available_sample_positions (0-4) SORRY!!
        self.current_sample_gui_index=0 #This might be different from the tray position. For example, if samples are set in trays 2 and 4 only then the gui_index will range from 0 (wr) to 1 (tray 2).
        self.available_sample_positions=['Sample 1','Sample 2','Sample 3','Sample 4','Sample 5'] #All available positions. Does not change.
        self.taken_sample_positions=[] #Filled positions. Changes as samples are added and removed.
        
        
        #Yay formatting. Might not work for Macs.
        self.bg='#333333'
        self.textcolor='light gray'
        self.buttontextcolor='white'
        self.bd=2
        self.padx=3
        self.pady=3
        self.border_color='light gray'
        self.button_width=15
        self.buttonbackgroundcolor='#888888'
        self.highlightbackgroundcolor='#222222'
        self.entry_background='light gray'
        if self.opsys=='Windows':
            self.listboxhighlightcolor='darkgray'
        else:
            self.listboxhighlightcolor='white'
        self.selectbackground='#555555'
        self.selectforeground='white'
        self.check_bg='#444444'
        
        
        #Tkinter notebook GUI
        self.master=Tk()
        self.master.configure(background = self.bg)

        self.master.title('Control')
        self.master.minsize(1050,400)
        #When the window closes, send a command to set the geometry to i=0, e=30.
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.tk_master=self.master #this gets used when deciding whether to open a new master when giving a no connection dialog or something. I can't remember. Maybe could be deleted, but I don't think so

        self.menubar = Menu(self.master)
        # create a pulldown menu, and add it to the menu bar
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load script", command=self.load_script)
        self.filemenu.add_command(label="Process and export data", command=self.show_process_frame)
        self.filemenu.add_command(label="Plot processed data", command=self.show_plot_frame)
        self.filemenu.add_command(label='Clear plotted data cache',command=self.reset_plot_data)

        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)

        self.menubar.add_cascade(label="File", menu=self.filemenu)
        
        # create more pulldown menus
        editmenu = Menu(self.menubar, tearoff=0)
        editmenu.add_command(label="Failsafes...", command=self.show_settings_frame)
        editmenu.add_command(label="Plot settings...", command=self.show_plot_settings_frame)
        self.menubar.add_cascade(label="Settings", menu=editmenu)
        

        
        self.goniometermenu=Menu(editmenu, tearoff=0)
        self.goniometermenu.add_command(label='X Manual', command=lambda:self.set_manual_automatic(force=0))
        self.goniometermenu.add_command(label='  Automatic', command=lambda:self.set_manual_automatic(force=1))
        editmenu.add_cascade(label="Goniometer control", menu=self.goniometermenu)
        
        self.geommenu=Menu(editmenu, tearoff=0)
        self.geommenu.add_command(label='X Individual', command=lambda:self.set_individual_range(0))
        self.geommenu.add_command(label='  Range (Automatic only)', command=lambda:self.set_individual_range(1),state=DISABLED)
        editmenu.add_cascade(label='Geometry specification', menu=self.geommenu)
        
        helpmenu = Menu(self.menubar, tearoff=0)
        #helpmenu.add_command(label="About", command=hello)
        self.menubar.add_cascade(label="Help", menu=helpmenu)
        
        # display the menu
        self.master.config(menu=self.menubar)
        
        self.notebook_frame=Frame(self.master)
        self.notebook_frame.pack(side=LEFT,fill=BOTH, expand=True)
        self.notebook=ttk.Notebook(self.notebook_frame)
        self.tk_buttons=[]
        self.entries=[]
        self.radiobuttons=[]
        self.tk_check_buttons=[]
        self.option_menus=[]
        
        self.view_frame = Frame(self.master, width=1800, height=1200,bg=self.bg)
        self.view_frame.pack(side=RIGHT,fill=BOTH,expand=True)
        self.view_notebook_holder=Frame(self.view_frame,width=1800,height=1200)
        self.view_notebook_holder.pack(fill=BOTH,expand=True)
        self.view_notebook=ttk.Notebook(self.view_notebook_holder) 
        self.view_notebook.pack()
        
        self.goniometer_view=GoniometerView(self,self.view_notebook) 
        self.view_notebook.bind("<<NotebookTabChanged>>", lambda event: self.goniometer_view.tab_switch(event))
        self.view_notebook.bind('<Button-3>',lambda event: self.plot_right_click(event))

        #The plotter, surprisingly, plots things.
        self.plotter=Plotter(self,self.get_dpi(),[ self.global_config_loc+'color_config.mplstyle',self.global_config_loc+'size_config.mplstyle'])
        
        
        #The commander is in charge of sending all the commands for the spec compy to read
        #If the user has saved spectra with this program before, load in their previously used directories.
        self.process_input_dir=''
        self.process_output_dir=''
        try:
            with open(self.local_config_loc+'process_directories.txt','r') as process_config:
                self.proc_local_remote=process_config.readline().strip('\n')
                self.process_input_dir=process_config.readline().strip('\n')
                self.process_output_dir=process_config.readline().strip('\n')
        except:
            with open(self.local_config_loc+'process_directories.txt','w+') as f:
                f.write('remote')
                f.write('C:\\Users\n')
                f.write('C:\\Users\n')
                self.proc_local_remote='remote'
                self.proc_input_dir='C:\\Users'
                self.proc_output_dir='C:\\Users'
                
        try:
            with open(self.local_config_loc+'plot_config.txt','r') as plot_config:
                self.plot_local_remote=plot_config.readline().strip('\n')
                self.plot_input_file=plot_config.readline().strip('\n')
                self.plot_title=plot_config.readline().strip('\n')
        except:
            with open(self.local_config_loc+'plot_config.txt','w+') as f:
                f.write('remote')
                f.write('C:\\Users\n')
                f.write('C:\\Users\n')
                
            self.plot_local_remote='remote'
            self.plot_title=''
            self.plot_input_file='C:\\Users'
    
        try:
            with open(self.local_config_loc+'spec_save.txt','r') as spec_save_config:
                self.spec_save_path=spec_save_config.readline().strip('\n')
                self.spec_basename=spec_save_config.readline().strip('\n')
                self.spec_startnum=str(int(spec_save_config.readline().strip('\n'))+1)
                while len(self.spec_startnum)<NUMLEN:
                    self.spec_startnum='0'+self.spec_startnum
        except:
            with open(self.local_config_loc+'spec_save.txt','w+') as f:
                f.write('C:\\Users\n')
                f.write('basename\n')
                f.write('-1\n')

                self.spec_save_path='C:\\Users'
                self.spec_basename='basename'
                self.spec_startnum='0'
                while len(self.spec_startnum)<NUMLEN:
                    self.spec_startnum='0'+self.spec_startnum
                    
        try:
            with open(self.local_config_loc+'script_config.txt','r') as script_config:
                self.script_loc=script_config.readline().strip('\n')
        except:
            with open(self.local_config_loc+'script_config.txt','w+') as script_config:
                script_config.write(os.getcwd())
                self.script_loc=os.getcwd()
        self.notebook_frames=[]
        
        self.control_frame=VerticalScrolledFrame(self, self.notebook_frame, bg=self.bg)
        self.control_frame.pack(fill=BOTH, expand=True)
        
        self.save_config_frame=Frame(self.control_frame.interior,bg=self.bg,highlightthickness=1)
        self.save_config_frame.pack(fill=BOTH,expand=True)
        self.spec_save_label=Label(self.save_config_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Raw spectral data save configuration:')
        self.spec_save_label.pack(pady=(15,5))
        self.spec_save_path_label=Label(self.save_config_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Directory:')
        self.spec_save_path_label.pack(padx=self.padx)
        
        self.spec_save_dir_frame=Frame(self.save_config_frame,bg=self.bg)
        self.spec_save_dir_frame.pack()
        
        self.spec_save_dir_browse_button=Button(self.spec_save_dir_frame,text='Browse',command=self.choose_spec_save_dir)
        self.tk_buttons.append(self.spec_save_dir_browse_button)
        self.spec_save_dir_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.spec_save_dir_browse_button.pack(side=RIGHT, padx=(3,15), pady=(5,10))
        
        self.spec_save_dir_var = StringVar()
        self.spec_save_dir_var.trace('w', self.validate_spec_save_dir)
        self.spec_save_dir_entry=Entry(self.spec_save_dir_frame, width=50,bd=self.bd,bg=self.entry_background, selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.spec_save_dir_var)
        self.entries.append(self.spec_save_dir_entry)
        self.spec_save_dir_entry.insert(0, self.spec_save_path)
        self.spec_save_dir_entry.pack(padx=(15,5), pady=(5,10), side=RIGHT)
        self.spec_save_frame=Frame(self.save_config_frame, bg=self.bg)
        self.spec_save_frame.pack()
        
        self.spec_basename_label=Label(self.spec_save_frame,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Base name:')
        self.spec_basename_label.pack(side=LEFT,pady=self.pady)
        
        self.spec_basename_var = StringVar()
        self.spec_basename_var.trace('w', self.validate_basename)
        self.spec_basename_entry=Entry(self.spec_save_frame, width=10,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.spec_basename_var)
        self.entries.append(self.spec_basename_entry)
        self.spec_basename_entry.pack(side=LEFT,padx=(5,5), pady=self.pady)
        self.spec_basename_entry.insert(0,self.spec_basename)
        

        
        self.spec_startnum_label=Label(self.spec_save_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Number:')
        self.spec_startnum_label.pack(side=LEFT,pady=self.pady)
        
        self.startnum_var = StringVar()
        self.startnum_var.trace('w', self.validate_startnum)
        self.spec_startnum_entry=Entry(self.spec_save_frame, width=10,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground,textvariable=self.startnum_var)
        self.entries.append(self.spec_startnum_entry)
        self.spec_startnum_entry.insert(0,self.spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=self.pady)      
              
        self.instrument_config_frame=Frame(self.control_frame.interior, bg=self.bg, highlightthickness=1)
        self.spec_settings_label=Label(self.instrument_config_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Instrument Configuration:')
        self.spec_settings_label.pack(padx=self.padx,pady=(10,10))
        self.instrument_config_frame.pack(fill=BOTH,expand=True)
        self.i_config_label_entry_frame=Frame(self.instrument_config_frame,bg=self.bg)
        self.i_config_label_entry_frame.pack()
        self.instrument_config_label=Label(self.i_config_label_entry_frame, fg=self.textcolor,text='Number of spectra to average:', bg=self.bg)
        self.instrument_config_label.pack(side=LEFT,padx=(20,0))
        

        
        
        self.instrument_config_entry=Entry(self.i_config_label_entry_frame, width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.instrument_config_entry)
        self.instrument_config_entry.insert(0, 200)
        self.instrument_config_entry.pack(side=LEFT)

        self.viewing_geom_options_frame=Frame(self.control_frame.interior,bg=self.bg)
        
        self.viewing_geom_options_frame_left=Frame(self.viewing_geom_options_frame, bg=self.bg,highlightthickness=1)
        self.viewing_geom_options_frame_left.pack(side=LEFT,fill=BOTH,expand=True)
        

        
        self.single_mult_frame=Frame(self.viewing_geom_options_frame,bg=self.bg,highlightthickness=1)
        self.single_mult_frame.pack(side=RIGHT, fill=BOTH,expand=True)
        self.angle_control_label=Label(self.single_mult_frame,text='Geometry specification:      ',bg=self.bg, fg=self.textcolor)
        self.angle_control_label.pack(padx=(5,5),pady=(10,5))
        
        self.individual_range=IntVar()
        self.individual_radio=Radiobutton(self.single_mult_frame, text='Individual         ',bg=self.bg,fg=self.textcolor,highlightthickness=0,variable=self.individual_range,value=0,selectcolor=self.check_bg,command=self.set_individual_range)
        self.radiobuttons.append(self.individual_radio)
        self.individual_radio.pack()
        
        self.range_radio=Radiobutton(self.single_mult_frame, text='Range with interval\n(Automatic only)',bg=self.bg, fg=self.textcolor,highlightthickness=0,variable=self.individual_range,value=1,selectcolor=self.check_bg,command=self.set_individual_range)
        self.radiobuttons.append(self.range_radio)
        self.range_radio.configure(state = DISABLED)
        self.range_radio.pack()
        
        self.gon_control_label_frame=Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.gon_control_label_frame.pack()
        self.gon_control_label=Label(self.gon_control_label_frame,text='\nGoniometer control:         ',bg=self.bg, fg=self.textcolor)
        self.gon_control_label.pack(side=LEFT,padx=(10,5))
        
        self.manual_radio_frame=Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.manual_radio_frame.pack()
        self.manual_automatic=IntVar()
        self.manual_radio=Radiobutton(self.manual_radio_frame,text='Manual            ',bg=self.bg,fg=self.textcolor,highlightthickness=0,variable=self.manual_automatic, value=0,selectcolor=self.check_bg,command=self.set_manual_automatic)
        self.radiobuttons.append(self.manual_radio)
        self.manual_radio.pack(side=LEFT,padx=(10,10),pady=(5,5))
        
        self.automation_radio_frame=Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.automation_radio_frame.pack()
        self.automation_radio=Radiobutton(self.automation_radio_frame,text='Automatic         ',bg=self.bg,fg=self.textcolor,highlightthickness=0,variable=self.manual_automatic,value=1,selectcolor=self.check_bg,command=self.set_manual_automatic)
        self.radiobuttons.append(self.automation_radio)
        self.automation_radio.pack(side=LEFT,padx=(10,10))
        self.filler_label=Label(self.viewing_geom_options_frame_left,text='',bg=self.bg)
        self.filler_label.pack()

        
        
        self.viewing_geom_frame=Frame(self.control_frame.interior,bg=self.bg, highlightthickness=1)
        self.viewing_geom_frame.pack(fill=BOTH,expand=True)     

        self.viewing_geom_options_label=Label(self.viewing_geom_frame,text='Viewing geometry:', fg=self.textcolor, bg=self.bg)
        self.viewing_geom_options_label.pack(pady=(10,10))
        
        self.individual_angles_frame=Frame(self.viewing_geom_frame, bg=self.bg,highlightbackground=self.border_color)
        self.individual_angles_frame.pack()
        self.add_geometry()


        
        self.range_frame=Frame(self.viewing_geom_frame,padx=self.padx,pady=self.pady,bd=2,highlightbackground=self.border_color,highlightcolor=self.border_color,highlightthickness=0,bg=self.bg)
        #self.range_frame.pack()
        self.light_frame=Frame(self.range_frame,bg=self.bg)
        self.light_frame.pack(side=LEFT,padx=(5,5))
        self.light_label=Label(self.light_frame,padx=self.padx, pady=self.pady,bg=self.bg,fg=self.textcolor,text='Incidence angles:')
        self.light_label.pack()
        
        light_labels_frame = Frame(self.light_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        light_labels_frame.pack(side=LEFT)
        
        light_start_label=Label(light_labels_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='First:')
        light_start_label.pack(pady=(0,8),padx=(40,0))
        light_end_label=Label(light_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Last:')
        light_end_label.pack(pady=(0,5), padx=(40,0))
        light_increment_label=Label(light_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Increment:')
        light_increment_label.pack(pady=(0,5), padx=(0,0))
    
        
        light_entries_frame=Frame(self.light_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        light_entries_frame.pack(side=RIGHT)
        
        self.light_start_entry=Entry(light_entries_frame,width=5, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.light_start_entry)
        self.light_start_entry.pack(padx=self.padx,pady=self.pady)
        self.light_end_entry=Entry(light_entries_frame,width=5, highlightbackground='white', bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.light_end_entry)
        self.light_end_entry.pack(padx=self.padx,pady=self.pady)    
        self.light_increment_entry=Entry(light_entries_frame,width=5,highlightbackground='white', bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.light_increment_entry)
        self.light_increment_entry.pack(padx=self.padx,pady=self.pady)
        
        detector_frame=Frame(self.range_frame,bg=self.bg)
        detector_frame.pack(side=LEFT)
        
        detector_label=Label(detector_frame,padx=self.padx, pady=self.pady,bg=self.bg,fg=self.textcolor,text='Emission angles:')
        detector_label.pack()
        
        detector_labels_frame = Frame(detector_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        detector_labels_frame.pack(side=LEFT,padx=(5,5))
        
        detector_start_label=Label(detector_labels_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='First:')
        detector_start_label.pack(pady=(0,8),padx=(40,0))
        detector_end_label=Label(detector_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Last:')
        detector_end_label.pack(pady=(0,5),padx=(40,0))
    
        detector_increment_label=Label(detector_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Increment:')
        detector_increment_label.pack(pady=(0,5),padx=(0,0))
    
        
        detector_entries_frame=Frame(detector_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        detector_entries_frame.pack(side=RIGHT)
        self.detector_start_entry=Entry(detector_entries_frame,bd=self.bd,width=5,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.detector_start_entry)
        self.detector_start_entry.pack(padx=self.padx,pady=self.pady)
        
        self.detector_end_entry=Entry(detector_entries_frame,bd=self.bd,width=5,highlightbackground='white',bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.detector_end_entry)
        self.detector_end_entry.pack(padx=self.padx,pady=self.pady)
        
        self.detector_increment_entry=Entry(detector_entries_frame,bd=self.bd,width=5, highlightbackground='white',bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.detector_increment_entry)
        self.detector_increment_entry.pack(padx=self.padx,pady=self.pady)
        
        self.azimuth_frame=Frame(self.range_frame,bg=self.bg)
        self.azimuth_frame.pack(side=LEFT,padx=(5,5))
        self.azimuth_label=Label(self.azimuth_frame,padx=self.padx, pady=self.pady,bg=self.bg,fg=self.textcolor,text='Azimuth angles:')
        self.azimuth_label.pack()
        
        azimuth_labels_frame = Frame(self.azimuth_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        azimuth_labels_frame.pack(side=LEFT)
        
        azimuth_start_label=Label(azimuth_labels_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='First:')
        azimuth_start_label.pack(pady=(0,8),padx=(40,0))
        azimuth_end_label=Label(azimuth_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Last:')
        azimuth_end_label.pack(pady=(0,5),padx=(40,0))
    
        azimuth_increment_label=Label(azimuth_labels_frame,bg=self.bg,padx=self.padx,pady=self.pady,fg=self.textcolor,text='Increment:')
        azimuth_increment_label.pack(pady=(0,5),padx=(0,0))
    
        azimuth_entries_frame=Frame(self.azimuth_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        azimuth_entries_frame.pack(side=RIGHT)
        
        self.azimuth_start_entry=Entry(azimuth_entries_frame,width=5, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.azimuth_start_entry)
        self.azimuth_start_entry.pack(padx=self.padx,pady=self.pady)
        
        self.azimuth_end_entry=Entry(azimuth_entries_frame,width=5, highlightbackground='white', bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.azimuth_end_entry)
        self.azimuth_end_entry.pack(padx=self.padx,pady=self.pady)    
        self.azimuth_increment_entry=Entry(azimuth_entries_frame,width=5,highlightbackground='white', bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.entries.append(self.azimuth_increment_entry)
        self.azimuth_increment_entry.pack(padx=self.padx,pady=self.pady)
       
        self.samples_frame=Frame(self.control_frame.interior,bg=self.bg, highlightthickness=1)
        self.samples_frame.pack(fill=BOTH,expand=True) 

        self.samples_label=Label(self.samples_frame, padx=self.padx,pady=self.pady,bg=self.bg, fg=self.textcolor,text='Samples:')
        self.samples_label.pack(pady=(10,10))
        
        self.add_sample()

        self.gen_frame=Frame(self.control_frame.interior, bg=self.bg,highlightthickness=1,pady=10)
        self.gen_frame.pack(fill=BOTH,expand=True)
        
        self.action_button_frame=Frame(self.gen_frame, bg=self.bg)
        self.action_button_frame.pack()
        
        self.opt_button=Button(self.action_button_frame, fg=self.textcolor,text='Optimize', padx=self.padx, pady=self.pady,width=self.button_width, bg='light gray', command=self.opt_button_cmd, height=2)
        self.tk_buttons.append(self.opt_button)
        self.opt_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.opt_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
        self.wr_button=Button(self.action_button_frame, fg=self.textcolor,text='White Reference', padx=self.padx, pady=self.pady, width=self.button_width, bg='light gray', command=self.wr_button_cmd, height=2)
        self.tk_buttons.append(self.wr_button)
        self.wr_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
        self.wr_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    
        self.spec_button=Button(self.action_button_frame, fg=self.textcolor,text='Take Spectrum', padx=self.padx, pady=self.pady, width=self.button_width,height=2,bg='light gray', command=self.spec_button_cmd)
        self.tk_buttons.append(self.spec_button)
        self.spec_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
        self.spec_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        
        self.acquire_button=Button(self.action_button_frame, fg=self.textcolor,text='Acquire Data', padx=self.padx, pady=self.pady, width=self.button_width,height=2,bg='light gray', command=self.acquire)
        self.tk_buttons.append(self.acquire_button)
        self.acquire_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)


        #************************Console********************************
        self.console_frame=Frame(self.view_frame, bg=self.border_color, height=200, highlightthickness=2,highlightcolor=self.bg)
        self.console_frame.pack(fill=BOTH, expand=True, padx=(1,1))
        self.console_title_label=Label(self.console_frame,padx=self.padx,pady=self.pady,bg=self.border_color,fg='black',text='Console',font=("Helvetica", 11))
        self.console_title_label.pack(pady=(5,5))
        self.text_frame=Frame(self.console_frame)
        self.scrollbar = Scrollbar(self.text_frame)
        self.some_width=self.control_frame.winfo_width()
        self.console_log = Text(self.text_frame, width=self.some_width,bg=self.bg, fg=self.textcolor)
        self.scrollbar.pack(side=RIGHT, fill=Y)
    
        self.scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry=Entry(self.console_frame, width=self.some_width,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.console_entry.bind("<Return>",self.execute_cmd)
        self.console_entry.bind('<Up>',self.iterate_cmds)
        self.console_entry.bind('<Down>',self.iterate_cmds)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.console_log.pack(fill=BOTH,expand=True)
        self.console_entry.focus()
    
        #check before taking spectra whether conditions have been met regarding when the last white reference was, etc
        self.wrfailsafe=IntVar()
        self.wrfailsafe.set(1)
        self.optfailsafe=IntVar()
        self.optfailsafe.set(1)
        self.angles_failsafe=IntVar()
        self.angles_failsafe.set(1)
        self.labelfailsafe=IntVar()
        self.labelfailsafe.set(1)
        self.wr_angles_failsafe=IntVar()
        self.wr_angles_failsafe.set(1)
        self.anglechangefailsafe=IntVar()
        self.anglechangefailsafe.set(1)
        
        self.plot_remote=IntVar()
        self.plot_local=IntVar()
        if self.plot_local_remote=='remote':
            self.plot_remote.set(1)
            self.plot_local.set(0)
        else:
            self.plot_local.set(1)
            self.plot_remote.set(0)
            
        self.proc_remote=IntVar()
        self.proc_local=IntVar()
        if self.proc_local_remote=='remote':
            self.proc_remote.set(1)
            self.proc_local.set(0)
        else:
            self.proc_local.set(1)
            self.proc_remote.set(0)
            
        if not PI_OFFLINE:
            self.set_manual_automatic(force=1)


        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        thread = Thread(target =self.bind)
        thread.start()
        
        thread = Thread(target =self.scrollbar_check) #Waits for everything to get packed, then checks if you need a scrollbar on the control frame.
        thread.start()
        if opsys=='Windows':
            self.master.wm_state('zoomed')
        self.master.mainloop()
        
    def scrollbar_check(self):
        time.sleep(0.5)
        self.control_frame.update()

    #********************** Process frame ******************************
    #called when user goes to File > Process and export data
    def show_process_frame(self):
        
        self.process_top=Toplevel(self.master)
        self.process_top.wm_title('Process Data')
        self.process_frame=Frame(self.process_top, bg=self.bg, pady=15,padx=15)
        self.process_frame.pack()

        self.input_dir_label=Label(self.process_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Raw spectral data input directory:')
        self.input_dir_label.pack(padx=self.padx,pady=(10,5))
        
        self.input_frame=Frame(self.process_frame, bg=self.bg)
        self.input_frame.pack()
        
        self.process_input_browse_button=Button(self.input_frame,text='Browse',command=self.choose_process_input_dir)
        self.process_input_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_input_browse_button.pack(side=RIGHT, padx=self.padx)
        self.tk_buttons.append(self.process_input_browse_button)
        
        
        self.input_dir_var = StringVar()
        self.input_dir_var.trace('w', self.validate_input_dir)
         
        self.input_dir_entry=Entry(self.input_frame, width=50,bd=self.bd, textvariable=self.input_dir_var,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.input_dir_entry.insert(0, self.process_input_dir)
        self.input_dir_entry.pack(side=RIGHT,padx=self.padx, pady=self.pady)
        self.entries.append(self.input_dir_entry)
        

        self.proc_local_remote_frame=Frame(self.process_frame, bg=self.bg)
        self.proc_local_remote_frame.pack()
        
        self.output_dir_label=Label(self.proc_local_remote_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Processed data output directory:')
        self.output_dir_label.pack(padx=self.padx,pady=(10,5),side=LEFT)
        
        self.proc_local_check=Checkbutton(self.proc_local_remote_frame, fg=self.textcolor,text=' Local',selectcolor=self.check_bg, bg=self.bg, pady=self.pady, variable=self.proc_local,highlightthickness=0, highlightbackground=self.bg,command=self.local_process_cmd)
        self.proc_local_check.pack(side=LEFT,pady=(5,0),padx=(5,5))
        if self.proc_local_remote=='local':
            self.proc_local_check.select()
        self.tk_check_buttons.append(self.proc_local_check)

        self.proc_remote_check=Checkbutton(self.proc_local_remote_frame, fg=self.textcolor,text=' Remote', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.proc_remote, command=self.remote_process_cmd,selectcolor=self.check_bg)
        self.proc_remote_check.pack(side=LEFT, pady=(5,0),padx=(5,5))
        if self.proc_local_remote=='remote':
            self.proc_remote_check.select()
        self.tk_check_buttons.append(self.proc_remote_check)
        

        self.process_output_frame=Frame(self.process_frame, bg=self.bg)
        self.process_output_frame.pack(pady=(5,10))
        self.process_output_browse_button=Button(self.process_output_frame,text='Browse',command=self.choose_process_output_dir)
        self.process_output_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_output_browse_button.pack(side=RIGHT, padx=self.padx)
        self.tk_buttons.append(self.process_output_browse_button)
        
        self.output_dir_entry=Entry(self.process_output_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.output_dir_entry.insert(0, self.process_output_dir)
        self.output_dir_entry.pack(side=RIGHT,padx=self.padx,pady=self.pady)
        self.entries.append(self.output_dir_entry)
        
        self.output_file_label=Label(self.process_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Output file name:')
        self.output_file_label.pack(padx=self.padx,pady=self.pady)
        self.output_file_entry=Entry(self.process_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.output_file_entry.pack()
        self.entries.append(self.output_file_entry)
        

        self.process_check_frame=Frame(self.process_frame, bg=self.bg)
        self.process_check_frame.pack(pady=(15,5))
        self.process_save_dir=IntVar()
        self.process_save_dir_check=Checkbutton(self.process_check_frame, selectcolor=self.check_bg,fg=self.textcolor,text='Save file configuration', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.process_save_dir)
        self.process_save_dir_check.select()
        
        self.process_button_frame=Frame(self.process_frame, bg=self.bg)
        self.process_button_frame.pack()  
        self.process_button=Button(self.process_button_frame, fg=self.textcolor,text='Process', padx=self.padx, pady=self.pady, width=int(self.button_width*1.3),bg='light gray', command=self.process_cmd)
        self.process_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.process_button.pack(padx=(15,15),side=LEFT)
        self.tk_buttons.append(self.process_button)
        
        self.process_close_button=Button(self.process_button_frame,fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,text='Close',padx=self.padx,pady=self.pady,width=int(self.button_width*1.3),bg=self.buttonbackgroundcolor,command=self.close_process)
        self.process_close_button.pack(padx=(15,15),side=LEFT)
        self.tk_buttons.append(self.process_close_button)
       
    #Closes process frame
    def close_process(self):
        self.process_top.destroy()
        
    def show_plot_settings_frame(self):
        pass
        
    #Show failsafes settings frame
    def show_settings_frame(self):        
        self.settings_top=Toplevel(self.master)
        self.settings_top.wm_title('Failsafe Settings')
        self.settings_frame=Frame(self.settings_top, bg=self.bg, pady=2*self.pady,padx=15)
        self.settings_frame.pack()

        
        self.failsafe_title_frame=Frame(self.settings_frame, bg=self.bg)
        self.failsafe_title_frame.pack(pady=(10,0),fill=X, expand=True)
        self.failsafe_label0=Label(self.failsafe_title_frame, fg=self.textcolor,text='Failsafes:                                                                      ', bg=self.bg)
        self.failsafe_label0.pack(side=LEFT)
        
        self.failsafe_frame=Frame(self.settings_frame, bg=self.bg, pady=self.pady)
        self.failsafe_frame.pack(fill=BOTH, expand=True, padx=(10,10))
        


        self.wr_failsafe_check_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.wr_failsafe_check_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.wrfailsafe_check=Checkbutton(self.wr_failsafe_check_frame, fg=self.textcolor,text='Prompt if no white reference has been taken.', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.wrfailsafe,selectcolor=self.check_bg)
        self.wrfailsafe_check.pack(side=LEFT)
        if self.wrfailsafe.get():
            self.wrfailsafe_check.select()
        
        self.wr_timeout_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.wr_timeout_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.wr_timeout_label=Label(self.wr_timeout_frame, fg=self.textcolor,text='Timeout (minutes):', bg=self.bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(20,0))
        self.wr_timeout_entry=Entry(self.wr_timeout_frame, bd=self.bd,width=10,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.wr_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.wr_timeout_entry.insert(0,'8')
        
        
        self.optfailsafe_check_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.optfailsafe_check_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.optfailsafe_check=Checkbutton(self.optfailsafe_check_frame, fg=self.textcolor,text='Prompt if the instrument has not been optimized.', bg=self.bg, pady=self.pady,highlightthickness=0,selectcolor=self.check_bg, variable=self.optfailsafe)
        self.optfailsafe_check.pack(side=LEFT)
        if self.optfailsafe.get():
            self.optfailsafe_check.select()
        
        self.opt_timeout_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.opt_timeout_frame.pack(pady=self.pady,fill=X, expand=True,padx=(20,5))
        self.opt_timeout_label=Label(self.opt_timeout_frame, fg=self.textcolor,text='Timeout (minutes):', bg=self.bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(20,0))
        self.opt_timeout_entry=Entry(self.opt_timeout_frame,bd=self.bd, width=10,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.opt_timeout_entry.pack(side=LEFT, padx=(0,20))
        self.opt_timeout_entry.insert(0,'60')
        self.filler_label=Label(self.opt_timeout_frame,bg=self.bg,fg=self.textcolor,text='              ')
        self.filler_label.pack(side=LEFT)
        
        self.angles_failsafe_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.angles_failsafe_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.angles_failsafe_check=Checkbutton(self.angles_failsafe_frame, fg=self.textcolor,text='Check validity of emission and incidence angles.', bg=self.bg, pady=self.pady,highlightthickness=0,selectcolor=self.check_bg, variable=self.angles_failsafe)
        #self.angles_failsafe_check.pack(pady=(6,5),side=LEFT,padx=(0,20))
        if self.angles_failsafe.get():
            self.angles_failsafe_check.select()
        
        self.label_failsafe_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.label_failsafe_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.label_failsafe_check=Checkbutton(self.label_failsafe_frame, fg=self.textcolor,text='Require a label for each spectrum.', bg=self.bg, pady=self.pady,highlightthickness=0, selectcolor=self.check_bg,variable=self.labelfailsafe)
        self.label_failsafe_check.pack(pady=(6,5), side=LEFT,padx=(0,20))
        if self.labelfailsafe.get():
            self.label_failsafe_check.select()

        self.wr_angles_failsafe_frame=Frame(self.failsafe_frame, bg=self.bg)
        self.wr_angles_failsafe_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.wr_angles_failsafe_check=Checkbutton(self.wr_angles_failsafe_frame,selectcolor=self.check_bg, fg=self.textcolor,text='Require a new white reference at each viewing geometry             ', bg=self.bg, pady=self.pady, highlightthickness=0, variable=self.wr_angles_failsafe)
        self.wr_angles_failsafe_check.pack(pady=(6,5),side=LEFT)
        if self.wr_angles_failsafe.get():
            self.wr_angles_failsafe_check.select()
        
        self.wrap_frame=Frame(self.failsafe_frame,bg=self.bg)
        self.wrap_frame.pack(pady=self.pady,padx=(20,5),fill=X, expand=True)
        self.anglechangefailsafe_check=Checkbutton(self.wrap_frame, selectcolor=self.check_bg,fg=self.textcolor,text='Remind me to check the goniometer if the viewing geometry changes.', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.anglechangefailsafe)
        #self.anglechangefailsafe_check.pack(pady=(6,5),side=LEFT)#side=LEFT, pady=self.pady)
        #if self.anglechangefailsafe.get():
         #   self.anglechangefailsafe_check.select()
            
        self.failsafes_ok_button=Button(self.failsafe_frame,text='Ok',command=self.settings_top.destroy)
        self.failsafes_ok_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor, width=15)
        self.failsafes_ok_button.pack(pady=self.pady)
        self.settings_top.resizable(False, False)
        
     
    #********************** Plot frame ******************************   
    def show_plot_frame(self): 
        self.plot_top=Toplevel(self.master)
        self.plot_top.wm_title('Plot')
        self.plot_frame=Frame(self.plot_top, bg=self.bg, pady=2*self.pady,padx=15)
        self.plot_frame.pack()
        
        self.plot_title_label=Label(self.plot_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Plot title:')
        self.plot_title_label.pack(padx=self.padx,pady=(15,5))
        self.plot_title_entry=Entry(self.plot_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.plot_title_entry.insert(0,self.plot_title)
        self.plot_title_entry.pack(pady=(5,20))
        self.plot_local_remote_frame=Frame(self.plot_frame, bg=self.bg)
        self.plot_local_remote_frame.pack()
        
        self.plot_input_dir_label=Label(self.plot_local_remote_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='Path to .csv file:')
        self.plot_input_dir_label.pack(side=LEFT,padx=self.padx,pady=self.pady)

        self.plot_local_check=Checkbutton(self.plot_local_remote_frame, fg=self.textcolor,text=' Local',selectcolor=self.check_bg, bg=self.bg, pady=self.pady, variable=self.plot_local,highlightthickness=0, highlightbackground=self.bg,command=self.local_plot_cmd)
        self.plot_local_check.pack(side=LEFT,pady=(5,5),padx=(5,5))

        self.plot_remote_check=Checkbutton(self.plot_local_remote_frame, fg=self.textcolor,text=' Remote', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.plot_remote, command=self.remote_plot_cmd,selectcolor=self.check_bg)
        self.plot_remote_check.pack(side=LEFT, pady=(5,5),padx=(5,5))
        
        #controls whether the file being plotted is looked for locally or on the spectrometer computer
        if self.plot_local_remote=='remote':
            self.plot_remote_check.select()
            self.plot_local_check.deselect()
        if self.plot_local_remote=='local':
            self.plot_local_check.select()
            self.plot_remote_check.deselect()
        

        self.plot_file_frame=Frame(self.plot_frame, bg=self.bg)
        self.plot_file_frame.pack(pady=(5,10))
        self.plot_file_browse_button=Button(self.plot_file_frame,text='Browse',command=self.choose_plot_file)
        self.plot_file_browse_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.plot_file_browse_button.pack(side=RIGHT, padx=self.padx)
        
        self.plot_input_dir_entry=Entry(self.plot_file_frame, width=50,bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.plot_input_dir_entry.insert(0, self.plot_input_file)
        self.plot_input_dir_entry.pack(side=RIGHT)
   
        self.plot_button_frame=Frame(self.plot_frame,bg=self.bg)
        self.plot_button_frame.pack()
        
        self.plot_button=Button(self.plot_button_frame, fg=self.textcolor,text='Plot', padx=self.padx, pady=self.pady, width=int(self.button_width*1.3),bg='light gray', command=self.plot)
        self.plot_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.plot_button.pack(side=LEFT,pady=(20,20),padx=(15,15))
        
        self.process_close_button=Button(self.plot_button_frame,fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,text='Close',padx=self.padx,pady=self.pady,width=int(self.button_width*1.3),bg=self.buttonbackgroundcolor,command=self.close_plot)
        self.process_close_button.pack(pady=(20,20),padx=(15,15),side=LEFT)
    
    def close_plot(self):
        self.plot_top.destroy()
        
        
    def bind(self): #This is probably important but I don't remember exactly how it works. Somethign to do with setting up the GUI.
        self.master.bind("<Configure>", self.resize)
        time.sleep(0.2)
        window=PretendEvent(self.master,self.master.winfo_width(),self.master.winfo_height())
        self.resize(window)
        time.sleep(0.2)
        
        if not SPEC_OFFLINE:
            self.log('Spec compy connected.')
        else:
            self.log('Spec compy not connected. Working offline. Restart to collect spectral data.')
        if not PI_OFFLINE:
            self.log('Raspberry pi connected.')
        else:
            self.log('Raspberry pi not connected. Working offline. Restart to use automation features.')
        
    def on_closing(self):
        self.goniometer_view.quit()
        self.master.destroy()
        
    #Toggle back and forth between saving your processed data remotely or locally
    def local_process_cmd(self):
        if self.proc_local.get() and not self.proc_remote.get():
            return
        elif self.proc_remote.get() and not self.proc_local.get():
            return
        elif not self.proc_remote.get():
            self.proc_remote_check.select()
        else:
            self.proc_remote_check.deselect()
            self.proc_local_remote='local'
            self.output_dir_entry.delete(0,'end')
       
    #Toggle back and forth between saving your processed data remotely or locally
    def remote_process_cmd(self):
        if self.proc_local.get() and not self.proc_remote.get():
            return
        elif self.proc_remote.get() and not self.proc_local.get():
            return
        elif not self.proc_local.get():
            self.proc_local_check.select()

        else:
            self.proc_local_check.deselect()
            self.proc_local_remote='remote'
            self.output_dir_entry.delete(0,'end')

    #Toggle back and forth between plotting your data from a remote or local file
    def local_plot_cmd(self):
        if self.plot_local.get() and not self.plot_remote.get():
            return
        elif self.plot_remote.get() and not self.plot_local.get():
            return
        elif not self.plot_remote.get():
            self.plot_remote_check.select()
        else:
            self.plot_remote_check.deselect()
    #Toggle back and forth between plotting your data from a remote or local file
    def remote_plot_cmd(self):
        if self.plot_local.get() and not self.plot_remote.get():
            return
        elif self.plot_remote.get() and not self.plot_local.get():
            return
        elif not self.plot_local.get():
            self.plot_local_check.select()
        else:
            self.plot_local_check.deselect()


      
    def load_script(self):
        self.script_running=True
        self.script_failed=False
        script_file = askopenfilename(initialdir=self.script_loc,title='Select script')
        self.queue=[]
        with open(self.local_config_loc+'script_config.txt','w') as script_config:
            dir=''
            if self.opsys=='Linux' or self.opsys=='Mac':
                dir='/'.join(script_file.split('/')[0:-1])
            else:
                dir='\\'.join(script_file.split('\\')[0:-1])

            self.script_loc=dir
            script_config.write(dir)
            
        with open(script_file,'r') as script:
            cmd=script.readline().strip('\n')
            success=True
            while cmd!='' and success==True and self.script_failed==False: #probably just cmd!=''.
                self.queue.append({self.next_script_line:[cmd]})
                cmd=script.readline().strip('\n')
                continue
        self.queue.append({self.next_script_line:['end file']})
        for item in self.queue:
            print(item)
        self.next_in_queue()

    
    def next_script_line(self,cmd):
        self.script_running=True
        if cmd=='end file':
            self.log('Script complete')
            self.script_running=False
            self.queue=[]
        if self.script_failed:
            self.log('Exiting')
            self.queue=[]
        else:
            self.console_entry.delete(0,'end')
            self.console_entry.insert(0,cmd)
            success=self.execute_cmd('event!')
            if success==False:
                self.log('Exiting.')

        
    def move_sample():
        self.pi_commander.move_sample()
        
    #use this to make plots - matplotlib works in inches but we want to use pixels.
    def get_dpi(self):
        MM_TO_IN = 1/25.4
        pxw = self.master.winfo_screenwidth()
        inw = self.master.winfo_screenmmwidth() * MM_TO_IN
        return pxw/inw

   

            
    def opt_old(self, override=False):
        
        try:
            new_spec_config_count=int(self.instrument_config_entry.get())
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return 
        
        # if self.manual_automatic.get()==0 and override==False: #manual
        #     buttons={
        #         'yes':{
        #             self.opt:[True]
        #         },
        #         'no':{
        #             self.clear_queue:[]
        #         }
        #     }
        #     warnings=self.check_viewing_geom_for_manual_operation(buttons)
        #     if warnings!='':
        #         return
                
            
            
        ready=self.setup_RS3_config({self.opt:[True]}) #Since we want to make sure optimization times are logged in the current folder, we do all the setup checks before optimizing even though no data gets saved.


        
        if ready: #If we don't still need to set save config or configure instrument before optimizing

            self.spec_commander.optimize()
            handler=OptHandler(self)
            
    #when operating in manual mode, check validity of viewing geom when the user clicks buttons. If valid, update graphic and self.i and self.e before moving on to other checks. Return any warnings.       
    def check_viewing_geom_for_manual_operation(self):
            warnings=''
            
            valid_i=validate_int_input(self.incidence_entries[0].get(),-90,90)
            if valid_i:
                if str(self.i)!=self.incidence_entries[0].get():
                    self.angles_change_time=time.time()
                self.i=int(self.incidence_entries[0].get())
                
            else:
                warnings+='The incidence angle is invalid (Min:'+str(-90)+', Max:'+str(90)+').\n\n'
                
            valid_e=validate_int_input(self.emission_entries[0].get(),-90,90)
            if valid_e:
                if str(self.e)!=self.emission_entries[0].get():
                    self.angles_change_time=time.time()
                self.e=int(self.emission_entries[0].get())
            else:
                warnings+='The emission angle is invalid (Min:'+str(-90)+', Max:'+str(90)+').\n\n'
                
            valid_separation=self.validate_distance(self.incidence_entries[0].get(),self.emission_entries[0].get())
            if valid_e and valid_i and not valid_separation:
                warnings+='Incidence and emission should be at least '+str(self.required_angular_separation)+' degrees apart.\n\n'
            self.set_and_animate_geom()
                
            return warnings

        
    #Check whether the current save configuration for raw spectral is different from the last one saved. If it is, send commands to the spec compy telling it so.
    def check_save_config(self):
        new_spec_save_dir=self.spec_save_dir_entry.get()
        new_spec_basename=self.spec_basename_entry.get()
        try:
            new_spec_num=int(self.spec_startnum_entry.get())
        except:
            return 'invalid'
 
        if new_spec_save_dir=='' or new_spec_basename=='' or new_spec_num=='':
            return 'invalid'
        
        if new_spec_save_dir != self.spec_save_path or new_spec_basename != self.spec_basename or self.spec_num==None or new_spec_num!=self.spec_num:
            return 'not_set'
        else:
            return 'set'
            
    def check_mandatory_input(self):
        save_config_status=self.check_save_config()
        if save_config_status=='invalid':
            dialog=ErrorDialog(self,label='Error: Please enter a valid save configuration.')
            return False
            
        try:
            new_spec_config_count=int(self.instrument_config_entry.get())
            if new_spec_config_count<1 or new_spec_config_count>32767:
                raise(Exception)
        except:
            dialog=ErrorDialog(self,label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return False
            
        if self.manual_automatic.get()==1: #0 is manual, 1 is automatic
            for index in range(len(self.active_incidence_entries)):
                i=self.active_incidence_entries[index].get()
                e=self.active_emission_entries[index].get()
                az=self.active_azimuth_entries[index].get()
                valid_i=validate_int_input(i,self.min_i, self.max_i)
                valid_e=validate_int_input(e,self.min_e,self.max_e)
                valid_az=validate_int_input(az,self.min_az,self.max_az)
                if not valid_i or not valid_e or not valid_az:
                    dialog=ErrorDialog(self,label='Error: Invalid viewing geometry:\n\nincidence = '+str(i)+'\nemission = '+str(e)+'\nazimuth = '+str(az),width=300, height=130)
                    return False
                elif not self.validate_distance(i, e, az):
                    dialog=ErrorDialog(self,label='Error: Due to geometric constraints on the goniometer,\nincidence must be at least '+str(self.required_angular_separation)+' degrees different than emission.',width=300, height=130)
                    return False
        
        return True
        
    #If the user has failsafes activated, check that requirements are met. Always require a valid number of spectra.
    #Different requirements are checked depending on what the function func is that will be called next (opt, wr, take spectrum, acquire)
    def check_optional_input(self, func, args=[],warnings=''):
            label=warnings
            now=int(time.time())
            incidence=self.incidence_entries[0].get()
            emission=self.emission_entries[0].get()
            
            if self.manual_automatic.get()==0:
                warnings=self.check_viewing_geom_for_manual_operation()
                label+=warnings

                if self.optfailsafe.get() and func!=self.opt:
                    try:
                        opt_limit=int(float(self.opt_timeout_entry.get()))*60
                    except:
                        opt_limit=sys.maxsize
                    if self.opt_time==None:
                        label+='The instrument has not been optimized.\n\n'
                    elif now-self.opt_time>opt_limit: 
                        minutes=str(int((now-self.opt_time)/60))
                        seconds=str((now-self.opt_time)%60)
                        if int(minutes)>0:
                            label+='The instrument has not been optimized for '+minutes+' minutes '+seconds+' seconds.\n\n'
                        else: label+='The instrument has not been optimized for '+seconds+' seconds.\n\n'
                    if self.opt_time!=None:
                        if self.angles_change_time==None:
                            pass
                        elif self.opt_time<self.angles_change_time:
                            valid_i=validate_int_input(incidence,self.min_i,self.max_i)
                            valid_e=validate_int_input(emission,self.min_e,self.max_e)
                            if valid_i and valid_e:
                                label+='The insturment has not been optimized at this geometry.\n\n'
                

                if self.wrfailsafe.get() and func!=self.wr and func!=self.opt:
    
                    try:
                        wr_limit=int(float(self.wr_timeout_entry.get()))*60
                    except:
                        wr_limit=sys.maxsize
                    if self.wr_time==None:
                        label+='No white reference has been taken.\n\n'
                    elif self.opt_time!=None and self.opt_time>self.wr_time:
                            label+='No white reference has been taken since the instrument was optimized.\n\n'
                    elif int(self.instrument_config_entry.get()) !=int(self.spec_config_count):
                        label+='No white reference has been taken while averaging this number of spectra.\n\n'
                    elif self.spec_config_count==None:
                        label+='No white reference has been taken while averaging this number of spectra.\n\n'
                    elif now-self.wr_time>wr_limit: 
                        minutes=str(int((now-self.wr_time)/60))
                        seconds=str((now-self.wr_time)%60)
                        if int(minutes)>0:
                            label+=' No white reference has been taken for '+minutes+' minutes '+seconds+' seconds.\n\n'
                        else: label+=' No white reference has been taken for '+seconds+' seconds.\n\n'
                if self.wr_angles_failsafe.get() and func!=self.wr:
    
                    if self.angles_change_time!=None and self.wr_time!=None and func!=self.opt:
                        if self.angles_change_time>self.wr_time+1:
                            valid_i=validate_int_input(incidence,self.min_i,self.max_i)
                            valid_e=validate_int_input(emission,self.min_e,self.max_e)
                            if valid_i and valid_e:
                                label+=' No white reference has been taken at this viewing geometry.\n\n'
                        # elif str(emission)!=str(self.e) or str(incidence)!=str(self.i):
                        #     label+=' No white reference has been taken at this viewing geometry.\n\n'
                        
                if False:#self.angles_failsafe.get():
                    valid_i=validate_int_input(incidence,self.min_i,self.max_i)
                    valid_e=validate_int_input(emission,self.min_e,self.max_e)
                    valid_separation=self.validate_distance(incidence,emission)

                    if not valid_i:
                        label+='The incidence angle is invalid (Min:'+str(self.min_i)+', Max:'+str(self.max_i)+').\n\n'
                    if not valid_e:
                        label+='The emission angle is invalid (Min:'+str(self.min_e)+', Max:'+str(self.max_e)+').\n\n'
                    if valid_e and valid_i:
                        if not valid_separation:
                            label+='Incidence and emission need to be at least '+str(self.required_angular_separation)+' degrees apart.\n\n'
                        
                if False:#self.anglechangefailsafe.get():
                    anglechangealert=False
                    if self.angles_change_time==None and emission!='' and incidence !='':
                        label+='This is the first time emission and incidence angles are being set,\n'
                        anglechangealert=True
                    elif self.e==None and emission!='':
                        label+='This is the first time the emission angle is being set,\n'
                        anglechangealert=True
                        if str(incidence)!=str(self.i) and incidence!='' and self.i!=None:
                            label+='and the incidence angle has changed since last spectrum,\n'
                        anglechangealert=True
                    elif self.i==None and incidence!='':
                        label+='This is the first time the incidence angle is being set,\n'
                        anglechangealert=True
                        if str(emission)!=str(self.e) and emission !='' and self.e!=None:
                            label+='and the emission angle has changed since last spectrum,\n' 
                        anglechangealert=True
                    if anglechangealert==False and emission!=str(self.e) and str(emission) !='' and str(incidence) !=str(self.i) and incidence!='':
                        if self.e!=None and self.i!=None:
                            label+='The emission and incidence angles have changed since last spectrum,\n'
                            anglechangealert=True
                    elif anglechangealert==False and str(emission)!=str(self.e) and emission !='':
                        label+='The emission angle has changed since last spectrum,\n'
                        anglechangealert=True
                    elif anglechangealert==False and str(incidence)!=str(self.i) and incidence!='':
                        label+='The incidence angle has changed since last spectrum,\n' 
                        anglechangealert=True
                        
                    if anglechangealert:#and onlyanglechange:
                        label+='so the goniometer arm(s) may need to change to match.\n\n'
                        pass
                   
            if self.labelfailsafe.get() and func!=self.opt and func!=self.wr:
                if self.sample_label_entries[self.current_sample_gui_index].get()=='':
                    label +='This sample has no label.\n\n'
            for entry in self.sample_label_entries:
                sample_label=entry.get()
                newlabel=self.validate_sample_name(sample_label)
                if newlabel!=sample_label:
                    entry.delete(0,'end')
                    if newlabel=='':
                        newlabel='sample'

                    entry.insert(0,newlabel)
                    label+="'"+sample_label+"' is an invalid sample label.\nSample will be labeled as '"+newlabel+"' instead.\n\n"
                    self.log("Warning: '"+sample_label+"' is an invalid sample label. Removing reserved characters and expressions.")

            if label !='': #if we came up with errors
                title='Warning!'
                
                buttons={
                    'yes':{
                        #if the user says they want to continue anyway, run take spectrum again but this time with override=True
                        func:args
                    },
                    'no':{}
                }
                label='Warning!\n\n'+label
                label+='\nDo you want to continue?'
                dialog=Dialog(self,title,label,buttons)
                return False
            else: #if there were no errors
                return True
        
    #Setup gets called after we already know that input is valid, but before we've set up the specrometer control software. If we need to set RS3's save configuration or the instrument configuration (number of spectra to average), it puts those things into the queue saying we will need to do them when we start.
    def setup_RS3_config(self, nextaction):
        #self.check_logfile()
        if self.manual_automatic.get()==0:
            thread=Thread(target=self.set_and_animate_geom)
            thread.start()

        #Requested save config is guaranteed to be valid because of input checks above.
        save_config_status=self.check_save_config()
        if self.check_save_config()=='not_set':
            self.complete_queue_item()
            self.queue.insert(0,nextaction)
            self.queue.insert(0,{self.set_save_config:[]})
            self.set_save_config()#self.take_spectrum,[True])
            return False

        #Requested instrument config is guaranteed to be valid because of input checks above.
        new_spec_config_count=int(self.instrument_config_entry.get())
        if self.spec_config_count==None or str(new_spec_config_count) !=str(self.spec_config_count):
            self.complete_queue_item()
            self.queue.insert(0,nextaction)
            self.queue.insert(0,{self.configure_instrument:[]})
            self.configure_instrument()
            return False
            
        if True: #self.spec_save_config.get():
            file=open(self.local_config_loc+'spec_save.txt','w')
            file.write(self.spec_save_dir_entry.get()+'\n')
            file.write(self.spec_basename_entry.get()+'\n')
            file.write(self.spec_startnum_entry.get()+'\n')
            self.process_input_dir=self.spec_save_dir_entry.get()
        return True
        
    #acquire is called every time opt, wr, or take spectrum buttons are pushed from manual mode
    #also called if acquire button is pushed in automatic mode
    #Action will be either wr, take_spectrum, or opt (manual mode) OR it might just be 'acquire' (automatic mode)
    #For any of these things, we need to validate input. 
    def acquire(self, override=False, setup_complete=False, action=None, garbage=False):
        if not setup_complete:
            #Make sure basenum entry has the right number of digits. It is already guaranteed to have no more digits than allowed and to only have numbers.
            start_num=self.spec_startnum_entry.get()
            num_zeros=NUMLEN-len(start_num)
            for _ in range(num_zeros):
                start_num='0'+start_num
            self.set_text(self.spec_startnum_entry, start_num)

            #Set all entries to active. Viewing geometry information will be pulled from these one at a time. Entries are removed from the active list after the geom info is read.
            self.active_incidence_entries=list(self.incidence_entries)
            self.active_emission_entries=list(self.emission_entries)
            self.active_azimuth_entries=list(self.azimuth_entries)
            self.active_geometry_frames=list(self.geometry_frames)
            
            
        range_warnings=''
        if action==None: #If this was called by the user clicking acquire. otherwise, it will be take_spectrum or wr?
            action=self.acquire
            self.queue.insert(0,{self.acquire:[]})
            if self.individual_range.get()==1:
                valid_range=self.range_setup(override)
                if not valid_range:
                    return
                elif type(valid_range)==str: #If there was a warning associated with the input check for the range setup e.g. interval specified as zero, then we'll log this as a warning for the user coming up.
                    range_warnings=valid_range
                
        if not override: #If input isn't valid and the user asks to continue, take_spectrum will be called again with override set to True
            ok=self.check_mandatory_input() #check things that have to be right in order to continue e.g. valid number of spectra to average
            if not ok:
                return
            
            #now check things that are optional e.g. having reasonable sample labels, taking a white reference at every geom.
            valid_input=False
            if action==self.take_spectrum:
                valid_input=self.check_optional_input(self.take_spectrum,[True,False,garbage],range_warnings)
            elif action==self.acquire or action==self.wr:
                valid_input=self.check_optional_input(action,[True,False],range_warnings)
            elif action==self.opt:
                valid_input=self.check_optional_input(self.opt,[True,False],range_warnings)
            if not valid_input:
                return         
        #Make sure RS3 save config and instrument config are taken care of. This will add those actions to the queue if needed.
        if not setup_complete:
            if action==self.take_spectrum:
                setup=self.setup_RS3_config({self.take_spectrum:[True, False,garbage]})
            elif action==self.wr or action==self.acquire:
                #print(action)
                setup=self.setup_RS3_config({action:[True, False]})
            elif action==self.opt:
                print('SETUP')
                setup=self.setup_RS3_config({self.opt:[True, False]})
                print(setup)
            else:
                raise Exception()
            #If things were not already set up (instrument config, etc) then the compy will take care of that and call take_spectrum again after it's done.
            if not setup:
                return
                    
        if action==self.take_spectrum:
            startnum_str=str(self.spec_startnum_entry.get())
            while len(startnum_str)<NUMLEN:
                startnum_str='0'+startnum_str
            if not garbage:
                label=''
                if self.white_referencing: #This will be true when we are saving the spectrum after the white reference
                    label='White Reference'
                else:
                    label=self.sample_label_entries[self.current_sample_gui_index].get()
                self.spec_commander.take_spectrum(self.spec_save_path, self.spec_basename, startnum_str,label ,self.i, self.e)
                handler=SpectrumHandler(self)
            else:
                self.spec_commander.take_spectrum(self.spec_save_path, self.spec_basename, startnum_str, 'GARBAGE',self.i, self.e)
                handler=SpectrumHandler(self,title='Collecting garbage...',label='Collecting garbage spectrum...')
                
        elif action==self.wr:
            self.spec_commander.white_reference()
            handler=WhiteReferenceHandler(self)
            
        elif action==self.opt:
            self.spec_commander.optimize()
            handler=OptHandler(self)
            
        elif action==self.acquire:
            self.build_queue()
            self.next_in_queue()
            
    def build_queue(self):
        script_queue=list(self.queue) #If we're running a script, the queue might have a lot of commands in it that will need to be executed after we're done acquiring. save these, we'll append them in a moment.
        self.queue=[]

            #For each (i, e, az), opt, white reference, save the white reference, move the tray, take a  spectrum, then move the tray back, then update geom to next.
        
        for index, entry in enumerate(self.active_incidence_entries): #This is one for each geometry when geometries are specified individually. When a range is specified, we actually quietly create pretend entry objects for each pair, so it works then too.
            if index==0:self.queue.append({self.next_geom:[False]}) #For the first, don't complete anything
            else:self.queue.append({self.next_geom:[]})
            self.queue.append({self.move_tray:['wr']})
            self.queue.append({self.opt:[True, True]})
            self.queue.append({self.wr:[True,True]})
            self.queue.append({self.take_spectrum:[True,True,False]})
            for pos in self.taken_sample_positions: #e.g. 'Sample 1'
                self.queue.append({self.move_tray:[pos]})
                self.queue.append({self.take_spectrum:[True,True,True]}) #Save and delete a garbage spectrum
                self.queue.append({self.take_spectrum:[True,True,False]}) #Save a real spectrum
        
        #Return tray to wr position when finished
        self.queue.append({self.move_tray:['wr']})
        
        #Now append the script queue we saved at the beginning. But check if acquire is the first command in the script queue and if it is, complete that item.
        if self.script_running:
            if len(script_queue)>0:
                while self.acquire in script_queue[0]:
                    script_queue.pop(0)
            self.queue=self.queue+script_queue

    #animates goniometer arms moving
    def set_and_animate_geom(self, complete_queue_item=False):
            try:
                self.set_geom()
            except:
                return
            valid_i=validate_int_input(self.i,self.min_i,self.max_i)
            if valid_i:
                if self.manual_automatic.get()==0:#manual, no animation
                    self.goniometer_view.set_incidence(int(self.i),config=True)
                else:
                    self.goniometer_view.set_incidence(int(self.i))
            
            valid_e=validate_int_input(self.e,self.min_e,self.max_e)
            if valid_e:
                if self.manual_automatic.get()==0:#manual, fast animation
                    self.goniometer_view.set_emission(int(self.e),config=True)
                else:
                    self.goniometer_view.set_emission(int(self.e))
            
            valid_az=validate_int_input(self.az,self.min_az,self.max_az)
            if valid_az:
                if self.manual_automatic.get()==0:#manual, fast animation
                    self.goniometer_view.set_emission(int(self.az),config=True)
                else:
                    self.goniometer_view.set_emission(int(self.az))

            if complete_queue_item:
                self.complete_queue_item()
                if len(self.queue)>0:
                    self.next_in_queue()
                        
    def set_geom(self):
        if self.i==None or self.e==None or self.az==None:
            self.angles_change_time=time.time()
        elif int(self.i)!=int(self.active_incidence_entries[0].get()) or int(self.e)!=int(self.active_emission_entries[0].get()) or int(self.az)!=self.active_azimuth_entries[0].get():
            self.angles_change_time=time.time()
        self.i=int(self.active_incidence_entries[0].get())
        self.e=int(self.active_emission_entries[0].get())
        self.az=int(self.active_azimuth_entries[0].get())
        

        
    def set_text(self, widget, text):
        state=widget.cget('state')
        widget.configure(state='normal')
        widget.delete(0,'end')
        widget.insert(0,text)
        widget.configure(state=state)
        
    def safe_az_sweep(self, i,e,start_az, end_az):
        print('*************************AZ SWEEP****************************')
        print(start_az)
        print(end_az)
        az_array=np.arange(start_az, end_az,1)
        if len(az_array)==0:
            az_array=np.arange(start_az, end_az,-1)
        az_array=np.append(az_array, end_az)
        
        for az in az_array:
            tup=(i,e,az)
            pos, dist=self.get_closest_approach(i, e, az)

            if dist<self.required_angular_separation:
                print('az hit')
                print(az_array)
                print("az, pos, dist")
                print(az)
                print(pos)
                print(dist)
                return False
        return True
    
    def safe_e_sweep(self, i,az,start_e, end_e):
        print('*************************E SWEEP****************************')
        print(start_e)
        print(end_e)
        e_array=np.arange(start_e, end_e,1)
        if len(e_array)==0:
            e_array=np.arange(start_e, end_e,-1)
        e_array=np.append(e_array, end_e)
        
        for e in e_array:
            pos, dist=self.get_closest_approach(i, e, az)
            if dist<self.required_angular_separation:
                print(e_array)
                print('hits at')
                print(e)
                print(pos)
                print(dist)
                print()
                return False
        return True
    
    def safe_i_sweep(self, e,az,start_i, end_i):
        print('*************************I SWEEP****************************')
        print(start_i)
        print(end_i)
        i_array=np.arange(start_i, end_i,1)
        if len(i_array)==0:
            i_array=np.arange(start_i, end_i,-1)
        i_array=np.append(i_array, end_i)
        
        for i in i_array:
            pos, dist=self.get_closest_approach(i, e, az)

            if dist<self.required_angular_separation:
                print(i_array)
                print('hits at')
                print(i)
                print(pos)
                print(dist)
                print()
                return False
        return True
    
    def get_movement_order(self, next_science_i, next_science_e, next_science_az, current_motor=None):
        
        if current_motor==None:
            current_motor=(self.i, self.e, self.az)
            
        current_motor_i=int(current_motor[0])
        current_motor_e=int(current_motor[1])
        current_motor_az=int(current_motor[2])
        
        next_science_i=int(next_science_i)
        next_science_e=int(next_science_e)
        next_science_az=int(next_science_az)
        
        current_science_i, current_science_e, current_science_az=self.motor_pos_to_science_pos(current_motor_i, current_motor_e, current_motor_az)
        
        movement_order=None
        
        def convert_based_on_motor_pos(movement_order):
            if current_motor_az>=180 and movement_order!=None:
                if 'az' in movement_order:
                    movement_order[movement_order.index('az')]='az+180'
                    movement_order[movement_order.index('i')]='-i'
                elif 'az-180' in movement_order:
                    movement_order[movement_order.index('az-180')]='az'
                    movement_order[movement_order.index('-i')]='i'
                elif 'az+180' in movement_order:
                    pass
                    #raise(Exception('YIKES super positive!'))
            elif current_motor_az<0 and movement_order!=None:
                if 'az' in movement_order:
                    movement_order[movement_order.index('az')]='az-180'
                    movement_order[movement_order.index('i')]='-i'
                elif 'az+180' in movement_order:
                    movement_order[movement_order.index('az+180')]='az'
                    movement_order[movement_order.index('-i')]='i'
                elif 'az-180' in movement_order:
                    pass
                    #raise(Exception('YIKES super negative!'))
                
            return movement_order
        
        #try moving az, i, e. If that doesn't work, try az, e, i.
        safe_az=self.safe_az_sweep(current_science_i, current_science_e, current_science_az, next_science_az)
        if safe_az:
            safe_i=self.safe_i_sweep(current_science_e, next_science_az, current_science_i, next_science_i)
            if safe_i:
                safe_e=self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                if safe_e:
                    print('1')
                    movement_order= ['az','i','e']
            if movement_order==None:
                safe_e=self.safe_e_sweep(current_science_i, next_science_az, current_science_e, next_science_e)
                if safe_e:
                    safe_i=self.safe_i_sweep(next_science_e, next_science_az, current_science_i, next_science_i)
                    if safe_i:
                        print('2')
                        movement_order= ['az','e','i']

        #try moving azimuth +180, i, e. If that doesn't work, try az, e, i.
        if movement_order==None:# and next_science_az<=90:
            safe_az1=self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 179)
            print(safe_az1)
            print('safe az sweep 2')
            safe_az2=self.safe_az_sweep(-1*current_science_i, current_science_e, 0, next_science_az)
            print(safe_az2)
            if safe_az1 and safe_az2:
    
                safe_i=self.safe_i_sweep(current_science_e, next_science_az, -1*current_science_i, next_science_i)
                print('safe i? '+str(safe_i))
                if safe_i:
                    safe_e=self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        print('3')
                        movement_order=['az+180','-i','e']
                if movement_order==None:# and next_science_az<=90:
                    safe_e=self.safe_e_sweep(-1*current_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        safe_i=self.safe_i_sweep(next_science_e, next_science_az, -1*current_science_i, next_science_i)
                        if safe_i:
                            print('4')
                            movement_order= ['az+180','e','-i']
                            
        if movement_order==None:
            safe_az_1=self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 0)
            safe_az_2=self.safe_az_sweep(-1*current_science_i, current_science_e, 179, next_science_az) #get_closest_approach reverses i for az<180
            print('safe az? '+str(safe_az_1))
            print('safe az?'+str(safe_az_2))
            if safe_az_1 and safe_az_2:
                safe_i=self.safe_i_sweep(current_science_e, next_science_az, -1*current_science_i, next_science_i)
                print('safe i? '+str(safe_i))
                if safe_i:
                    safe_e=self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        print('3 negative')
                        movement_order= ['az-180','-i','e']
                if movement_order==None and next_science_az>=90:
                    safe_e=self.safe_e_sweep(-1*current_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        safe_i=self.safe_i_sweep(next_science_e, next_science_az, -1*current_science_i, next_science_i)
                        if safe_i:
                            print('4 negative')
                            movement_order= ['az-180','e','-i']
                            

        if movement_order==None:
            if current_science_e>=0:
                temp_i=-1*(current_science_e+2*self.required_angular_separation)
            else:
                temp_i=-1*(current_science_e-2*self.required_angular_separation)
            temp_i_str='temp i'
                
            print('TEMP I: '+str(temp_i))    
            print('current i: '+str(current_science_i))  
            safe_temp_i=self.safe_i_sweep(current_science_e, current_science_az, current_science_i, temp_i)
            print(safe_temp_i)
            if not safe_temp_i:
                temp_i_str='-temp i'
                temp_i=-1*temp_i
                safe_temp_i=self.safe_i_sweep(current_science_e, current_science_az, current_science_i, temp_i)
            
            if safe_temp_i:
                #try moving az, i, e
                safe_az=self.safe_az_sweep(temp_i, current_science_e, current_science_az, next_science_az)
                if safe_az:
                    safe_i=self.safe_i_sweep(current_science_e, next_science_az, temp_i, next_science_i)
                    if safe_i:
                        safe_e=self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                        if safe_e:
                            print('9')
                            movement_order=[temp_i_str, 'az','i','e']
                    else:
                        safe_e=self.safe_e_sweep(temp_i, next_science_az, current_science_e, next_science_e)
                        if safe_e:
                            safe_i=self.safe_i_sweep(next_science_e, next_science_az, temp_i, next_science_i)
                            if safe_i:
                                print('10')
                                movement_order=[temp_i_str,'az','e','i']
                if movement_order==None:
                    #try moving azimuth +180, i, e. If that doesn't work, try az+180, e, i.
                    safe_az1=self.safe_az_sweep(temp_i, current_science_e, current_science_az, 179)
                    print('Temp i plus az?'+str(safe_az1))
                    safe_az2=self.safe_az_sweep(-1*temp_i, current_science_e, 0, next_science_az)
                    print(safe_az2)
                    if safe_az1 and safe_az2:
                        safe_i=self.safe_i_sweep(current_science_e, next_science_az, -1*temp_i, next_science_i)
                        if safe_i:
                            safe_e=self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                            if safe_e:
                                print('5')
                                movement_order= [temp_i_str,'temp e', 'az+180','-i','e']
                        safe_e=self.safe_e_sweep(-1*temp_i, next_science_az, current_science_e, next_science_e)
                        if safe_e:
                            safe_i=self.safe_i_sweep(next_science_e, next_science_az, -1*temp_i, next_science_i)
                            if safe_i:
                                print('6')
                                movement_order= [temp_i_str, 'temp e','az+180','e','-i']
                                
                if movement_order==None:
                    safe_az1=self.safe_az_sweep(temp_i, current_science_e, current_science_az, 0)
                    print('Temp i minus az?'+str(safe_az1))
                    safe_az2=self.safe_az_sweep(-1*temp_i, current_science_e, 179, next_science_az)
                    print(safe_az2)
                    if safe_az1 and safe_az2:
                        safe_i=self.safe_i_sweep(current_science_e, next_science_az, -1*temp_i, next_science_i)
                        if safe_i:
                            safe_e=self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                            if safe_e:
                                print('7')
                                movement_order= [temp_i_str,'temp e','az-180','-i','e']
                        safe_e=self.safe_e_sweep(-1*temp_i, next_science_az, current_science_e, next_science_e)
                        if safe_e:
                            safe_i=self.safe_i_sweep(next_science_e, next_science_az, -1*temp_i, next_science_i)
                            if safe_i:
                                print('8')
                                movement_order= [temp_i_str,'temp e', 'az-180','e','-i']
        movement_order=convert_based_on_motor_pos(movement_order)
        return movement_order

        #Try moving to 90 degree azimuth, moving e, moving i
        if movement_order==None:
            safe_az=self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 90)
            if safe_az:
                safe_i=self.safe_i_sweep(current_science_e, current_science_az, current_science_i, 10)
                if safe_i:
                        safe_az=self.safe_az_sweep(10, next_science_e, 90, next_science_az) #won't give desired path if e.g. next science az is 0 and want to go through 180.
                        if safe_az:
                            safe_i=self.safe_i_sweep(next_science_e, next_science_az, self.max_i, next_science_i)
                            if safe_i:
                                safe_e=self.safe_e_sweep(10,next_science_az, 10, next_science_e)
                                if safe_e:
                                    print('Weirdo')
                                    movement_order=['az motor 90', 'i 10', 'e 10','az','i','e']
                            

            
        return movement_order
        
        
        print('ERROR: NO PATH FOUND')
        return 'ERROR: NO PATH FOUND'
        
        
        
        
    def next_geom(self, complete_last=True): 
        self.complete_queue_item()
        if complete_last:
            self.active_incidence_entries.pop(0)
            self.active_emission_entries.pop(0)
            self.active_azimuth_entries.pop(0)
            if self.individual_range.get()==0:
                self.active_geometry_frames.pop(0)
        
        next_i=int(self.active_incidence_entries[0].get())
        next_e=int(self.active_emission_entries[0].get())
        next_az=int(self.active_azimuth_entries[0].get())
 
        #Update goniometer position. Don't run the arms into each other
        movements, reversed=self.get_movement_order(next_i, next_e, next_az)
        
        if reversed: self.reversed_goniometer=True
        else: self.reversed_goniometer=False
        print('*********************')
        print(movements)
        if 'az+180' in movements:
            self.queue.insert(movements.index('az+180'), {self.set_azimuth:[next_az+180]})
        if 'az' in movements:
            print('az')
            self.queue.insert(movements.index('az'), {self.set_azimuth:[next_az]})
        if 'i to negative e + angular_separation' in movements:
            i=-1*(int(self.e)+np.sign(int(self.e))*self.required_angular_separation)
            self.queue.insert(movements.index('az'), {self.set_incidence:[i]})
        if 'i to e + angular_separation' in movements:
            i=(int(self.e)+np.sign(int(self.e))*self.required_angular_separation)
            self.queue.insert(movements.index('az'), {self.set_incidence:[i]})
        self.queue.insert(movements.index('e'),{self.set_emission:[]}) #either 1 or 2
        self.queue.insert(movements.index('i'),{self.set_incidence:[]}) #either 1 or 2
        
#         n=0
#         if int(next_i)<int(next_e):#(int(self.e)>int(self.i) and int(next_e)<int(next_i)) or (int(self.e)<int(self.i) and int(next_e)>int(next_i)): #If keeping az the same would result in swapping positions
#             self.queue.insert(n, {self.set_azimuth:[next_az+180]})
#             n+=1
#         else:
#             self.queue.insert(n, {self.set_azimuth:[next_az]})
#             n+=1
#                 
#                 
#         if int(self.e)>int(self.i): 
#             if int(next_e)>int(self.e):  
#                 self.queue.insert(n,{self.set_emission:[]})
#                 self.queue.insert(n+1,{self.set_incidence:[]})
#             else:
#                 self.queue.insert(n,{self.set_incidence:[]})
#                 self.queue.insert(n+1,{self.set_emission:[]})
#         elif int(self.e)<int(self.i): 
#             if int(next_e)<int(self.e):
#                 self.queue.insert(n,{self.set_emission:[]})
#                 self.queue.insert(n+1,{self.set_incidence:[]})
#             else:
#                 self.queue.insert(n,{self.set_incidence:[]})
#                 self.queue.insert(n+1,{self.set_emission:[]})        
        
        self.next_in_queue()
    #def set_motion_order(self, next_i, next_e, next_az):

    #Move light will either read i from the GUI (default, i=None), or if this is a text command then i will be passed as a parameter.
    #When from the commandline, i may not be an incidence angle at all but a number of steps to move. In this case, type will be 'steps'.
    def set_incidence(self, i=None, type='angle', negative=False):
        steps=True
        timeout=0
        
        if type=='angle':
            steps=False #We will need to tell the motionhandler whether we're specifying steps or an angle
            
            #First check whether we actually need to move at all.
            if i==None:
                i=int(self.active_incidence_entries[0].get())
            if i==self.i: #No change in incidence angle, no need to move
                self.log('Goniometer remaining at an incidence angle of '+str(i)+' degrees.')
                self.complete_queue_item()
                if len(self.queue)>0:
                    self.next_in_queue()
                return #If we're staying in the same spot, just return!
            timeout=np.abs(int(i)-int(self.i))*8+PI_BUFFER
        else:
            timeout=np.abs(int(i))/15+PI_BUFFER
            
        self.pi_commander.set_incidence(i,type)
        handler=MotionHandler(self,label='Setting incidence...',timeout=timeout,steps=steps, destination=i)

        if type=='angle': #Only change the visualization if an angle is specified. Specifiying steps is for setting up the 
            self.goniometer_view.set_incidence(int(i))
                
            
    def set_emission(self, e=None, type='angle'):
        steps=True
        timeout=0
        
        if type=='angle':
            steps=False #We will need to tell the motionhandler whether we're specifying steps or an angle
            
            #First check whether we actually need to move at all.
            if e==None:
                e=int(self.active_emission_entries[0].get())
            if e==self.e: #No change in incidence angle, no need to move
                self.log('Goniometer remaining at an emission angle of '+str(e)+' degrees.')
                self.complete_queue_item()
                if len(self.queue)>0:
                    self.next_in_queue()
                return #If we're staying in the same spot, just return!
            timeout=np.abs(int(e)-int(self.e))*8+PI_BUFFER
        else:
            timeout=np.abs(int(i))/15+PI_BUFFER
            
        self.pi_commander.set_emission(e,type)
        handler=MotionHandler(self,label='Setting emission...',timeout=timeout,steps=steps, destination=e)

        if type=='angle': #Only change the visualization if an angle is specified. Specifiying steps is for setting up the 
            self.goniometer_view.set_emission(int(e))
            
    def set_azimuth(self, az=None, type='angle'):
        steps=True
        timeout=0
        
        if type=='angle':
            steps=False #We will need to tell the motionhandler whether we're specifying steps or an angle

            #First check whether we actually need to move at all.
            if az==None:
                az=int(self.active_azimuth_entries[0].get())
            if az==self.az: #No change in incidence angle, no need to move
                self.log('Goniometer remaining at an azimuth angle of '+str(az)+' degrees.')
                self.complete_queue_item()
                if len(self.queue)>0:
                    self.next_in_queue()
                return #If we're staying in the same spot, just return!
            timeout=np.abs(int(az)-int(self.az))*8+PI_BUFFER
        else:
            timeout=np.abs(int(i))/15+PI_BUFFER
            
        self.pi_commander.set_azimuth(az,type)
        handler=MotionHandler(self,label='Setting azimuth...',timeout=timeout,steps=steps, destination=az)

        if type=='angle': #Only change the visualization if an angle is specified. Specifiying steps is for setting up the 
            self.goniometer_view.set_azimuth(int(az))

        
    def move_tray(self, pos, type='position'):
        steps=False
        if type=='steps':steps=True
        self.goniometer_view.set_current_sample('Moving...')
        self.pi_commander.move_tray(pos, type)
        handler=MotionHandler(self,label='Moving sample tray...',timeout=30+BUFFER, new_sample_loc=pos, steps=steps)
        

            
    def range_setup(self,override=False):
        self.active_incidence_entries=[]
        self.active_emission_entries=[]
        self.active_azimuth_entries=[]
        
        incidence_err_str=''
        incidence_warn_str=''
        
        first_i=self.light_start_entry.get()
        valid=validate_int_input(first_i,self.min_i,self.max_i)
        if not valid: 
            incidence_err_str='Incidence must be a number from '+str(self.min_i)+' to '+str(self.max_i)+'.\n'
        else:
            first_i=int(first_i)
        final_i=self.light_end_entry.get()
        valid=validate_int_input(final_i,self.min_i,self.max_i)
        
        if not valid: 
            incidence_err_str='Incidence must be a number from '+str(self.min_i)+' to '+str(self.max_i)+'.\n'
        else:
            final_i=int(final_i)
            
        i_interval=self.light_increment_entry.get()
        valid=validate_int_input(i_interval,0,2*self.max_i)
        if not valid:
            incidence_err_str+='Incidence interval must be a number from 0 to '+str(2*self.max_i) +'.\n'
        else:
            i_interval=int(i_interval)
        incidences=[]
        if incidence_err_str=='':
            if i_interval==0:
                if first_i==final_i:
                    incidences=[first_i]
                else:
                    incidences=[first_i,final_i]
                    incidence_warn_str='Incidence interval = 0. Using first and last given incidence values.\n'
            elif final_i>first_i:
                incidences=np.arange(first_i,final_i,i_interval)
                incidences=list(incidences)
                incidences.append(final_i)
            else:
                incidences=np.arange(first_i,final_i,-1*i_interval)
                incidences=list(incidences)
                incidences.append(final_i)

        emission_err_str=''
        emission_warn_str=''
        
        first_e=self.detector_start_entry.get()
        valid=validate_int_input(first_e,self.min_e,self.max_e)
        if not valid: 
            emission_err_str='Emission must be a number from '+str(self.min_e)+' to '+str(self.max_e)+'.\n'
        else:
            first_e=int(first_e)
        final_e=self.detector_end_entry.get()
        valid=validate_int_input(final_e,self.min_e,self.max_e)
        
        if not valid: 
            emission_err_str='Emission must be a number from '+str(self.min_e)+' to '+str(self.max_e)+'.\n'
        else:
            final_e=int(final_e)
            
        e_interval=self.detector_increment_entry.get()
        valid=validate_int_input(e_interval,0,2*self.max_e)
        if not valid:
            emission_err_str+='Emission interval must be a number from 0 to '+str(2*self.max_e) +'.\n'
        else:
            e_interval=int(e_interval)
        emissions=[]
        if emission_err_str=='':
            if e_interval==0:
                if first_e==final_e:
                    emissions=[first_e]
                else:
                    emissions=[first_e,final_e]
                    emission_warn_str='Emission interval = 0. Using first and last given emission values.'
            elif final_e>first_e:
                emissions=np.arange(first_e,final_e,e_interval)
                emissions=list(emissions)
                emissions.append(final_e)
            else:
                emissions=np.arange(first_e,final_e,-1*e_interval)
                emissions=list(emissions)
                emissions.append(final_e)
                
        err_str='Error: '+incidence_err_str+emission_err_str
        if err_str!='Error: ':
            dialog=ErrorDialog(self,title='Error',label=err_str)
            return False
        warning_string=incidence_warn_str+emission_warn_str
        
        azimuth_err_str=''
        azimuth_warn_str=''
        
        first_az=self.azimuth_start_entry.get()
        valid=validate_int_input(first_az,self.min_az,self.max_az)
        if not valid: 
            azimuth_err_str='Azimuth must be a number from '+str(self.min_az)+' to '+str(self.max_az)+'.\n'
        else:
            first_az=int(first_az)
        final_az=self.azimuth_end_entry.get()
        valid=validate_int_input(final_az,self.min_az,self.max_az)
        
        if not valid: 
            azimuth_err_str='Azimuth must be a number from '+str(self.min_az)+' to '+str(self.max_az)+'.\n'
        else:
            final_az=int(final_az)
            
        az_interval=self.azimuth_increment_entry.get()
        valid=validate_int_input(az_interval,0,2*self.max_az)
        if not valid:
            azimuth_err_str+='Azimuth interval must be a number from 0 to '+str(2*self.max_az) +'.\n'
        else:
            az_interval=int(az_interval)
        azimuths=[]
        if azimuth_err_str=='':
            if az_interval==0:
                if first_az==final_az:
                    azimuths=[first_az]
                else:
                    azimuths=[first_az,final_az]
                    azimuth_warn_str='Azimuth interval = 0. Using first and last given azimuth values.'
            elif final_az>first_az:
                azimuths=np.arange(first_az,final_az,az_interval)
                azimuths=list(azimuths)
                azimuths.append(final_az)
            else:
                azimuths=np.arange(first_az,final_az,-1*az_interval)
                azimuths=list(azimuths)
                azimuths.append(final_az)
        
        for i in incidences:
            for e in emissions:
                for az in azimuths:
                    if self.validate_distance(i, e, az):
                        i_entry=PrivateEntry(str(i))
                        e_entry=PrivateEntry(str(e))
                        az_entry=PrivateEntry(str(az))
                        self.active_incidence_entries.append(i_entry)
                        self.active_emission_entries.append(e_entry)
                        self.active_azimuth_entries.append(az_entry)
                
        if warning_string=='':
            return True
        else:
            return warning_string


    #called when user clicks optimize button. No different than opt() except we clear out the queue first just in case there is something leftover hanging out in there.
    def opt_button_cmd(self):
        self.queue=[]
        self.queue.append({self.opt:[True, True]}) #Setting override and setup_complete to True make is so if we automatically retry because of an error on the spec compy we won't have to do setup things agian.
        self.acquire(override=False, setup_complete=False,action=self.opt)
     
    #called when user clicks wr button. No different than wr() except we clear out the queue first just in case there is something leftover hanging out in there.
    def wr_button_cmd(self):
        self.queue=[]
        self.queue.append({self.wr:[True,True]}) #Setting override and setup_complete to True make is so if we automatically retry because of an error on the spec compy we won't have to do setup things agian.
        self.queue.append({self.take_spectrum:[True,True,False]})
        self.acquire(override=False, setup_complete=False,action=self.wr)

    #called when user clicks take spectrum button. No different than take_spectrum() except we clear out the queue first just in case there is something leftover hanging out in there.
    def spec_button_cmd(self):
        self.queue=[]
        self.queue.append({self.take_spectrum:[False,False,False]}) #We don't automatically retry taking spectra so there is no need to have override and setup complete set to true here as for the other two above.
        self.acquire(override=False, setup_complete=False,action=self.take_spectrum,garbage=False)
        
    #commands that are put in the queue for optimizing, wr, taking a spectrum. 
    def opt(self, override=False, setup_complete=False):
        self.acquire(override=override, setup_complete=setup_complete,action=self.opt)
        
    def wr(self, override=False, setup_complete=False):
        self.acquire(override=override, setup_complete=setup_complete,action=self.wr)
        
    def take_spectrum(self, override, setup_complete, garbage):
        self.acquire(override=override, setup_complete=setup_complete,action=self.take_spectrum,garbage=garbage)
        
    
    def check_connection(self):
        self.connection_checker.check_connection(False)
    
    def configure_instrument(self):
        self.spec_commander.configure_instrument(self.instrument_config_entry.get())
        handler=InstrumentConfigHandler(self)
        
    #Set thes ave configuration for raw spectral data. First, use a remotedirectoryworker to check whether the directory exists and is writeable. If it doesn't exist, give an option to create the directory.
    def set_save_config(self):
        
        #This function gets called if the directory doesn't exist and the user clicks 'yes' for making the directory.
        def inner_mkdir(dir):
            status=self.remote_directory_worker.mkdir(dir)
            if status=='mkdirsuccess':
                self.set_save_config()
            elif status=='mkdirfailedfileexists':
                dialog=ErrorDialog(self,title='Error',label='Could not create directory:\n\n'+dir+'\n\nFile exists.')
            elif status=='mkdirfailed':
                dialog=ErrorDialog(self,title='Error',label='Could not create directory:\n\n'+dir)
                
        status=self.remote_directory_worker.get_dirs(self.spec_save_dir_entry.get())


        if status=='listdirfailed':

            if self.script_running: #If a script is running, automatically try to make the directory.
                inner_mkdir(self.spec_save_dir_entry.get())
            else: #Otherwise, ask the user first.
                buttons={
                    'yes':{
                        inner_mkdir:[self.spec_save_dir_entry.get()]
                    },
                    'no':{
                        self.reset:[]
                    }
                }
                dialog=ErrorDialog(self,title='Directory does not exist',label=self.spec_save_dir_entry.get()+'\n\ndoes not exist. Do you want to create this directory?',buttons=buttons)
            return
            
        elif status=='listdirfailedpermission':
            dialog=ErrorDialog(self,label='Error: Permission denied for\n'+self.spec_save_dir_entry.get())
            return
        
        elif status=='timeout':
            if not self.text_only:
                buttons={
                    'cancel':{},
                    'retry':{self.next_in_queue:[]}
                }
                try: #Do this if there is a wait dialog up
                    self.wait_dialog.interrupt('Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer\n computer and the spectrometer is connected.')
                    self.wait_dialog.set_buttons(buttons)#, buttons=buttons)
                    self.wait_dialog.top.geometry('376x175')
                    for button in self.wait_dialog.tk_buttons:
                        button.config(width=15)
                except:
                    dialog=ErrorDialog(self, label='Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer\n computer and the spectrometer is connected.',buttons=buttons)
                    dialog.top.geometry('376x145')
                    for button in dialog.tk_buttons:
                        button.config(width=15)
            else:
                self.log('Error: Operation timed out while trying to set save configuration')
            return

        self.spec_commander.check_writeable(self.spec_save_dir_entry.get())
        t=3*BUFFER
        while t>0:
            if 'yeswriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('yeswriteable')
                break
            elif 'notwriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('notwriteable')
                dialog=ErrorDialog(self, label='Error: Permission denied.\nCannot write to specified directory.')
                return
            time.sleep(INTERVAL)
            t=t-INTERVAL
        if t<=0:
            dialog=ErrorDialog(self,label='Error: Operation timed out.')
            return
        
        
        spec_num=self.spec_startnum_entry.get()
        while len(spec_num)<NUMLEN:
            spec_num='0'+spec_num

        self.spec_commander.set_save_path(self.spec_save_dir_entry.get(), self.spec_basename_entry.get(), self.spec_startnum_entry.get())
        handler=SaveConfigHandler(self)
        
    #when the focus is on the console entry box, the user can scroll through past commands.
    #these are stored in user_cmds with the index of the most recent command at 0
    #Every time the user enters a command, the user_cmd_index is changed to -1
    def iterate_cmds(self,keypress_event): 
        if keypress_event.keycode==111 or keypress_event.keycode==38: #up arrow on linux and windows, respectively

            if len(self.user_cmds)>self.user_cmd_index+1 and len(self.user_cmds)>0:
                self.user_cmd_index=self.user_cmd_index+1
                last=self.user_cmds[self.user_cmd_index]
                self.console_entry.delete(0,'end')
                self.console_entry.insert(0,last)

        elif keypress_event.keycode==116 or keypress_event.keycode==40: #down arrow on linux and windows, respectively
            if self.user_cmd_index>0:
                self.user_cmd_index=self.user_cmd_index-1
                next=self.user_cmds[self.user_cmd_index]
                self.console_entry.delete(0,'end')
                self.console_entry.insert(0,next)
    
    def reset(self):
        self.clear_queue()
        self.overwrite_all=False
        self.script_running=False
        self.script_failed=False
        self.white_referencing=False
        
    #execute a command either input into the console by the user or loaded from a script
    def execute_cmd(self,event):
        if self.script_running:
            self.complete_queue_item()
        #self.cmd_complete=False

            
        self.text_only=True
        command=self.console_entry.get()
        self.user_cmds.insert(0,command)
        self.user_cmd_index=-1
        if command !='end file':
            self.console_log.insert(END,'>>> '+command+'\n')
        self.console_entry.delete(0,'end')
        thread=Thread(target=self.execute_cmd_2,kwargs={'cmd':command})
        thread.start()
    
    def execute_cmd_2(self,cmd): #In a separate method because that allows it to be spun off in a new thread, so tkinter mainloop continues, which means that the console log gets updated immediately e.g. if you say sleep(10) it will say sleep up in the log while it is sleeping.
        print('Command is: '+cmd)
        
        def get_val(param):
            return param.split('=')[1].strip(' ').strip('"').strip("'")
            
        if cmd=='wr()':
            if not self.script_running:
                self.queue=[]
            self.queue.insert(0,{self.wr:[True,False]})
            self.queue.insert(1,{self.take_spectrum:[True,True,False]})
            self.wr(True,False)
        elif cmd=='opt()':
            if not self.script_running:
                self.queue=[]
            self.queue.insert(0,{self.opt:[True, False]})
            self.opt(True, False) #override=True, setup complete=False
        elif cmd=='goniometer.configure(MANUAL)':
            self.set_manual_automatic(force=0)

        elif 'goniometer.configure(' in cmd:
            try:
                if 'AUTOMATIC' in cmd:
                    #e.g. goniometer.configure(AUTOMATIC,-30,50,wr)
                    params=cmd[0:-1].split('goniometer.configure(AUTOMATIC')[1].split(',')[1:]
                    for i in range(len(params)):
                        params[i]=params[i].strip(' ')
                elif 'MANUAL' in cmd:
                    params=cmd[0:-1].split('goniometer.configure(MANUAL')[1].split(',')[1:]
                    params.append(1)
                else:
                    self.log('Error: invalid arguments for mode, i, e, sample_num: '+str(params)+'\nExample input: goniometer.configure(AUTOMATIC, 0, 20, wr)')
                    self.queue=[]
                    self.script_running=False
                valid_i=validate_int_input(params[0],self.min_i,self.max_i)
                valid_e=validate_int_input(params[1],self.min_e,self.max_e)

                valid_sample=validate_int_input(params[2],1,int(self.num_samples))
                if params[2]=='wr':
                    valid_sample=True
                if valid_i and valid_e and valid_sample:
                    self.i=params[0]
                    self.e=params[1]
                    if params[2]=='wr':
                        self.sample_tray_index=-1
                    else:
                        self.sample_tray_index=int(params[2])-1 #this is used as an index where available_sample_positions[4]=='Sample 5' so it should be one less than input.
                    
                    if 'AUTOMATIC' in cmd:
                        self.set_manual_automatic(force=1, known_goniometer_state=True)
                    else:
                        self.set_manual_automatic(force=0)
                    self.incidence_entries[0].delete(0,'end')
                    self.incidence_entries[0].insert(0,params[0])
                    self.emission_entries[0].delete(0,'end')
                    self.emission_entries[0].insert(0,params[1])
                    self.configure_pi(params[0],params[1],params[2], params[3])

                else:
                    self.log('Error: invalid arguments for mode, i, e, sample_num: '+str(params)+'\nExample input: goniometer.configure(AUTOMATIC, 0, 20, wr)')
                    self.queue=[]
                    self.script_running=False
            except Exception as e:
                self.log('Error: Could not parse command '+cmd)
                self.queue=[]
                self.script_running=False
                print(e)
        elif cmd=='collect_garbage()':
            if not self.script_running:
                self.queue=[]
            self.queue.insert(0,{self.take_spectrum:[True,False,True]})
            self.take_spectrum(True,False,True)
        elif cmd =='acquire()':
            if not self.script_running:
                self.queue=[]
            self.acquire()
        elif cmd=='take_spectrum()':
            if not self.script_running:
                self.queue=[]
            self.queue.insert(0,{self.take_spectrum:[True,True,False]})
            self.take_spectrum(True,True,False)
        #e.g. set_spec_save(directory=R:\RiceData\Kathleen\test_11_15, basename=test,num=0000) 
        elif 'setup_geom(' in cmd: #params are i, e, index=0
            params=cmd[0:-1].split('setup_geom(')[1].split(',')
            if len(params)!=2 and len(params)!=3:
                self.log('Error: could not parse command '+cmd)
            elif self.manual_automatic.get()==0: #manual mode
                valid_i=validate_int_input(params[0],-90,90)
                valid_e=validate_int_input(params[1],-90,90)
                if not valid_i or not valid_e:
                    self.log('Error: i='+params[0]+', e='+params[1]+' is not a valid viewing geometry.')
                else:
                    self.incidence_entries[0].delete(0,'end')
                    self.incidence_entries[0].insert(0,params[0])
                    self.emission_entries[0].delete(0,'end')
                    self.emission_entries[0].insert(0,params[1])
            else: #automatic mode
                valid_i=validate_int_input(params[0],self.min_i,self.max_i)
                valid_e=validate_int_input(params[1],self.min_e,self.max_e)
                if not valid_i or not valid_e:
                    self.log('Error: i='+params[0]+', e='+params[1]+' is not a valid viewing geometry.')
                else:
                    index=0
                    if len(params)==3:
                        index=int(get_val(params[2]))
                    valid_index=validate_int_input(index, 0, len(self.emission_entries)-1)
                    if not valid_index:
                        self.log('Error: '+str(index)+' is not a valid index. Enter a value from 0-'+str(len(self.emission_entries)-1))
                    else:
                        self.incidence_entries[index].delete(0,'end')
                        self.incidence_entries[index].insert(0,params[0])
                        self.emission_entries[index].delete(0,'end')
                        self.emission_entries[index].insert(0,params[1])
        elif 'add_geom(' in cmd: #params are i, e. Will not overwrite existing geom.
            params=cmd[0:-1].split('add_geom(')[1].split(',')
            if len(params)!=2:
                self.log('Error: could not parse command '+cmd)
            elif self.manual_automatic.get()==0: #manual mode
                valid_i=validate_int_input(params[0],-90,90)
                valid_e=validate_int_input(params[1],-90,90)
                if not valid_i or not valid_e:
                    self.log('Error: i='+params[0]+', e='+params[1]+' is not a valid viewing geometry.')
                elif self.emission_entries[0].get()=='' and self.incidence_entries[0].get()=='':
                    self.incidence_entries[0].insert(0,params[0])
                    self.emission_entries[0].insert(0,params[1])
                else:
                    self.log('Error: Cannot add second geometry in manual mode.')
            else: #automatic mode
                if self.individual_range.get()==1:
                    self.log('Error: Cannot add geometry in range mode. Use setup_geom_range() instead')
                else:
                    valid_i=validate_int_input(params[0],self.min_i,self.max_i)
                    valid_e=validate_int_input(params[1],self.min_e,self.max_e)
                    if not valid_i or not valid_e:
                        self.log('Error: i='+params[0]+', e='+params[1]+' is not a valid viewing geometry.')
                    elif self.emission_entries[0].get()=='' and self.incidence_entries[0].get()=='':
                        self.incidence_entries[0].insert(0,params[0])
                        self.emission_entries[0].insert(0,params[1])
                    else:
                        self.add_geometry()
                        self.incidence_entries[-1].insert(0,params[0])
                        self.emission_entries[-1].insert(0,params[1])
            
                    


        elif 'setup_geom_range(' in cmd:
            if self.manual_automatic.get()==0:
                self.log('Error: Not in automatic mode')
                self.queue=[]
                self.script_running=False
                return False
            self.set_individual_range(force=1)
            params=cmd[0:-1].split('setup_geom_range(')[1].split(',')
            for param in params:
                if 'i_start' in param:
                    try:
                        self.light_start_entry.delete(0,'end')
                        self.light_start_entry.insert(0,get_val(param))
                    except:
                        self.log('Error: Unable to parse initial incidence angle')
                        self.queue=[]
                        self.script_running=False
                elif 'i_end' in param:
                    try:
                        self.light_end_entry.delete(0,'end')
                        self.light_end_entry.insert(0,get_val(param))
                    except:
                        self.log('Error: Unable to parse final incidence angle')
                        self.queue=[]
                        self.script_running=False
                elif 'e_start' in param:
                    try:
                        self.detector_start_entry.delete(0,'end')
                        self.detector_start_entry.insert(0,get_val(param))
                    except:
                        self.log('Error: Unable to parse initial emission angle')
                        self.queue=[]
                        self.script_running=False
                elif 'e_end' in param:
                    try:
                        self.detector_end_entry.delete(0,'end')
                        self.detector_end_entry.insert(0,get_val(param))
                    except:
                        self.log('Error: Unable to parse final emission angle')
                        self.queue=[]
                        self.script_running=False
                elif 'i_increment' in param:
                    try:
                        self.light_increment_entry.delete(0,'end')
                        self.light_increment_entry.insert(0,get_val(param))
                    except:
                        self.log('Error: Unable to parse incidence angle increment.')
                        self.queue=[]
                        self.script_running=False
                elif 'e_increment' in param:
                    try:
                        self.detector_increment_entry.delete(0,'end')
                        self.detector_increment_entry.insert(0,get_val(param))
                    except:
                        self.log('Error: Unable to parse emission angle increment.')
                        self.queue=[]
                        self.script_running=False
            if len(self.queue)>0:
                self.next_in_queue()
        elif 'set_samples(' in cmd:
            params=cmd[0:-1].split('set_samples(')[1].split(',')
            if params==['']:params=[]

            #First clear all existing sample names
            while len(self.sample_frames)>1:
                self.remove_sample(-1)
            print('clearing')
            self.set_text(self.sample_label_entries[0],'')
            
            #Then add in samples in order specified in params. Each param should be a sample name and pos.
            skip_count=0 #If a param is badly formatted, we'll skip it. Keep track of how many are skipped in order to index labels, etc right.
            for i, param in enumerate(params):
                
                try:
                    pos=param.split('=')[0].strip(' ')
                    name=get_val(param)
                    valid_pos=validate_int_input(pos,1,5)
                    if self.available_sample_positions[int(pos)-1] in self.taken_sample_positions: #If the requested position is already taken, we're not going to allow it.
                        if len(self.sample_label_entries)>1: #If only one label is out there, it will be listed as taken even though the entry is empty, so we can ignore it. But if there is more than one label, we know the position is a repeat and not valid.
                            valid_pos=False
                        elif self.sample_label_entries[0].get()!='': #Even if there is only one label, if the entry has already been filled in then the position is a repeat and not valid.
                            valid_pos=False
                    if i-skip_count!=0 and valid_pos:
                        self.add_sample()
                except: #If the position isn't specified, fail.
                    self.log('Error: could not parse command '+cmd+'. Use the format set_samples({position}={name}) e.g. set_samples(1=Basalt)')
                    skip_count+=1

                if valid_pos:
                    print('setting')
                    self.set_text(self.sample_label_entries[i-skip_count], name)
                    self.sample_pos_vars[i-skip_count].set(self.available_sample_positions[int(pos)-1])
                    self.set_taken_sample_positions()
                else:
                    self.log('Error: '+pos+' is an invalid sample position. Use the format set_samples({name}={position}) e.g. set_samples(Basalt=1). Do not repeat sample positions.')
                    skip_count+=1
                
            if len(self.queue)>0:
                self.next_in_queue()
                
        elif 'set_spec_save(' in cmd:
            self.unfreeze()
            params=cmd[0:-1].split('set_spec_save(')[1].split(',')
            
            for i, param in enumerate(params):
                params[i]=param.strip(' ') #Need to do this before looking for setup only
                if 'directory' in param:
                    dir=get_val(param)
                    self.spec_save_dir_entry.delete(0,'end')
                    self.spec_save_dir_entry.insert(0,dir)
                elif 'basename' in param:
                    basename=get_val(param)
                    self.spec_basename_entry.delete(0,'end')
                    self.spec_basename_entry.insert(0,basename)
                elif 'num' in param:
                    num=get_val(param)
                    self.spec_startnum_entry.delete(0,'end')
                    self.spec_startnum_entry.insert(0,num)
                    
            if not self.script_running:
                self.queue=[]
                
            #If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI is just filled in for them how they want.
            setup_only=False

                
            if 'setup_only=True' in params: setup_only=True
            elif 'setup_only =True' in params: setup_only=True
            elif 'setup_only = True' in params: setup_only=True
            
            if not setup_only:
                self.queue.insert(0,{self.set_save_config:[]})
                self.set_save_config()
            elif len(self.queue)>0:
                self.next_in_queue()
        elif 'instrument.configure('in cmd:
            params=cmd[0:-1].split('instrument.configure(')[1].split(',')
            for i, param in enumerate(params):
                params[i]=param.strip(' ') #needed when we check for setup_only
            try:
                num=int(params[0])
                self.instrument_config_entry.delete(0,'end')
                self.instrument_config_entry.insert(0,str(num))
                if not self.script_running:
                    self.queue=[]
                    
                #If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI is just filled in for them how they want.
                setup_only=False
                if 'setup_only=True' in params: setup_only=True
                elif 'setup_only =True' in params: setup_only=True
                elif 'setup_only = True' in params: setup_only=True
                
                if not setup_only:
                    self.queue.insert(0,{self.configure_instrument:[]})
                    self.configure_instrument()
                elif len(self.queue)>0:
                    self.next_in_queue()
            except:
                self.log('Error: could not parse command '+cmd)
                self.queue=[]
                self.script_running=False
                    

        elif 'sleep' in cmd:
            param=cmd[0:-1].split('sleep(')[1]
            try:
                num=float(param)
                print('wait dialog')
                print(self.wait_dialog)
                try:
                    title='Sleeping...'
                    label='Sleeping...'
                    self.wait_dialog.reset(title=title, label=label)
                except:
                    pass #If there isn't already a wait dialog up, don't create one.
                elapsed=0
                while elapsed<num-10:
                    time.sleep(10)
                    elapsed+=10
                    self.console_log.insert(END,'\t'+str(elapsed))
                remaining=num-elapsed
                time.sleep(remaining)
                #self.cmd_complete==True
                self.console_log.insert(END,'\tDone sleeping.\n')
                if len(self.queue)>0:
                    self.next_in_queue()
            except:
                self.log('Error: could not parse command '+cmd)
                self.queue=[]
                self.script_running=False
            
                
        elif 'move_tray(' in cmd:
            if self.manual_automatic.get()==0:
                self.log('Error: Not in automatic mode')
                return False
            try:
                param=cmd.split('move_tray(')[1].strip(')')
            except:
                self.log('Error: Could not parse command '+cmd)
                self.queue=[]
                self.script_running=False
                return False
            if 'steps' in param:
                try:
                    steps=int(param.split('=')[-1])
                    valid_steps=validate_int_input(steps,-800,800)

                except:
                    self.log('Error: could not parse command '+cmd)
                    self.queue=[]
                    self.script_running=False
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue=[]
                    self.queue.insert(0,{self.move_tray:[steps,'steps']})
                    self.move_tray(steps,type='steps')
                else:
                    self.log('Error: '+str(steps) +' is not a valid number of steps. Enter an integer from -800 to 800.')
                    self.queue=[]
                    self.script_running=False
                    return False
            else:
                pos=param
                print(pos)
                alternatives=['1','2','3','4','5'] #These aren't how sample positions are specified in available_sample_positions (which has Sample 1, etc) but we'll accept them.
                if pos in alternatives:
                    pos=self.available_sample_positions[alternatives.index(pos)]
                elif pos.lower()=='wr':
                    pos=pos.lower()
                if pos in self.available_sample_positions or pos=='wr':
    
                    if not self.script_running:
                        self.queue=[]
                    self.queue.insert(0,{self.move_tray:[pos]})
                    self.move_tray(pos)
                else:
                    self.log('Error: '+pos+' is an invalid tray position')
                    self.queue=[]
                    self.script_running=False
                    return False
                
        elif 'set_emission(' in cmd: 
            if self.manual_automatic.get()==0:
                self.log('Error: Not in automatic mode')
                self.queue=[]
                self.script_running=False
                return False
            try:
                param=cmd.split('set_emission(')[1][:-1]
                
            except:
                self.log('Error: could not parse command '+cmd)
                self.queue=[]
                self.script_running=False
                return False
                
            if 'steps' in param:
                try:
                    steps=int(param.split('=')[-1])
                    valid_steps=validate_int_input(steps,-1000,1000)

                except:
                    self.log('Error: could not parse command '+cmd)
                    self.queue=[]
                    self.script_running=False
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue=[]
                    self.queue.insert(0,{self.move_detector:[steps,'steps']})
                    self.move_detector(steps,'steps')
                else:
                    self.log('Error: '+str(steps) +' is not a valid number of steps. Enter an integer from -1000 to 1000.')
                    self.queue=[]
                    self.script_running=False
                    return False  
            else:
                e=param
                valid_e=validate_int_input(e, self.min_e, self.max_e)
                if valid_e:
                    print('here')
                    if int(e)<int(self.i)+15:
                        self.log('Error: Because of geometric constraints on the instrument, the emission angle must be at least '+str(self.required_angular_separation)+' degrees different than the incidence angle.')
                        self.queue=[]
                        self.script_running=False
                        return False
    
                    if not self.script_running:
                        self.queue=[]
                    self.queue.insert(0,{self.move_detector:[e]})
                    self.move_detector(e)
                    print('moving detector!')
                else:
                    self.log('Error: '+e+' is an invalid emission angle.')
                    self.queue=[]
                    self.script_running=False
                    return False
                    
                
        elif 'set_incidence(' in cmd: 
            if self.manual_automatic.get()==0:
                self.log('Error: Not in automatic mode')
                self.queue=[]
                self.script_running=False
                return False
            try:
                param=cmd.split('set_incidence(')[1][:-1]
                
            except:
                self.log('Error: could not parse command '+cmd)
                self.queue=[]
                self.script_running=False
                return False
                
            if 'steps' in param:
                try:
                    steps=int(param.split('=')[-1])
                    valid_steps=validate_int_input(steps,-1000,1000)

                except:
                    self.log('Error: could not parse command '+cmd)
                    self.queue=[]
                    self.script_running=False
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue=[]
                    self.queue.insert(0,{self.move_light:[steps,'steps']})
                    self.move_light(steps,'steps')
                else:
                    self.log('Error: '+str(steps) +' is not a valid number of steps. Enter an integer from -1000 to 1000.')
                    self.queue=[]
                    self.script_running=False
                    return False  
            else:
                i=param
                valid_i=validate_int_input(i, self.min_i, self.max_i)
                if valid_i:
                    if int(i)>int(self.e)-15:
                        self.log('Error: Because of geometric constraints on the instrument, the emission angle must be at least '+str(self.required_angular_separation)+' degrees different than the incidence angle.')
                        return False
    
                    if not self.script_running:
                        self.queue=[]
                    self.queue.insert(0,{self.move_light:[i]})
                    self.move_light(i)
                else:
                    self.log('Error: '+i+' is an invalid incidence angle.')
                    self.queue=[]
                    self.script_running=False
                    return False
        elif 'set_display' in cmd:
            params=cmd.split('set_display(')[1].strip(')').split(',')
            if len(params)!=3:
                self.log(str(len(params)))
                self.log('Error: invalid display setting. Enter set_display(i, e, az')
                return 

            for n, angle in enumerate(params[0:2]):
                valid=validate_int_input(angle, -90, 90)
                if not valid:
                    print(angle)
                    self.log('Error: invalid geometry')
                    return 
                else:
                    params[n]=int(params[n])
                    
            valid=validate_int_input(params[2],-90,270)
            if not valid:
                self.log('Error: invalid geometry')
                return 
            else:
                params[2]=int(params[2])
            
            i=params[0]
            e=params[1]
            az=params[2]
            collision=False
            valid_geom=self.validate_distance(i,e,az)
            
            pos, dist=self.get_closest_approach(i, e, az)
            if dist<self.required_angular_separation:
                collision=True
            

            
#             self.goniometer_view.set_incidence(i)
#             self.goniometer_view.set_emission(e)
#             self.goniometer_view.set_azimuth(az)
#             return
            current_motor=(self.goniometer_view.motor_i,self.goniometer_view.motor_e, self.goniometer_view.motor_az)
            movements=self.get_movement_order(i,e,az, current_motor=current_motor)

            print('*********************')
            print(movements)
            if movements==None:
                print('NO PATH FOUND')
                self.goniometer_view.set_azimuth(az)
                self.goniometer_view.set_incidence(i)
                self.goniometer_view.set_emission(e)
            else:
                temp_queue=[]
                for _ in range(len(movements)):
                    temp_queue.append({})
                if 'az+180' in movements:
                    temp_queue.insert(movements.index('az+180'), {self.goniometer_view.set_azimuth:[az+180]})
                if 'az-180' in movements:
                    temp_queue.insert(movements.index('az-180'), {self.goniometer_view.set_azimuth:[az-180]})
                if 'az' in movements:
                    temp_queue[movements.index('az')]= {self.goniometer_view.set_azimuth:[az]}
                if 'temp i' in movements:

                    current_science_e=current_motor[1]
                    if current_science_e>=0:
                        temp_i=-1*(current_science_e+2*self.required_angular_separation)
                    else:
                        temp_i=-1*(current_science_e-2*self.required_angular_separation)
                        
                    if current_motor[2]>=180 or current_motor[2]<0:
                        temp_i=-1*temp_i
                    print('CURRENT MOTOR I: '+str(current_motor[0]))
                    print('TEMP I: '+str(temp_i))
                        
                    temp_queue[movements.index('temp i')]= {self.goniometer_view.set_incidence:[temp_i]}
                if '-temp i' in movements:
                    current_science_e=current_motor[1]
                    if current_science_e>=0:
                        temp_i=(current_science_e+2*self.required_angular_separation)
                    else:
                        temp_i=(current_science_e-2*self.required_angular_separation)
                        
                    if current_motor[2]>=180 or current_motor[2]<0:
                        temp_i=-1*temp_i
                    print('CURRENT MOTOR I: '+str(current_motor[0]))
                    print('TEMP I: '+str(temp_i))
                        
                    temp_queue[movements.index('-temp i')]= {self.goniometer_view.set_incidence:[temp_i]}

                if 'i 10' in movements:
                    temp_queue[movements.index('i 10')]={self.goniometer_view.set_incidence:[10]}
                if 'az motor 90' in movements:
                    temp_queue[movements.index('az motor 90')]={self.goniometer_view.set_azimuth:[90]}
                if 'az -90' in movements:
                    temp_queue[movements.index('az 90')]={self.goniometer_view.set_azimuth:[-90]}
                if 'e' in movements:
                    temp_queue[movements.index('e')]={self.goniometer_view.set_emission:[e]}
                     
                if 'i' in movements:
                    temp_queue[movements.index('i')]={self.goniometer_view.set_incidence:[i]}
                     
                if '-i' in movements:
                    temp_queue[movements.index('-i')]={self.goniometer_view.set_incidence:[-1*i]}
                
                print(temp_queue)
    
                for item in temp_queue:
                    for func in item:
                        args=item[func]
                        func(*args)
                    
            print('MOTOR AZ: '+str(self.goniometer_view.motor_az))
            print('MOTOR I: '+str(self.goniometer_view.motor_i))
            if len(self.queue)>0:
                self.next_in_queue()
            else:
                self.script_running=False
                self.queue=[]
            
        elif 'rotate_display' in cmd:
            angle=cmd.split('rotate_display(')[1].strip(')')
            valid=validate_int_input(angle, -360, 360)
            if not valid:
                self.log('Error: invalid geometry')
                return 
            else:
                angle=int(angle)
            
            self.goniometer_view.set_goniometer_tilt(0)
            
            self.goniometer_view.wireframes['i'].rotate_az(angle)
            self.goniometer_view.wireframes['light'].rotate_az(angle)
            self.goniometer_view.wireframes['light guide'].rotate_az(angle)
            
            self.goniometer_view.wireframes['e'].rotate_az(angle)
            self.goniometer_view.wireframes['detector'].rotate_az(angle)
            self.goniometer_view.wireframes['detector guide'].rotate_az(angle)
            
            self.goniometer_view.set_goniometer_tilt(20)
            
            self.goniometer_view.draw_3D_goniometer(self.goniometer_view.width, self.goniometer_view.height)
            self.goniometer_view.flip()
            
        elif 'rotate_tray_display' in cmd:
            angle=cmd.split('rotate_tray_display(')[1].strip(')')
            valid=validate_int_input(angle, -360, 360)
            if not valid:
                self.log('Error: invalid geometry')
                return 
            else:
                angle=int(angle)
            self.goniometer_view.rotate_tray(angle)
            self.goniometer_view.draw_3D_goniometer(self.goniometer_view.width, self.goniometer_view.height)
            self.goniometer_view.flip()
            
        elif cmd=='end file':
            self.script_running=False
            self.queue=[]
            try:
                self.wait_dialog.interrupt('Success!') #If there is a wait dialog up, make it say success. There may never have been one that was made though.
            except:
                pass
            return True
                
        else:
            self.log('Error: could not parse command '+cmd)
            self.queue=[]
            self.script_running=False
            return False
            
        self.text_only=False
        return True
            
            
    def increment_num(self):
        try:
            num=int(self.spec_startnum_entry.get())+1
            self.spec_startnum_entry.delete(0,'end')
            self.spec_startnum_entry.insert(0,str(num))
        except:
            return
    
    def move(self):
        try:
            incidence=int(man_light_entry.get())
            emission=int(man_detector_entry.get())
        except:
            return
        if incidence<0 or incidence>90 or emission<0 or emission>90:
            return
        # self.model.move_light(i)
        # self.model.move_detector(e)
    
        

    def check_local_folder(self,dir, next_action):
        def try_mk_dir(dir, next_action):
            try:
                os.makedirs(dir)
                next_action()
            except Exception as e:
                dialog=ErrorDialog(self, title='Cannot create directory',label='Cannot create directory:\n\n'+dir)
            return False
        exists=os.path.exists(dir)
        if exists:
            #If the file exists, try creating and deleting a new file there to make sure we have permission.
            try:
                if self.opsys=='Linux' or self.opsys=='Mac':
                    if dir[-1]!='/':
                        dir+='/'
                else:
                    if dir[-1]!='\\':
                        dir+='\\'
                
                existing=os.listdir(dir)
                i=0
                delme='delme'+str(i)
                while delme in existing:
                    
                    i+=1
                    delme='delme'+str(i)
                    print(dir+delme)
                    
                os.mkdir(dir+delme)
                os.rmdir(dir+delme)
                return True
                
            except:
                dialog=ErrorDialog(self,title='Error: Cannot write',label='Error: Cannot write to specified directory.\n\n'+dir)
                return False
        else:
            if self.script_running: #If we're running a script, just try making the directory automatically.
                try_mk_dir(dir,next_action)
            else: #Otherwise, ask the user.
                buttons={
                    'yes':{
                        try_mk_dir:[dir,next_action]
                    },
                    'no':{
                    }
                }
                dialog=ErrorDialog(self,title='Directory does not exist',label=dir+'\n\ndoes not exist. Do you want to create this directory?',buttons=buttons)
        return exists
        
    #Checks if the given directory exists and is writeable. If not writeable, gives user option to create.
    def check_remote_folder(self,dir,next_action):
    
        def inner_mkdir(dir,next_action):
            status=self.remote_directory_worker.mkdir(dir)
            if status=='mkdirsuccess':
                next_action()
            elif status=='mkdirfailedfileexists':
                dialog=ErrorDialog(self,title='Error',label='Could not create directory:\n\n'+dir+'\n\nFile exists.')
            elif status=='mkdirfailed':
                dialog=ErrorDialog(self,title='Error',label='Could not create directory:\n\n'+dir)
                
        status=self.remote_directory_worker.get_dirs(self.spec_save_dir_entry.get())

        if status=='listdirfailed':
            buttons={
                'yes':{
                    inner_mkdir:[dir,next_action]
                },
                'no':{
                }
            }
            dialog=ErrorDialog(self,title='Directory does not exist',label=dir+'\ndoes not exist. Do you want to create this directory?',buttons=buttons)
            return False
        elif status=='listdirfailedpermission':
            dialog=ErrorDialog(self,label='Error: Permission denied for\n'+dir)
            return False
        
        elif status=='timeout':
            if not self.text_only:
                buttons={
                    'cancel':{},
                    'retry':{self.next_in_queue:[]}
                }
                dialog=ErrorDialog(self, label='Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer\n computer and the spectrometer is connected.', buttons=buttons)
                for button in dialog.tk_buttons:
                    button.config(width=15)
            else:
                self.log('Error: Operation timed out.')
            return False
            
        self.spec_commander.check_writeable(dir)
        t=3*BUFFER
        while t>0:
            if 'yeswriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('yeswriteable')
                return True
            elif 'notwriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('notwriteable')
                dialog=ErrorDialog(self, label='Error: Permission denied.\nCannot write to specified directory.')
                return False
            time.sleep(INTERVAL)
            t=t-INTERVAL
        if t<=0:
            dialog=ErrorDialog(self,label='Error: Operation timed out.')
            return False
            
            
    def check_local_file(self,directory,file,next_action):
        def remove_retry(file,next_action):
            try:
                os.remove(file)
                next_action()
            except:
                dialog=ErrorDialog(self,title='Error overwriting file',label='Error: Could not delete file.\n\n'+file)
                
        
        if self.opsys=='Linux' or self.opsys=='Mac':
            if directory[-1]!='/':
                directory+='/'
        else:
            if directory[-1]!='\\':
                directory+='\\'
                
        self.full_process_output_path=directory+file
        if os.path.exists(self.full_process_output_path):
            buttons={
                'yes':{
                    remove_retry:[self.full_process_output_path,next_action]
                    },
                'no':{
                }
            }
            dialog=Dialog(self,title='Error: File Exists',label='Error: Specified output file already exists.\n\n'+self.full_process_output_path+'\n\nDo you want to overwrite this data?',buttons=buttons)
            dialog.geometry('376x175')
            return False
        else:
            return True
        
    def process_cmd(self):

        output_file=self.output_file_entry.get()

        if output_file=='':
            dialog=ErrorDialog(self, label='Error: Enter an output file name')
            return
        
        if output_file[-4:]!='.csv': 
            output_file=output_file+'.csv'
            self.output_file_entry.insert('end','.csv')
        
        self.full_process_output_path=output_file
        
        input_directory=self.input_dir_entry.get()
        if input_directory[-1]=='\\':
            input_directory=input_directory[:-1]
            print('MODIFYING input DIRECTORY')
            print(input_directory)
    
        if self.proc_local.get()==1:
            print('local 1')
            self.plot_local_remote='local'

            check=self.check_local_file(self.output_dir_entry.get(),output_file,self.process_cmd)
            if not check: return #If the file exists, controller.check_local_file_exists gives the user the option to overwrite, in which case process_cmd gets called again.
            check=self.check_local_folder(self.output_dir_entry.get(),self.process_cmd)
            if not check: return #Same deal for the folder (except existing is good).

            self.spec_commander.process(input_directory,'spec_share_loc','proc_temp.csv')

        else:
            print('remote 1')
            self.plot_local_remote='remote'
            output_directory=self.output_dir_entry.get()             
            check=self.check_remote_folder(output_directory,self.process_cmd)
            if not check:
                return


            self.spec_commander.process(input_directory, output_directory, output_file)
            
        if self.process_save_dir.get():
            file=open(self.local_config_loc+'process_directories.txt','w')
            file.write(self.plot_local_remote+'\n')
            file.write(self.input_dir_entry.get()+'\n')
            file.write(self.output_dir_entry.get()+'\n')
            file.write(output_file+'\n')
            file.close()
            
        self.queue.insert(0,{self.process_cmd:[]})
        self.queue.insert(1,{self.finish_process:[output_file]})
        process_handler=ProcessHandler(self)
        
        
        
    def finish_process(self,output_file):
        print('finishing processing')
        self.complete_queue_item()
        #We're going to transfer the data file and log file to the final destination. To transfer the log file, first decide on a name to call it. This will be based on the dat file name. E.g. foo.csv would have foo_log.txt associated with it.
        final_data_destination=self.output_file_entry.get()
        print(final_data_destination)
        if '.' not in final_data_destination:
            final_data_destination=final_data_destination+'.csv'
        data_base='.'.join(final_data_destination.split('.')[0:-1])
        log_base=''
            
        if self.opsys=='Linux' or self.opsys=='Mac':
            final_data_destination=self.output_dir_entry.get()+'/'+final_data_destination
            log_base=self.output_dir_entry.get()+'/'+data_base+'_log'
        else:
            final_data_destination=self.output_dir_entry.get()+'\\'+final_data_destination
            log_base=self.output_dir_entry.get()+'\\'+data_base+'_log'

            
        final_log_destination=log_base
        i=1
        while os.path.isfile(final_log_destination+'.txt'):
            final_log_destination=log_base+'_'+str(i)
            i+=1
        final_log_destination+='.txt'
        print('moving data to '+final_data_destination)
        shutil.move(self.spec_temp_loc+'proc_temp.csv',final_data_destination)
        print('moving log to '+final_log_destination)
        shutil.move(self.spec_temp_loc+'proc_temp_log.txt',final_log_destination)
        
    def open_options(self, tab,current_title):
        #If the user already has dialogs open for editing the plot, close the extras to avoid confusion.
        try:
            self.analysis_dialog.top.destroy()
        except:
            pass
        try:
            self.edit_plot_dialog.top.destroy()
        except:
            pass        
        try:
            self.plot_options_dialog.top.destroy()
        except:
            pass
        def select_tab():
            self.view_notebook.select(tab.top)
        buttons={
            'ok':{
                select_tab:[],
                lambda: tab.set_title(self.new_plot_title_entry.get()):[]
            }
        }
        
        def apply_x():
            self.view_notebook.select(tab.top)

            try:
                x1=float(self.left_zoom_entry.get())
                x2=float(self.right_zoom_entry.get())
                tab.adjust_x(x1,x2)
            except:
                ErrorDialog(self, title='Invalid Zoom Range',label='Error: Invalid x limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
                
        def apply_y():
            self.view_notebook.select(tab.top)
            try:
                y1=float(self.left_zoom_entry2.get())
                y2=float(self.right_zoom_entry2.get())
                tab.adjust_y(y1,y2)
            except Exception as e:
                print(e)
                ErrorDialog(self, title='Invalid Zoom Range',label='Error! Invalid y limits: '+self.left_zoom_entry2.get()+', '+self.right_zoom_entry2.get())
                
        def apply_z():
            self.view_notebook.select(tab.top)

            try:
                z1=float(self.left_zoom_entry_z.get())
                z2=float(self.right_zoom_entry_z.get())
                tab.adjust_z(z1,z2)
            except Exception as e:
                print(e)
                ErrorDialog(self, title='Invalid Zoom Range',label='Error: Invalid z limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
        
        self.plot_options_dialog=Dialog(self,'Plot Options','\nPlot title:',buttons=buttons)
        self.new_plot_title_entry=Entry(self.plot_options_dialog.top, width=20, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.new_plot_title_entry.insert(0,current_title)
        self.new_plot_title_entry.pack()
        
        self.outer_outer_zoom_frame=Frame(self.plot_options_dialog.top,bg=self.bg,padx=self.padx,pady=15)
        self.outer_outer_zoom_frame.pack(expand=True,fill=BOTH)

        self.zoom_title_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg)
        self.zoom_title_frame.pack(pady=(5,10))
        self.zoom_title_label=Label(self.zoom_title_frame,text='Adjust plot x and y limits:',bg=self.bg,fg=self.textcolor)
        self.zoom_title_label.pack(side=LEFT,pady=(0,4)) 
        
        self.outer_zoom_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.outer_zoom_frame.pack(expand=True,fill=BOTH,pady=(0,10))
        self.zoom_frame=Frame(self.outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.zoom_frame.pack()
        
        self.zoom_label=Label(self.zoom_frame,text='x1:',bg=self.bg,fg=self.textcolor)
        self.left_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_label2=Label(self.zoom_frame,text='x2:',bg=self.bg,fg=self.textcolor)
        self.right_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_button=Button(self.zoom_frame,text='Apply',  command=apply_x,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.zoom_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.zoom_button.pack(side=RIGHT,padx=(10,10))
        self.right_zoom_entry.pack(side=RIGHT,padx=self.padx)
        self.zoom_label2.pack(side=RIGHT,padx=self.padx)
        self.left_zoom_entry.pack(side=RIGHT,padx=self.padx)
        self.zoom_label.pack(side=RIGHT,padx=self.padx)
        
        
        self.outer_zoom_frame2=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.outer_zoom_frame2.pack(expand=True,fill=BOTH,pady=(0,10))
        self.zoom_frame2=Frame(self.outer_zoom_frame2,bg=self.bg,padx=self.padx)
        self.zoom_frame2.pack()
        self.zoom_label3=Label(self.zoom_frame2,text='y1:',bg=self.bg,fg=self.textcolor)
        self.left_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_label4=Label(self.zoom_frame2,text='y2:',bg=self.bg,fg=self.textcolor)
        self.right_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_button2=Button(self.zoom_frame2,text='Apply',  command=apply_y,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.zoom_button2.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        
        self.zoom_button2.pack(side=RIGHT,padx=(10,10))
        self.right_zoom_entry2.pack(side=RIGHT,padx=self.padx)
        self.zoom_label4.pack(side=RIGHT,padx=self.padx)
        self.left_zoom_entry2.pack(side=RIGHT,padx=self.padx)
        self.zoom_label3.pack(side=RIGHT,padx=self.padx)
        
        self.outer_zoom_frame_z=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.outer_zoom_frame_z.pack(expand=True,fill=BOTH,pady=(0,10))
        self.zoom_frame_z=Frame(self.outer_zoom_frame_z,bg=self.bg,padx=self.padx)
        self.zoom_frame_z.pack()
        self.zoom_label_z1=Label(self.zoom_frame_z,text='z1:',bg=self.bg,fg=self.textcolor)
        self.left_zoom_entry_z=Entry(self.zoom_frame_z, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_label_z2=Label(self.zoom_frame_z,text='z2:',bg=self.bg,fg=self.textcolor)
        self.right_zoom_entry_z=Entry(self.zoom_frame_z, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_button_z=Button(self.zoom_frame_z,text='Apply',  command=apply_z,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.zoom_button_z.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)


        
        self.zoom_button_z.pack(side=RIGHT,padx=(10,10))
        self.right_zoom_entry_z.pack(side=RIGHT,padx=self.padx)
        self.zoom_label_z2.pack(side=RIGHT,padx=self.padx)
        self.left_zoom_entry_z.pack(side=RIGHT,padx=self.padx)
        self.zoom_label_z1.pack(side=RIGHT,padx=self.padx)
        
        
        
    def open_analysis_tools(self, tab):

        #tab.set_exclude_artifacts(True)
        def calculate():
            self.view_notebook.select(tab.top)
            artifact_warning=False
            
            if self.analyze_var.get()=='slope':
                left, right, slopes, artifact_warning=tab.calculate_slopes(self.left_slope_entry.get(),self.right_slope_entry.get())
                update_entries(left, right)
                populate_listbox(slopes)
                update_plot_menu(['e','i','g','e,i','theta'])
                
            elif self.analyze_var.get()=='band depth':
                left, right, depths, artifact_warning=tab.calculate_band_depths(self.left_slope_entry.get(),self.right_slope_entry.get(), self.neg_depth.get(),self.use_delta.get())
                update_entries(left, right)
                populate_listbox(depths)
                update_plot_menu(['e','i','g','e,i','theta'])
                
            elif self.analyze_var.get()=='band center':
                left, right, centers,artifact_warning=tab.calculate_band_centers(self.left_slope_entry.get(),self.right_slope_entry.get(), self.use_max_for_centers.get(),self.use_delta.get())
                update_entries(left, right)
                populate_listbox(centers)
                update_plot_menu(['e','i','g','e,i','theta'])
                print(self.use_max_for_centers.get())
                
            elif self.analyze_var.get()=='reflectance':
                left, right, reflectance,artifact_warning=tab.calculate_avg_reflectance(self.left_slope_entry.get(),self.right_slope_entry.get())
                update_entries(left, right)
                populate_listbox(reflectance)
                update_plot_menu(['e','i','g','e,i','theta'])
                
            elif self.analyze_var.get()=='reciprocity':
                left, right, reciprocity, artifact_warning=tab.calculate_reciprocity(self.left_slope_entry.get(),self.right_slope_entry.get())
                update_entries(left, right)
                populate_listbox(reciprocity)
                update_plot_menu(['e','i','g','e,i'])
                
            elif self.analyze_var.get()=='difference':
                left, right, error, artifact_warning=tab.calculate_error(self.left_slope_entry.get(),self.right_slope_entry.get(), self.abs_val.get())
                #Tab validates left and right values. If they are no good, put in min and max wavelengths available.
                update_entries(left, right)
                populate_listbox(error)
                update_plot_menu([u'\u03bb', 'e,i'])
                        
            if artifact_warning:
                dialog=ErrorDialog(self, 'Warning','Warning: Excluding data potentially\ninfluenced by artifacts from 1000-1400 nm.')
                
            self.analysis_dialog.min_height=1000
            self.analysis_dialog.update()
                
        def update_plot_menu(plot_options):
            self.plot_slope_var.set(plot_options[0])
            self.plot_slope_menu['menu'].delete(0, 'end')
        
            # Insert list of new options (tk._setit hooks them up to var)
            max_len=len(plot_options[0])
            for option in plot_options:
                max_len=np.max([max_len,len(option)])
                self.plot_slope_menu['menu'].add_command(label=option, command=tk._setit(self.plot_slope_var, option))
            self.plot_slope_menu.configure(width=max_len)

        def update_entries(left, right):
                self.left_slope_entry.delete(0,'end')
                self.left_slope_entry.insert(0,str(left))
                self.right_slope_entry.delete(0,'end')
                self.right_slope_entry.insert(0,str(right))
                
        def populate_listbox(results):
            if len(results)>0:
                self.slope_results_frame.pack(fill=BOTH, expand=True,pady=(10,10))
                try:
                    self.slopes_listbox.delete(0,'end')
                except:
                    self.slopes_listbox=ScrollableListbox(self.slope_results_frame,self.bg,self.entry_background, self.listboxhighlightcolor,selectmode=EXTENDED)
                    self.slopes_listbox.configure(height=8)
                for result in results:
                    self.slopes_listbox.insert('end',result)
                self.slopes_listbox.pack(fill=BOTH, expand=True)
                self.plot_slope_button.configure(state=NORMAL)
                
        def plot():
            
            if self.analyze_var.get()=='slope':
                tab.plot_slopes(self.plot_slope_var.get())
            elif self.analyze_var.get()=='band depth':
                tab.plot_band_depths(self.plot_slope_var.get())
            elif self.analyze_var.get()=='band center':
               tab.plot_band_centers(self.plot_slope_var.get())
            elif self.analyze_var.get()=='reflectance':
                tab.plot_avg_reflectance(self.plot_slope_var.get())
            elif self.analyze_var.get()=='reciprocity':
                tab.plot_reciprocity(self.plot_slope_var.get())
            elif self.analyze_var.get()=='difference':
                new=tab.plot_error(self.plot_slope_var.get())

            if self.plot_slope_var.get()=='\u03bb':
                x1=float(self.left_slope_entry.get())
                x2=float(self.right_slope_entry.get())
                new.adjust_x(x1,x2)


        def normalize():
            self.view_notebook.select(tab.top)
            
            try:
                self.slopes_listbox.delete(0,'end')
                self.plot_slope_button.configure(state='disabled')
            except:
                pass
            tab.normalize(self.normalize_entry.get())
            
        def offset():
            tab.offset(self.offset_sample_var.get(), self.offset_entry.get())

        def apply_x():
            self.view_notebook.select(tab.top)

            try:
                x1=float(self.left_zoom_entry.get())
                x2=float(self.right_zoom_entry.get())
                tab.adjust_x(x1,x2)
            except:
                ErrorDialog(self, title='Invalid Zoom Range',label='Error! Invalid x limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
        def apply_y():
            self.view_notebook.select(tab.top)
            try:
                y1=float(self.left_zoom_entry2.get())
                y2=float(self.right_zoom_entry2.get())
                tab.adjust_y(y1,y2)
            except:
                ErrorDialog(self, title='Invalid Zoom Range',label='Error! Invalid y limits: '+self.left_zoom_entry2.get()+', '+self.right_zoom_entry2.get())
            
        def uncheck_exclude_artifacts():
            self.exclude_artifacts.set(0)
            self.exclude_artifacts_check.deselect()
            
        def disable_plot(analyze_var='None'):
            try:
                self.slopes_listbox.delete(0,'end')
            except:
                pass
            self.plot_slope_button.configure(state='disabled')
            
            if analyze_var=='difference':
                self.neg_depth_check.pack_forget()
                self.use_max_for_centers_check.pack_forget()
                self.use_delta_check.pack_forget()
                self.abs_val_check.pack()
                self.extra_analysis_check_frame.pack()
        
            elif analyze_var=='band center':
                self.neg_depth_check.pack_forget()
                self.abs_val_check.pack_forget()
                self.use_delta_check.pack_forget()
                self.use_max_for_centers_check.pack()
                self.use_delta_check.pack()
                self.extra_analysis_check_frame.pack()
        
            elif analyze_var=='band depth':
                self.abs_val_check.pack_forget()
                self.use_max_for_centers_check.pack_forget()
                self.use_delta_check.pack_forget()
                self.neg_depth_check.pack()
                self.use_delta_check.pack()
                self.extra_analysis_check_frame.pack()
            
            else:
                self.abs_val_check.pack_forget()
                self.neg_depth_check.pack_forget()
                self.use_max_for_centers_check.pack_forget()
                self.use_delta_check.pack_forget()
                
                self.extra_analysis_check_frame.grid_propagate(0)
                self.extra_analysis_check_frame.configure(height=1) #for some reason 0 doesn't work.
                self.extra_analysis_check_frame.pack()
                self.outer_slope_frame.pack()
            
        def calculate_photometric_variability():

            photo_var=tab.calculate_photometric_variability(self.right_photo_var_entry.get(),self.left_photo_var_entry.get())
            try:
                self.photo_var_listbox.delete(0,'end')
            except:
                self.photo_var_listbox=ScrollableListbox(self.photo_var_results_frame,self.bg,self.entry_background, self.listboxhighlightcolor,selectmode=EXTENDED)
            for var in photo_var:
                self.photo_var_listbox.insert('end',var)
            self.photo_var_listbox.pack(fill=BOTH, expand=True)

        def select_tab():
            self.view_notebook.select(tab.top)
        
        
        tab.freeze() #You have to finish dealing with this before, say, opening another analysis box.
        buttons={
            'reset':{
                select_tab:[],
                tab.reset:[],
                uncheck_exclude_artifacts:[],
                disable_plot:[]
            },
            'close':{}
        }
        
        #If the user already has analysis tools or a plot editing dialog open, close the extra to avoid confusion.
        try:
            self.analysis_dialog.top.destroy()
        except:
            pass
        try:
            self.edit_plot_dialog.top.destroy()
        except:
            pass
        try:
            self.plot_options_dialog.top.destroy()
        except:
            pass
        self.analysis_dialog=VerticalScrolledDialog(self,'Analyze Data','',buttons=buttons,button_width=13)
        
        
        
        
        self.outer_normalize_frame=Frame(self.analysis_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
        self.outer_normalize_frame.pack(expand=True,fill=BOTH)
        self.slope_title_label=Label(self.outer_normalize_frame,text='Normalize:',bg=self.bg,fg=self.textcolor)
        self.slope_title_label.pack()
        self.normalize_frame=Frame(self.outer_normalize_frame,bg=self.bg,padx=self.padx,pady=15)
        self.normalize_frame.pack()

        self.normalize_label=Label(self.normalize_frame,text='Wavelength (nm):',bg=self.bg,fg=self.textcolor)
        self.normalize_entry=Entry(self.normalize_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.normalize_button=Button(self.normalize_frame,text='Apply',  command=normalize,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.normalize_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.normalize_button.pack(side=RIGHT,padx=(10,10))
        self.normalize_entry.pack(side=RIGHT,padx=self.padx)
        self.normalize_label.pack(side=RIGHT,padx=self.padx)
        
        self.outer_offset_frame=Frame(self.analysis_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
        self.outer_offset_frame.pack(expand=True,fill=BOTH)
        self.slope_title_label=Label(self.outer_offset_frame,text='Add offset to sample:',bg=self.bg,fg=self.textcolor)
        self.slope_title_label.pack(pady=(0,15))
        self.offset_sample_frame=Frame(self.outer_offset_frame,bg=self.bg,padx=self.padx,pady=self.pady)
        self.offset_sample_frame.pack()
        self.offset_sample_label=Label(self.offset_sample_frame,text='Sample: ',bg=self.bg,fg=self.textcolor)
        self.offset_sample_label.pack(side=LEFT)
        self.offset_sample_var=StringVar()
        sample_names=[]
        repeats=False
        max_len=0
        for sample in tab.samples:
            if sample.name in sample_names:
                repeats=True
            else:
                sample_names.append(sample.name)
                max_len=np.max([max_len, len(sample.name)])
        if repeats:
            sample_names=[]
            for sample in tab.samples:
                sample_names.append(sample.title+': '+sample.name)
                max_len=np.max([max_len, len(sample_names[-1])])
        self.offset_sample_var.set(sample_names[0])
        self.offset_menu=OptionMenu(self.offset_sample_frame, self.offset_sample_var,*sample_names)
        self.offset_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
        self.offset_menu.pack(side=LEFT)
        self.offset_frame=Frame(self.outer_offset_frame,bg=self.bg,padx=self.padx,pady=15)
        self.offset_frame.pack()
        self.offset_label=Label(self.offset_frame,text='Offset:',bg=self.bg,fg=self.textcolor)
        self.offset_entry=Entry(self.offset_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.offset_button=Button(self.offset_frame,text='Apply',  command=offset,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.offset_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.offset_button.pack(side=RIGHT,padx=(10,10))
        self.offset_entry.pack(side=RIGHT,padx=self.padx)
        self.offset_label.pack(side=RIGHT,padx=self.padx)
        
        self.outer_outer_zoom_frame=Frame(self.analysis_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
        self.outer_outer_zoom_frame.pack(expand=True,fill=BOTH)

        self.zoom_title_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg)
        self.zoom_title_frame.pack(pady=(5,10))
        self.zoom_title_label=Label(self.zoom_title_frame,text='Adjust plot x and y limits:',bg=self.bg,fg=self.textcolor)
        self.zoom_title_label.pack(side=LEFT,pady=(0,4)) 
        
        self.outer_zoom_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.outer_zoom_frame.pack(expand=True,fill=BOTH,pady=(0,10))
        self.zoom_frame=Frame(self.outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.zoom_frame.pack()
        
        self.zoom_label=Label(self.zoom_frame,text='x1:',bg=self.bg,fg=self.textcolor)
        self.left_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_label2=Label(self.zoom_frame,text='x2:',bg=self.bg,fg=self.textcolor)
        self.right_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_button=Button(self.zoom_frame,text='Apply',  command=apply_x,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.zoom_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.zoom_button.pack(side=RIGHT,padx=(10,10))
        self.right_zoom_entry.pack(side=RIGHT,padx=self.padx)
        self.zoom_label2.pack(side=RIGHT,padx=self.padx)
        self.left_zoom_entry.pack(side=RIGHT,padx=self.padx)
        self.zoom_label.pack(side=RIGHT,padx=self.padx)
        
        
        self.outer_zoom_frame2=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
        self.outer_zoom_frame2.pack(expand=True,fill=BOTH,pady=(0,10))
        self.zoom_frame2=Frame(self.outer_zoom_frame2,bg=self.bg,padx=self.padx)
        self.zoom_frame2.pack()
        self.zoom_label3=Label(self.zoom_frame2,text='y1:',bg=self.bg,fg=self.textcolor)
        self.left_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_label4=Label(self.zoom_frame2,text='y2:',bg=self.bg,fg=self.textcolor)
        self.right_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.zoom_button2=Button(self.zoom_frame2,text='Apply',  command=apply_y,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.zoom_button2.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)


        
        self.zoom_button2.pack(side=RIGHT,padx=(10,10))
        self.right_zoom_entry2.pack(side=RIGHT,padx=self.padx)
        self.zoom_label4.pack(side=RIGHT,padx=self.padx)
        self.left_zoom_entry2.pack(side=RIGHT,padx=self.padx)
        self.zoom_label3.pack(side=RIGHT,padx=self.padx)
        
        self.outer_outer_slope_frame=Frame(self.analysis_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
        self.outer_outer_slope_frame.pack(expand=True,fill=BOTH)
        
        self.outer_slope_frame=Frame(self.outer_outer_slope_frame,bg=self.bg,padx=self.padx)
        self.outer_slope_frame.pack(expand=True,fill=BOTH,pady=(0,10))
        self.slope_title_frame=Frame(self.outer_slope_frame,bg=self.bg)
        self.slope_title_frame.pack(pady=(5,5))
        self.slope_title_label=Label(self.slope_title_frame,text='Analyze ',bg=self.bg,fg=self.textcolor)
        self.slope_title_label.pack(side=LEFT,pady=(0,4))
        self.analyze_var=StringVar()
        self.analyze_var.set('slope')
        self.analyze_menu=OptionMenu(self.slope_title_frame,self.analyze_var,'slope','band depth','band center','reflectance','reciprocity','difference',command=disable_plot)
        self.analyze_menu.configure(width=10,highlightbackground=self.highlightbackgroundcolor)
        self.analyze_menu.pack(side=LEFT)
        
        #We'll put checkboxes for additional options into this frame at the time the user selects a given option (e.g. select 'difference' from menu, add option to calculate differences based on absolute value
        self.extra_analysis_check_frame=Frame(self.outer_slope_frame,bg=self.bg,padx=self.padx)
        self.extra_analysis_check_frame.pack()
        self.abs_val=IntVar()
        #Note that we are not packing this checkbutton yet.
        self.abs_val_check=Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,fg=self.textcolor,text=' Use absolute values for average differences', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.abs_val)
        
        self.use_max_for_centers=IntVar()
        self.use_max_for_centers_check=Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,fg=self.textcolor,text=' If band max is more prominent than\nband min, use to find center.', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.use_max_for_centers)
        self.use_max_for_centers_check.select()
        
        self.use_delta=IntVar()
        self.use_delta_check=Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,fg=self.textcolor,text=u' Center at max \u0394'+'R from continuum  \nrather than spectral min/max. ', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.use_delta)
        self.use_delta_check.select()
        
        self.neg_depth=IntVar()
        self.neg_depth_check=Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,fg=self.textcolor,text=' If band max is more prominent than \nband min, report negative depth.', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.neg_depth)
        self.neg_depth_check.select()
        
        self.slope_frame=Frame(self.outer_slope_frame,bg=self.bg,padx=self.padx, highlightthickness=0)
        self.slope_frame.pack(pady=(15,0))
        
        self.slope_label=Label(self.slope_frame,text='x1:',bg=self.bg,fg=self.textcolor)
        self.left_slope_entry=Entry(self.slope_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.slope_label_2=Label(self.slope_frame,text='x2:',bg=self.bg,fg=self.textcolor)
        self.right_slope_entry=Entry(self.slope_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.slope_button=Button(self.slope_frame,text='Calculate',  command=calculate,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.slope_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)

        self.slope_button.pack(side=RIGHT,padx=(10,10))
        self.right_slope_entry.pack(side=RIGHT,padx=self.padx)
        self.slope_label_2.pack(side=RIGHT,padx=self.padx)
        self.left_slope_entry.pack(side=RIGHT,padx=self.padx)
        self.slope_label.pack(side=RIGHT,padx=self.padx)
        self.slope_results_frame=Frame(self.outer_slope_frame,bg=self.bg)
        self.slope_results_frame.pack(fill=BOTH, expand=True) #We'll put a listbox with slope info in here later after calculating.
        
        self.outer_plot_slope_frame=Frame(self.outer_outer_slope_frame,bg=self.bg,padx=self.padx,pady=10)
        self.outer_plot_slope_frame.pack(expand=True,fill=BOTH)
        self.plot_slope_frame=Frame(self.outer_plot_slope_frame,bg=self.bg,padx=self.padx)
        self.plot_slope_frame.pack(side=RIGHT)
        self.plot_slope_label=Label(self.plot_slope_frame,text='Plot as a function of',bg=self.bg,fg=self.textcolor)
        self.plot_slope_var=StringVar()
        self.plot_slope_var.set('e')
        self.plot_slope_menu=OptionMenu(self.plot_slope_frame,self.plot_slope_var,'e','i','g','e,i','theta')
        self.plot_slope_menu.configure(width=2,highlightbackground=self.highlightbackgroundcolor)
        self.plot_slope_button=Button(self.plot_slope_frame,text='Plot',  command=plot,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
        self.plot_slope_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor,state=DISABLED)
        self.plot_slope_button.pack(side=RIGHT,padx=(10,10))
        self.plot_slope_menu.pack(side=RIGHT,padx=self.padx)
        self.plot_slope_label.pack(side=RIGHT,padx=self.padx)
        

        self.exclude_artifacts_frame=Frame(self.analysis_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
        self.exclude_artifacts_frame.pack(fill=BOTH,expand=True)
        self.exclude_artifacts=IntVar()
        self.exclude_artifacts_check=Checkbutton(self.exclude_artifacts_frame, selectcolor=self.check_bg,fg=self.textcolor,text=' Exclude data susceptible to artifacts\n (high g, 1000-1400 nm)  ', bg=self.bg, pady=self.pady,highlightthickness=0, variable=self.exclude_artifacts, command=lambda x='foo',: tab.set_exclude_artifacts(self.exclude_artifacts.get()))
        self.exclude_artifacts_check.pack()
        if tab.exclude_artifacts:
            self.exclude_artifacts_check.select()




        self.analysis_dialog.interior.configure(highlightthickness=1,highlightcolor='white')
        

        
    #This gets called when the user clicks 'Edit plot' from the right-click menu on a plot.
    #Pops up a scrollable listbox with sample options.
    def ask_plot_samples(self, tab, existing_sample_indices, sample_options, existing_geoms, current_title):
        def config_tol_entry():
            return #Decided againsta having the tolerance entry disabled if you don't have exclude specular angles checked.
            if self.exclude_specular.get():
                self.spec_tolerance_entry.configure(state=NORMAL)
            else:
                self.spec_tolerance_entry.configure(state=DISABLED)

            
        def select_tab():
            self.view_notebook.select(tab.top)
        buttons={
            'ok':{
                select_tab:[],
                #The lambda sends a list of the currently selected samples back to the tab along with the new title and selected incidence/emission angles
                lambda: tab.set_samples(list(map(lambda y:sample_options[y],self.plot_samples_listbox.curselection())),self.new_plot_title_entry.get(), self.i_entry.get(),self.e_entry.get(), self.exclude_specular.get(), self.spec_tolerance_entry.get()):[]
                }
            }
        try:
            self.analysis_dialog.top.destroy()
        except:
            pass
        try:
            self.edit_plot_dialog.top.destroy()
        except:
            pass        
        try:
            self.plot_options_dialog.top.destroy()
        except:
            pass
            
        self.edit_plot_dialog=Dialog(self,'Edit Plot','\nPlot title:',buttons=buttons)
        self.new_plot_title_entry=Entry(self.edit_plot_dialog.top, width=20, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.new_plot_title_entry.insert(0,current_title)
        self.new_plot_title_entry.pack()
        
        sample_label=Label(self.edit_plot_dialog.top,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='\nSamples:')
        sample_label.pack(pady=(0,10))
        self.plot_samples_listbox=ScrollableListbox(self.edit_plot_dialog.top,self.bg,self.entry_background, self.listboxhighlightcolor,selectmode=EXTENDED)
        
        self.geom_label=Label(self.edit_plot_dialog.top,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='\nEnter incidence and emission angles to plot,\nor leave blank to plot all:\n')
        self.geom_label.pack()
        self.geom_frame=Frame(self.edit_plot_dialog.top)
        self.geom_frame.pack(padx=(20,20),pady=(0,10))
        self.i_label=Label(self.geom_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='i: ')
        self.i_label.pack(side=LEFT)
        self.i_entry=Entry(self.geom_frame, width=12, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        for i, incidence in enumerate(existing_geoms['i']):
            if i==0:
                self.i_entry.insert(0,incidence)
            else:
                self.i_entry.insert('end',','+incidence)
                
        self.i_entry.pack(side=LEFT)
        
        self.e_label=Label(self.geom_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text='    e: ')
        self.e_label.pack(side=LEFT)
        self.e_entry=Entry(self.geom_frame, width=12, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        for i, emission in enumerate(existing_geoms['e']):
            if i==0:
                self.e_entry.insert(0,emission)
            else:
                self.e_entry.insert('end',','+emission)
        self.e_entry.pack(side=LEFT)
        
        self.exclude_specular_frame=Frame(self.edit_plot_dialog.top,bg=self.bg,padx=self.padx, pady=self.pady)
        self.exclude_specular_frame.pack()
        self.exclude_specular=IntVar()
        self.exclude_specular_check=Checkbutton(self.exclude_specular_frame, selectcolor=self.check_bg,fg=self.textcolor,text='  Exclude specular angles (+/-', bg=self.bg, pady=self.pady,highlightthickness=0, command=config_tol_entry, variable=self.exclude_specular)
        self.exclude_specular_check.pack(side=LEFT)
        # self.spec_tolerance_frame=Frame(self.exclude_specular_frame,bg=self.bg,padx=self.padx, pady=self.pady)
        # self.spec_tolerance_frame.pack()

        self.spec_tolerance_entry=Entry(self.exclude_specular_frame, width=4, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        
        self.spec_tolerance_entry.pack(side=LEFT)
        self.spec_tolerance_label=Label(self.exclude_specular_frame,padx=self.padx,pady=self.pady,bg=self.bg,fg=self.textcolor,text=u'\u00B0)')
        self.spec_tolerance_label.pack(side=LEFT)
        
        if tab.exclude_specular:
            self.exclude_specular_check.select()
            self.spec_tolerance_entry.insert(0,tab.specularity_tolerance)
        


        sample_files=[]
        for option in sample_options:
            self.plot_samples_listbox.insert(END,option)
        

        for i in existing_sample_indices:
            self.plot_samples_listbox.select_set(i)
        self.plot_samples_listbox.config(height=8)
        
    def reset_plot_data(self):
        self.plotter=Plotter(self,self.get_dpi(),[ self.global_config_loc+'color_config.mplstyle',self.global_config_loc+'size_config.mplstyle'])
        for i, tab in enumerate(self.view_notebook.tabs()):
            if i==0: continue
            else: self.view_notebook.forget(tab)
    def plot(self):
        filename=self.plot_input_dir_entry.get()
        if self.opsys=='Windows' or self.plot_remote.get(): filename=filename.replace('\\','/')
        
        if self.plot_remote.get():
            self.queue.insert(0,{self.plot:[]})
            self.queue.insert(1,{self.actually_plot:[self.spec_share_loc+'plot_temp.csv']})
            self.spec_commander.transfer_data(filename, 'spec_share_loc','plot_temp.csv')
            data_handler=DataHandler(self, source=filename, temp_destination=self.spec_share_loc+'plot_temp.csv', final_destination=self.spec_share_loc+'plot_temp.csv')
        else:
            if os.path.exists(filename):
                self.actually_plot(filename)
            else:

                dialog=ErrorDialog(self,title='Error: File not found',label='Error: File not found.\n\n'+filename+'\n\ndoes not exist.')
                return False
            


    def actually_plot(self, filename):
        if len(self.queue)>0:
            print('There is a queue here if and only if we are transferring data from a remote location.')
            for item in self.queue:
                print(item)
            self.complete_queue_item()
        title=self.plot_title_entry.get()
        caption=''#self.plot_caption_entry.get()

            
                    
        try:
            self.plot_input_file=self.plot_input_dir_entry.get()
            self.plot_title=self.plot_title_entry.get()
            if self.plot_remote.get():
                self.plot_local_remote='remote'
            elif self.plot_local.get():
                self.plot_local_remote='local'
            
            with open(self.local_config_loc+'plot_config.txt','w') as plot_config:
                plot_config.write(self.plot_local_remote+'\n')
                plot_config.write(self.plot_input_file+'\n')
                plot_config.write(self.plot_title+'\n')

            self.plot_top.destroy()
        
            if self.plotter.controller.plot_local_remote=='remote':
                self.plotter.plot_spectra(title,filename,caption,exclude_wr=False, draw=False)
                self.plotter.tabs[-1].ask_which_samples()
            else:
                self.plotter.plot_spectra(title,filename,caption,exclude_wr=False, draw=True)
                self.plotter.tabs[-1].ask_which_samples()

            self.goniometer_view.flip()
    
            last=len(self.view_notebook.tabs())-1
    
            self.view_notebook.select(last)
            if self.plotter.save_dir==None: #If the user hasn't specified a folder where they want to save plots yet, set the default folder to be the same one they got the data from. Otherwise, leave it as is.
                if self.opsys=='Windows':
                    self.plotter.save_dir='\\'.join(filename.split('\\')[0:-1])
                else:
                    self.plotter.save_dir='/'.join(filename.split('/')[0:-1])
    

            
            
        except Exception as e:
            print(e)
            
            dialog=Dialog(self, 'Plotting Error', 'Error: Plotting failed.\n\nDoes file exist? Is data formatted correctly?\nIf plotting a remote file, is the server accessible?',{'ok':{}})
            raise e
    
    
    def auto_cycle_check(self):
        if self.auto.get():
            light_end_label.config(fg='black')
            detector_end_label.config(fg='black')
            light_increment_label.config(fg='black')
            detector_increment_label.config(fg='black')
            light_end_entry.config(bd=3)
            detector_end_entry.config(bd=3)
            light_increment_entry.config(bd=3)
            detector_increment_entry.config(bd=3)
        else:
            light_end_label.config(fg='lightgray')
            detector_end_label.config(fg='lightgray')
            light_increment_label.config(fg='lightgray')
            detector_increment_label.config(fg='lightgray')
            light_end_entry.config(bd=1)
            detector_end_entry.config(bd=1)
            light_increment_entry.config(bd=1)
            detector_increment_entry.config(bd=1)
        

        if keypress_event.keycode==111:
            if len(user_cmds)>user_cmd_index+1 and len(user_cmds)>0:
                user_cmd_index=user_cmd_index+1
                last=user_cmds[user_cmd_index]
                self.console_entry.delete(0,'end')
                self.console_entry.insert(0,last)

        elif keypress_event.keycode==116:
            if user_cmd_index>0:
                user_cmd_index=self.user_cmd_index-1
                next=selfuser_cmds[user_cmd_index]
                self.console_entry.delete(0,'end')
                self.console_entry.insert(0,next)
                
    def choose_spec_save_dir(self):

        self.remote_file_explorer=RemoteFileExplorer(self,label='Select a directory to save raw spectral data.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\RiceData\MarsGroup\Kathleen\spectral_data', target=self.spec_save_dir_entry)
        
    def choose_process_input_dir(self):
        r=RemoteFileExplorer(self,label='Select the directory containing the data you want to process.\nThis must be on a drive mounted on the spectrometer control computer.\n E.g. R:\RiceData\MarsGroup\Kathleen\spectral_data',target=self.input_dir_entry)
        
    def choose_process_output_dir(self):
        r=RemoteFileExplorer(self,label='Select the directory where you want to save your processed data.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\RiceData\MarsGroup\Kathleen\spectral_data',target=self.output_dir_entry)
    
    def add_sample(self):
        try:
            self.add_sample_button.pack_forget()
        except:
            self.add_sample_button=Button(self.samples_frame, text='Add new', command=self.add_sample,width=10, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
            self.tk_buttons.append(self.add_sample_button)
            self.add_sample_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor,state=DISABLED)
            
        self.sample_frames.append(Frame(self.samples_frame, bg=self.bg))
        self.sample_frames[-1].pack(pady=(5,0))
        
        self.control_frame.min_height+=50
        self.control_frame.update()
        
        self.sample_pos_vars.append(StringVar(self.master))
        self.sample_pos_vars[-1].trace('w',self.set_taken_sample_positions)
        menu_positions=[]
        pos_set=False
        for pos in self.available_sample_positions:
            if pos in self.taken_sample_positions:
                pass
            elif pos_set==False:
                self.sample_pos_vars[-1].set(pos)
                pos_set=True
            else:
                menu_positions.append(pos)
        if len(menu_positions)==0: #If all samples are full (i.e. this is the last sample), we need to have a value in the menu options in order for it to appear on the screen. This is really a duplicate option, but Tkinter won't create an OptionMenu without options.
            menu_positions.append(self.sample_pos_vars[-1].get())


        self.pos_menus.append(OptionMenu(self.sample_frames[-1],self.sample_pos_vars[-1],*menu_positions))
        self.pos_menus[-1].configure(width=8,highlightbackground=self.highlightbackgroundcolor)
        self.pos_menus[-1].pack(side=LEFT)
        self.option_menus.append(self.pos_menus[-1])
        
        self.sample_labels.append(Label(self.sample_frames[-1],bg=self.bg,fg=self.textcolor,text='Label:',padx=self.padx,pady=self.pady))
        self.sample_labels[-1].pack(side=LEFT, padx=(5,0))
        
        self.sample_label_entries.append(Entry(self.sample_frames[-1], width=20, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground))

        self.entries.append(self.sample_label_entries[-1])
        self.sample_label_entries[-1].pack(side=LEFT,padx=(0,10))
        

          
        self.sample_removal_buttons.append(Button(self.sample_frames[-1], text='Remove', command=lambda x=len(self.sample_removal_buttons):self.remove_sample(x),width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd))
        self.sample_removal_buttons[-1].config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.tk_buttons.append(self.sample_removal_buttons[-1])
        if len(self.sample_label_entries)>1:
            for button in self.sample_removal_buttons:
                button.pack(side=LEFT,padx=(5,5))
        
        if len(self.sample_label_entries)>len(self.available_sample_positions)-1:
            self.add_sample_button.configure(state=DISABLED)
        self.add_sample_button.pack(pady=(10,10))
        
        
    def remove_sample(self,index):
        self.sample_labels.pop(index)
        self.sample_label_entries.pop(index)
        self.sample_pos_vars.pop(index)
        self.sample_removal_buttons.pop(index)
        self.sample_frames.pop(index).destroy()
        self.pos_menus.pop(index)
        
        for i, button in enumerate(self.sample_removal_buttons):
            button.configure(command=lambda x=i:self.remove_sample(x))
        if self.manual_automatic.get()==1:
            self.add_sample_button.configure(state=NORMAL)
        if len(self.sample_label_entries)==1:
            self.sample_removal_buttons[0].pack_forget()
        self.set_taken_sample_positions()
        
        self.control_frame.min_height-=50 #Reduce the required size for the control frame to display all elements. 
        self.control_frame.update() #Configure scrollbar.
            
    def set_taken_sample_positions(self,arg1=None,arg2=None,arg3=None):
        self.taken_sample_positions=[]
        for var in self.sample_pos_vars:
            self.taken_sample_positions.append(var.get())
            
        #Now remake all option menus with taken sample positions not listed in options unless that was the option that was already selected for them.
        menu_positions=[]
        for pos in self.available_sample_positions:
            if pos in self.taken_sample_positions:
                pass
            else:
                menu_positions.append(pos)
        

        
        for i, menu in enumerate(self.pos_menus):
            local_menu_positions=list(menu_positions)
            if len(menu_positions)==0: #If all samples are full, we need to have a value in the menu options in order for it to appear on the screen. This is really a duplicate option, but Tkinter won't create an OptionMenu without options, so having it in there prevents errors.
                local_menu_positions.append(self.sample_pos_vars[i].get())
            self.pos_menus[i]['menu'].delete(0, 'end')
            for choice in local_menu_positions:
                self.pos_menus[i]['menu'].add_command(label=choice, command=tk._setit(self.sample_pos_vars[i], choice))
        
        

    def remove_geometry(self,index):
        self.incidence_labels.pop(index)
        self.incidence_entries.pop(index)
        self.azimuth_labels.pop(index)
        self.azimuth_entries.pop(index)
        self.emission_entries.pop(index)
        self.emission_labels.pop(index)
        self.geometry_removal_buttons.pop(index)
        self.geometry_frames.pop(index).destroy()


        for i, button in enumerate(self.geometry_removal_buttons):
            button.configure(command=lambda x=i:self.remove_geometry(x))
        if self.manual_automatic.get()==1:
            self.add_geometry_button.configure(state=NORMAL)
        if len(self.incidence_entries)==1:
            self.geometry_removal_buttons[0].pack_forget()
            
    def add_geometry(self):
        try:
            self.add_geometry_button.pack_forget()
        except:
            self.add_geometry_button=Button(self.individual_angles_frame, text='Add new', command=self.add_geometry,width=10, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
            self.tk_buttons.append(self.add_geometry_button)
            self.add_geometry_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor,state=DISABLED)
            
        self.geometry_frames.append(Frame(self.individual_angles_frame, bg=self.bg))
        self.geometry_frames[-1].pack(pady=(5,0))
        
        self.incidence_labels.append(Label(self.geometry_frames[-1],bg=self.bg,fg=self.textcolor,text='i:',padx=self.padx,pady=self.pady))
        self.incidence_labels[-1].pack(side=LEFT, padx=(5,0))
        self.incidence_entries.append(Entry(self.geometry_frames[-1], width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground))
        self.entries.append(self.incidence_entries[-1])
        self.incidence_entries[-1].pack(side=LEFT,padx=(0,10))
        
        self.emission_labels.append(Label(self.geometry_frames[-1], padx=self.padx,pady=self.pady,bg=self.bg, fg=self.textcolor,text='e:'))
        self.emission_labels[-1].pack(side=LEFT)
        self.emission_entries.append(Entry(self.geometry_frames[-1], width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground))
        self.entries.append(self.emission_entries[-1])
        self.emission_entries[-1].pack(side=LEFT, padx=(0,10))
        
        self.azimuth_labels.append(Label(self.geometry_frames[-1],bg=self.bg,fg=self.textcolor,text='az:',padx=self.padx,pady=self.pady))
        self.azimuth_labels[-1].pack(side=LEFT, padx=(5,0))
        self.azimuth_entries.append(Entry(self.geometry_frames[-1], width=10, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground))
        self.entries.append(self.azimuth_entries[-1])
        self.azimuth_entries[-1].pack(side=LEFT,padx=(0,10))
        
        self.geometry_removal_buttons.append(Button(self.geometry_frames[-1], text='Remove', command=lambda x=len(self.geometry_removal_buttons):self.remove_geometry(x),width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd))
        self.geometry_removal_buttons[-1].config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        if len(self.incidence_entries)>1:
            for button in self.geometry_removal_buttons:
                button.pack(side=LEFT)
        
        if len(self.incidence_entries)>10:
            self.add_geometry_button.configure(state=DISABLED)
        self.add_geometry_button.pack(pady=(15,10))
        
    def configure_pi(self,i=None, e=None, az=None, pos=None):
        if i==None or e==None or az==None or pos==None:
            if self.sample_tray_index>-1:
                self.pi_commander.configure(str(self.i),str(self.e),str(self.az), self.sample_tray_index)
            else:
                self.pi_commander.configure(str(self.i),str(self.e),str(self.az), 'wr')
        else:

            self.pi_commander.configure(str(i),str(e),str(az), pos)
            
        timeout_s=PI_BUFFER
        while timeout_s>0:
            if 'piconfigsuccess' in self.pi_listener.queue:
                self.pi_listener.queue.remove('piconfigsuccess')
                print('PI CONFIG')
                tray_position_string=''
                if self.sample_tray_index!=-1:
                    tray_position_string=self.available_sample_positions[self.sample_tray_index]
                else:
                    tray_position_string='WR'
                print('set')
                self.goniometer_view.set_current_sample(tray_position_string)

                if i!=None:self.i=i #redundant, this already happens elsewhere. I think this would probably be the better place to put it though.
                if e!=None:self.e=e #redundant, this already happens elsewhere
                if az!=None:self.az=az
                
                self.log('Raspberry pi configured.\n\ti = '+str(self.i)+'\n\te = '+str(self.e)+'\n\taz = '+str(self.az)+'\n\ttray position: '+tray_position_string)
                break

            time.sleep(INTERVAL)
            timeout_s-=INTERVAL
        if timeout_s<=0:
            self.queue=[]
            self.script_running=False
            if self.wait_dialog==None:
                dialog=ErrorDialog(self,label='Error: Failed to configure Raspberry Pi.\nCheck connections and/or restart scripts.')

            else: #Everything in this else clause is nonsense.
                self.wait_dialog.interrupt('Error: Failed to configure Raspberry Pi.\nCheck connections and/or restart scripts.')
                
            self.i=None
            self.e=None
            self.az=None
            self.set_manual_automatic(force=0)
            
            return
        else:
            self.goniometer_view.set_azimuth((int(self.az)), config=True)
            self.goniometer_view.set_incidence(int(self.i),config=True)
            self.goniometer_view.set_emission(int(self.e),config=True)
            self.complete_queue_item()
            
            if len(self.queue)>0:
                self.next_in_queue()
            else:
                self.unfreeze()
        
    def set_manual_automatic(self,override=False,force=-1,known_goniometer_state=False):
        menu=self.goniometermenu
        if force==0:
            self.manual_automatic.set(0)
        elif force==1:
            self.manual_automatic.set(1)
        
        if self.manual_automatic.get()==0:# or force==0:
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
            self.range_radio.configure(state = DISABLED)
            self.individual_range.set(0)
            
            while len(self.incidence_entries)>1:
                self.remove_geometry(len(self.incidence_entries)-1)
            self.add_geometry_button.configure(state=DISABLED)
            self.add_sample_button.configure(state=DISABLED)
            for pos_menu in self.pos_menus:
                pos_menu.configure(state=DISABLED)
           
            self.opt_button.pack(padx=self.padx,pady=self.pady, side=LEFT)
            self.wr_button.pack(padx=self.padx,pady=self.pady, side=LEFT) 
            self.spec_button.pack(padx=self.padx,pady=self.pady, side=LEFT)


            self.acquire_button.pack_forget()
            menu.entryconfigure(0,label='X Manual')
            menu.entryconfigure(1,label='  Automatic')
            self.geommenu.entryconfigure(0, label='X Individual')
            self.geommenu.entryconfigure(1,state=DISABLED, label='  Range (Automatic only)')
        else:

            self.add_geometry_button.configure(state=NORMAL)
            self.acquire_button.pack(padx=self.padx,pady=self.pady)
            self.spec_button.pack_forget()
            self.opt_button.pack_forget()
            self.wr_button.pack_forget()
            self.range_radio.configure(state = NORMAL)
            self.add_sample_button.configure(state=NORMAL)
            for pos_menu in self.pos_menus:
                pos_menu.configure(state=NORMAL)
            

            self.queue.insert(0,{self.configure_pi:[]})
            #This is if you are setting manual_automatic from commandline and already entered i, e, sample tray position.
            if known_goniometer_state:
                menu.entryconfigure(0,label='  Manual')
                menu.entryconfigure(1,label='X Automatic')
                self.geommenu.entryconfigure(1,state=NORMAL, label='  Range (Automatic only)')
            else:
                self.freeze()
                buttons={
                    'ok':{
                        self.next_in_queue:[],
                        self.unfreeze:[],
                    },
                    'cancel':{
                        self.unfreeze:[],
                        self.set_manual_automatic:[override,0], 
                        self.clear_queue:[],
                        
                    }
                }
                dialog=IntInputDialog(self,title='Setup Required',label='Setup required: Unknown goniometer state.\n\nPlease enter the current viewing geometry and tray position,\nor click \'Cancel\' to use the goniometer in manual mode.',values={'Incidence':[self.i,self.min_i,self.max_i],'Emission':[self.e,self.min_e,self.max_e],'Azimuth':[self.az, self.min_az, self.max_az], 'Tray position':[self.sample_tray_index,0,self.num_samples-1]},buttons=buttons)
                
            menu.entryconfigure(0,label='  Manual')
            menu.entryconfigure(1,label='X Automatic')
            self.geommenu.entryconfigure(1,state=NORMAL, label='  Range (Automatic only)')
            # else:
            #     dialog=Dialog(self,title='Setup Required',label='Please rotate the sample tray to the white reference position.',buttons={'ok':{}})
                
    def clear_queue(self):
        self.queue=[]
        
    def set_individual_range(self, force=-1):
        #TODO: save individually specified angles to config file
        if force==0:
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
            self.geommenu.entryconfigure(0,label='X Individual')
            self.geommenu.entryconfigure(1,label='  Range (Automatic only)')
            self.individual_range.set(0)
        elif force==1:
            self.individual_angles_frame.pack_forget()
            self.range_frame.pack()
            self.geommenu.entryconfigure(0,label='  Individual')
            self.geommenu.entryconfigure(1,label='X Range (Automatic only)')  
            self.individual_range.set(1)
    
    def set_overwrite_all(self, val):
        self.overwrite_all=val
    
    def validate_input_dir(self,*args):
        pos=self.input_dir_entry.index(INSERT)
        input_dir=rm_reserved_chars(self.input_dir_entry.get())
        if len(input_dir)<len(self.input_dir_entry.get()):
            pos=pos-1
        self.input_dir_entry.delete(0,'end')
        self.input_dir_entry.insert(0,input_dir)
        self.input_dir_entry.icursor(pos)
        
    def validate_output_dir(self):
        pos=self.output_dir_entry.index(INSERT)
        output_dir=rm_reserved_chars(self.output_dir_entry.get())
        if len(output_dir)<len(self.output_dir_entry.get()):
            pos=pos-1
        self.output_dir_entry.delete(0,'end')
        self.output_dir_entry.insert(0,output_dir)
        self.output_dir_entry.icursor(pos)
        
    def validate_output_filename(self,*args):
        pos=self.output_filename_entry.index(INSERT)
        filename=rm_reserved_chars(self.spec_output_filename_entry.get())
        filename=filename.strip('/').strip('\\')
        self.output_filename_entry.delete(0,'end')
        self.output_filename_entry.insert(0,filename)
        self.output_filename_entry.icursor(pos)
        
    def validate_spec_save_dir(self,*args):
        pos=self.spec_save_dir_entry.index(INSERT)
        spec_save_dir=rm_reserved_chars(self.spec_save_dir_entry.get())
        if len(spec_save_dir)<len(self.spec_save_dir_entry.get()):
            pos=pos-1
        self.spec_save_dir_entry.delete(0,'end')
        self.spec_save_dir_entry.insert(0,spec_save_dir)
        self.spec_save_dir_entry.icursor(pos)

    def validate_basename(self,*args):
        pos=self.spec_basename_entry.index(INSERT)
        basename=rm_reserved_chars(self.spec_basename_entry.get())
        basename=basename.strip('/').strip('\\')
        self.spec_basename_entry.delete(0,'end')
        self.spec_basename_entry.insert(0,basename)
        self.spec_basename_entry.icursor(pos)
        
    def validate_startnum(self,*args):
        pos=self.spec_startnum_entry.index(INSERT)
        num=numbers_only(self.spec_startnum_entry.get())
        if len(num)>NUMLEN:
            num=num[0:NUMLEN]
        if len(num)<len(self.spec_startnum_entry.get()):
            pos=pos-1
        self.spec_startnum_entry.delete(0,'end')
        self.spec_startnum_entry.insert(0,num)
        self.spec_startnum_entry.icursor(pos)
    

    def validate_sample_name(self, name):
        #print(entry)
        # pos=entry.index(INSERT)
        # name=entry.get()
        name=name.replace('(','').replace(')','').replace('i=','i').replace('e=','e').replace(':','')
        return name
        # entry.delete(0,'end')
        # entry.insert(0,name)
        # entry.icursor(pos)   
        
    #motor_az input from -90 to 270
    #science az from 0 to 179.
    #az=180, i=50 is the same position as az=0, i=-50
    def motor_pos_to_science_pos(self, motor_i,motor_e, motor_az):
        if motor_az<-90:
            print('UNEXPECTED AZ: '+str(motor_az))
        if motor_az>270:
            print('UNEXPECTED AZ: '+str(motor_az))
        science_i=motor_i
        science_e=motor_e
        science_az=motor_az
        
        if motor_az>=180:
            science_az-=180
            science_i=-1*science_i
        if motor_az<0:
            science_az+=180
            science_i=-1*science_i
        
        return science_i, science_e, science_az
            
        
        
    #get the point on the emission arm closest to intersecting the light source
    #az is the difference between the two, as shown in the visualization
    def get_closest_approach(self, i, e, az):
        def cos(theta):
            return np.cos(theta*3.14159/180)
        def sin(theta):
            return np.sin(theta*3.14159/180)
        
        i, e, az=self.motor_pos_to_science_pos(i, e, az)
        print_me=False
        if i ==-15:
            print('CHECKING APPROACH!')
            print(i)
            print(e)
            print(az)
            print_me=True
        
        
#         need to subtract component that is in same direction
#         or add component in opposite direction
#         for az=0: full component in same or opposite
#         az=90: no component in same or opposite
#         component in same plane is cos(az) or, if az > 90, cos(180-az)

        delta_az=az
        delta_i_e=np.abs(i-e*cos(delta_az))
        if az>90:
            delta_az=180-az
            delta_i_e=np.abs(-1*i-e*cos(delta_az))
        if print_me:
            print(delta_az)
            print(delta_i_e)
        print_me=False
            
        az_dist=sin(np.min([i, e]))*delta_az
        closest_pos=(i,e,az)
        closest_dist=np.sqrt((delta_i_e)**2+az_dist**2)

        if i<=0: #Can run into detector arm
            #define a list of positions of the arm
            arm_positions=[]
            arm_bottom_e=90
            arm_bottom_az=az-90 #-90 to 90 because i is negative.
            
            if e<=0: #azimuth is azimuth
                arm_top_e=-1*e
                arm_top_az=arm_bottom_az+90*sin(-e)
            else:
                arm_top_e=e
                arm_top_az=arm_bottom_az-90*sin(e)
                 
            delta=(arm_top_e-arm_bottom_e)/10
            if delta==0:
                arm_es=np.ones(10)*arm_top_az
            else:
                arm_es=np.arange(arm_bottom_e, arm_top_e, delta)
            
            if arm_bottom_az==arm_top_az: 
                arm_azes=np.ones(len(arm_es))*arm_top_az
            else:
                delta=(arm_bottom_az-arm_top_az)/10
                arm_azes=np.arange(arm_bottom_az, arm_top_az, delta)
                if len(arm_azes)==0:
                    delta=-1*delta
                    arm_azes=np.arange(arm_bottom_az, arm_top_az, delta)
            if print_me:
                print(arm_es)
                print(arm_azes)

            for num, arm_e in enumerate(arm_es):
                pos=[i,0,0]
                pos[0]=-1*arm_e
                pos[1]=arm_azes[num]

                az_diff=sin(pos[0])*pos[1]
                dist=np.sqrt((i-pos[0]*cos(az_diff))**2+az_diff**2)
                if print_me:
                    print(pos)
                    print(dist)

                if dist<closest_dist:
                    closest_dist=dist
                    closest_pos=pos
                    
        return closest_pos, closest_dist
        
    def validate_distance(self,i,e, az):
        print('Validating '+str(i)+', '+str(e)+', '+str(az))
        try:
            i=int(i)
            e=int(e)
            az=int(az)
        except:
            return False
    
#         if np.sqrt((i-e)**2+az**2)<self.required_angular_separation:
#             print('False because of angular sep')
#             return False
        
        closest_pos, closest_dist=self.get_closest_approach(i,e,az)
        if closest_dist<self.required_angular_separation:
            print('COLLISION')
            return False
        else:
            print('NO COLLISION')
        
        
        
    def clear(self):
        if self.manual_automatic.get()==0:
            self.unfreeze()
            self.active_incidence_entries[0].delete(0,'end')
            self.active_emission_entries[0].delete(0,'end')
            self.active_azimuth_enries[0].delete(0,'end')
            self.sample_label_entries[self.current_sample_gui_index].delete(0,'end')
            
    def next_in_queue(self):
        dict=self.queue[0]
        for func in dict:
            args=dict[func]
            func(*args)
            
    def refresh(self):
        time.sleep(0.25)
        self.goniometer_view.flip()
        self.master.update()
            
    def resize(self,window=None): #Resize the console and goniometer view frames to be proportional sizes, and redraw the goniometer.
        if window==None:
            window=PretendEvent(self.master, self.master.winfo_width(), self.master.winfo_height())
        if window.widget==self.master:
            reserve_width=500
            try:
                width=self.console_frame.winfo_width()
                #g_height=self.goniometer_view.double_embed.winfo_height()
                
                console_height=int(window.height/3)+10
                if console_height<200: console_height=200
                goniometer_height=window.height-console_height+10
                self.goniometer_view.double_embed.configure(height=goniometer_height)
                self.console_frame.configure(height=console_height)
                self.view_notebook.configure(height=goniometer_height)
                self.plotter.set_height(goniometer_height)
                

                thread = Thread(target =self.refresh) #I don't understand why this is needed, but things don't seem to get drawn right without it. 
                thread.start()
                
                self.goniometer_view.draw_side_view(window.width-self.control_frame.winfo_width()-2,goniometer_height-10)
                self.goniometer_view.flip()
                self.master.update()
            except AttributeError:
                #Happens when the program is just starting up and there is no view yet
                pass
            except ValueError:
                pass

    def finish_move(self):
        self.goniometer_view.draw_circle()
          
    def complete_queue_item(self):
        self.queue.pop(0)

    # def delete_placeholder_spectrum(self):
        # lastnumstr=str(int(self.spec_startnum_entry.get())-1)
        # while len(lastnumstr)<NUMLEN:
        #     lastnumstr='0'+lastnumstr
        #     
        # self.spec_commander.delete_spec(self.spec_save_dir_entry.get(),self.spec_basename_entry.get(),lastnumstr)
        # 
        # t=BUFFER
        # while t>0:
        #     if 'rmsuccess' in self.spec_listener.queue:
        #         self.spec_listener.queue.remove('rmsuccess')
        #         self.log('\nSaved and deleted a garbage spectrum ('+self.spec_basename_entry.get()+lastnumstr+'.asd).')
        #         break
        #     elif 'rmfailure' in self.spec_listener.queue:
        #         self.spec_listener.queue.remove('rmfailure')
        #         self.log('\nError: Failed to remove placeholder spectrum ('+self.spec_basename_entry.get()+lastnumstr+'.asd. This data is likely garbage. ')
        #         break
        #     t=t-INTERVAL
        #     time.sleep(INTERVAL)
        # if t<=0:
        #     self.log('\nError: Operation timed out removing placeholder spectrum ('+self.spec_basename_entry.get()+lastnumstr+'.asd). This data is likely garbage.')
        # self.complete_queue_item()
        # self.next_in_queue()
        
                        
    def rm_current(self):
        self.spec_commander.delete_spec(self.spec_save_dir_entry.get(),self.spec_basename_entry.get(),self.spec_startnum_entry.get())

        t=BUFFER
        while t>0:
            if 'rmsuccess' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmsuccess')

                return True
            elif 'rmfailure' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmfailure')
                return False
            t=t-INTERVAL
            time.sleep(INTERVAL)
        return False
        
    def choose_process_output_dir(self):
        init_dir=self.output_dir_entry.get()
        if self.proc_remote.get():
            process_file_explorer=RemoteFileExplorer(self, target=self.output_dir_entry,title='Select a directory',label='Select an output directory for processed data.',directories_only=True)
        else:
            self.process_top.lift()
            if os.path.isdir(init_dir):
                dir = askdirectory(initialdir=init_dir,title='Select an output directory')
            else:
                dir=askdirectory(initialdir=os.getcwd(),title='Select an output directory')
            if dir!=():
                self.output_dir_entry.delete(0,'end')
                self.output_dir_entry.insert(0, dir)
        self.process_top.lift()
                
    def choose_plot_file(self):
        init_file=self.plot_input_dir_entry.get()
        relative_file=init_file.split('/')[-1].split('\\')[-1]
        init_dir=init_file.strip(relative_file)
        if self.plot_remote.get():
            plot_file_explorer=RemoteFileExplorer(self, target=self.plot_input_dir_entry,title='Select a file',label='Select a file to plot',directories_only=False)
        else:
            if os.path.isdir(init_dir):
                file = askopenfilename(initialdir=init_dir,title='Select a file to plot')
            else:
                file=askopenfilename(initialdir=os.getcwd(),title='Select a file to plot')
            if file!=():
                self.plot_input_dir_entry.delete(0,'end')
                self.plot_input_dir_entry.insert(0, file)
        self.plot_top.lift()
            
    def log(self, info_string, write_to_file=False):
        write_to_file=False #Used to write to a local log file, but now we only write to a log file in the raw spectral data directory.
        #self.check_logfile()
        self.master.update()
        space=self.console_log.winfo_width()
        space=str(int(space/8.5))
        if int(space)<20:
            space=str(20)
        datestring=''
        datestringlist=str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring=datestring+d
            
        while info_string[0]=='\n':
            info_string=info_string[1:]
            
        if write_to_file:
            info_string_copy=str(info_string)
            
        if '\n' in info_string:
            lines=info_string.split('\n')

            lines[0]=('{1:'+space+'}{0}').format(datestring,lines[0])
            for i in range(len(lines)):
                if i==0:
                    continue
                else:
                    lines[i]=('{1:'+space+'}{0}').format('',lines[i])
            info_string='\n'.join(lines)
        else:
            info_string=('{1:'+space+'}{0}').format(datestring,info_string)
            
        if info_string[-2:-1]!='\n':
            info_string+='\n'

        self.console_log.insert(END,info_string+'\n')
        self.console_log.see(END)
                
    def freeze(self):
        for button in self.tk_buttons:
            try:
                button.configure(state='disabled')
            except:
                pass
        for entry in self.entries:
            try:
                entry.configure(state='disabled')
            except:
                pass
        for radio in self.radiobuttons:
            try:
                radio.configure(state='disabled')
            except:
                pass
        
        for button in self.tk_check_buttons:
            try:
                button.configure(state='disabled')
            except:
                pass
    
        for menu in self.option_menus:
            try:
                menu.configure(state='disabled')
            except:
                pass
        
        
        self.menubar.entryconfig('Settings', state='disabled')
        self.filemenu.entryconfig(0,state=DISABLED)
        self.filemenu.entryconfig(1,state=DISABLED)

        

    def unfreeze(self):
        self.menubar.entryconfig('Settings', state='normal')
        self.filemenu.entryconfig(0,state=NORMAL)
        self.filemenu.entryconfig(1,state=NORMAL)
        for button in self.tk_buttons:
            try:
                button.configure(state='normal')
            except Exception as e:
                print(e)
        for entry in self.entries:
            try:
                entry.configure(state='normal')
            except Exception as e:
                print(e)
        for radio in self.radiobuttons:
            try:
                radio.configure(state='normal')
            except Exception as e:
                print(e)
        
        for button in self.tk_check_buttons:
            try:
                button.configure(state='normal')
            except:
                pass
                
        for menu in self.option_menus:
            try:
                menu.configure(state='normal')
            except:
                pass
            
        if self.manual_automatic.get()==0:
            self.range_radio.configure(state='disabled')
            self.add_geometry_button.configure(state='disabled')
            self.add_sample_button.configure(state='disabled')
            for pos_menu in self.pos_menus:
                menu.configure(state='disabled')
            
                    
    def light_close(self):
        self.pi_commander.move_light(self.active_incidence_entries[0].get())
        handler=CloseHandler(self)
        self.goniometer_view.set_incidence(int(self.active_incidence_entries[0].get()))
        
    def detector_close(self):
        self.pi_commander.move_detector(self.active_emission_entries[0].get())
        handler=CloseHandler(self)
        self.goniometer_view.set_emission(int(self.active_emission_entries[0].get()))
    def plot_right_click(self,event):
        return
        dist_to_edge=self.dist_to_edge(event)
        if dist_to_edge==None: #not on a tab
            return
        
        else:
            index = self.view_notebook.index("@%d,%d" % (event.x, event.y))
            if index!=0:

                self.view_notebook.forget(index)
                self.view_notebook.event_generate("<<NotebookTabClosed>>")
        
        

        
    
class Dialog:
    def __init__(self, controller, title, label, buttons, width=None, height=None,allow_exit=True, button_width=20, info_string=None, grab=True):
        
        self.controller=controller
        self.grab=grab
        if True:#self.grab:
            try:
                self.controller.freeze()
            except:
                pass
        try:
            self.textcolor=self.controller.textcolor
            self.bg=self.controller.bg
            self.buttonbackgroundcolor=self.controller.buttonbackgroundcolor
            self.highlightbackgroundcolor=self.controller.highlightbackgroundcolor
            self.entry_background=self.controller.entry_background
            self.buttontextcolor=self.controller.buttontextcolor
            self.console_log=self.controller.console_log
            self.listboxhighlightcolor=self.controller.listboxhighlightcolor
            self.selectbackground=self.controller.selectbackground
            self.selectforeground=self.controller.selectforeground
        except:
            self.textcolor='black'
            self.bg='white'
            self.buttonbackgroundcolor='light gray'
            self.highlightbackgroundcolor='white'
            self.entry_background='white'
            self.buttontextcolor='black'
            self.console_log=None
            self.listboxhighlightcolor='light gray'
            self.selectbackground='light gray'
            self.selectforeground='black'
            

        
        #If we are starting a new master, we'll need to start a new mainloop after settin everything up. 
        #If this creates a new toplevel for an existing master, we will leave it as False.
        start_mainloop=False
        if controller==None:
            self.top=Tk()
            start_mainloop=True
            #global tk_master
            #tk_master=self.top
            self.top.configure(background=self.bg)
        else:
            if width==None or height==None:
                self.top = tk.Toplevel(controller.master, bg=self.bg)
            else:
                self.top=tk.Toplevel(controller.master, width=width, height=height, bg=self.bg)
                
        
        self.top.attributes('-topmost', 1)
        self.top.attributes('-topmost', 0)
                


        self.label_frame=Frame(self.top, bg=self.bg)
        self.label_frame.pack(side=TOP)
        self.__label = tk.Label(self.label_frame, fg=self.textcolor,text=label, bg=self.bg)
        self.set_label_text(label, log_string=info_string)
        if label!='':
            self.__label.pack(pady=(10,10), padx=(10,10))
    
        self.button_width=button_width
        self.buttons=buttons
        self.set_buttons(buttons)

        self.top.wm_title(title)
        self.allow_exit=allow_exit
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        if start_mainloop:
            self.top.mainloop()
            
        if controller!=None and info_string!=None:
            self.log(info_string)
    
    @property
    def label(self):
        return self.__label.cget('text')
        
    @label.setter
    def label(self, val):
        self.__label.configure(text=val)
        
        
    def set_title(self, newtitle):
        self.top.wm_title(newtitle)
    def set_label_text(self, newlabel, log_string=None):
        self.__label.config(fg=self.textcolor,text=newlabel)
        if log_string != None and self.controller!=None:
            self.log(log_string)
            #self.controller.console_log.insert(END, info_string)
        
    def set_buttons(self, buttons, button_width=None):
        self.buttons=buttons
        if button_width==None:
            button_width=self.button_width
        else:
            self.button_width=button_width
        #Sloppy way to check if button_frame already exists and reset it if it does.
        try:
            self.button_frame.destroy()
        except:
            pass
        self.button_frame=Frame(self.top, bg=self.bg)
        self.button_frame.pack(side=BOTTOM)
        self.tk_buttons=[]

        for button in buttons:
            
            
            if 'ok' in button.lower():
                self.ok_button = Button(self.button_frame, fg=self.textcolor,text='OK', command=self.ok, width=self.button_width)
                self.tk_buttons.append(self.ok_button)
                self.ok_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'yes to all' in button.lower():
                self.yes_to_all_button=Button(self.button_frame,fg=self.textcolor,text='Yes to all',command=self.yes_to_all,width=self.button_width)
                self.yes_to_all_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.yes_to_all_button)
            elif 'yes' in button.lower():
                self.yes_button=Button(self.button_frame, fg=self.textcolor,text='Yes', bg='light gray', command=self.yes, width=self.button_width)
                self.tk_buttons.append(self.yes_button)
                self.yes_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
            elif 'no' in button.lower():
                self.no_button=Button(self.button_frame, fg=self.textcolor,text='No',command=self.no, width=self.button_width)
                self.no_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.no_button)
            elif 'cancel_queue' in button.lower():
                self.cancel_queue_button=Button(self.button_frame, fg=self.textcolor,text='Cancel',command=self.cancel_queue, width=self.button_width)
                self.cancel_queue_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.cancel_queue_button)
            elif 'cancel' in button.lower():
                self.cancel_button=Button(self.button_frame, fg=self.textcolor,text='Cancel',command=self.cancel, width=self.button_width)
                self.cancel_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.cancel_button)

            elif 'retry' in button.lower():
                self.retry_button=Button(self.button_frame, fg=self.textcolor,text='Retry',command=self.retry, width=self.button_width)
                self.retry_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.retry_button)
            elif 'exit' in button.lower():
                self.exit_button=Button(self.button_frame, fg=self.textcolor,text='Exit',command=self.exit, width=self.button_width)
                self.exit_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.exit_button)
            elif 'work offline' in button.lower():
                self.offline_button=Button(self.button_frame, fg=self.textcolor,text='Work offline',command=self.work_offline, width=self.button_width)
                self.offline_button.pack(side=LEFT, padx=(10,10), pady=(10,10))
                self.tk_buttons.append(self.offline_button)
            elif 'pause' in button.lower():
                self.pause_button=Button(self.button_frame,fg=self.textcolor,text='Pause',command=self.pause,width=self.button_width)
                self.pause_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.pause_button)
        
            elif 'continue' in button.lower():
                self.continue_button=Button(self.button_frame,fg=self.textcolor,text='Continue',command=self.cont,width=self.button_width)
                self.continue_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.continue_button)
            elif 'close' in button.lower():
                self.close_button=Button(self.button_frame,fg=self.textcolor,text='Close',command=self.close,width=self.button_width)
                self.close_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.close_button)
            elif 'reset' in button.lower():
                self.reset_button=Button(self.button_frame,fg=self.textcolor,text='Reset',command=self.reset,width=self.button_width)
                self.reset_button.pack(side=LEFT,padx=(10,10),pady=(10,10))
                self.tk_buttons.append(self.reset_button)

                
            for button in self.tk_buttons:
                button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
            

            # else:
            #     #For each button, only handle one function with no arguments here 
            #     #the for loop is just a way to grab the function.
            #     #It would be cool to do better than this, but it will work for now.
            #     for func in buttons[button]:
            #         print(button)
            #         print(func)
            #         tk_buttons[button]=Button(self.button_frame, fg=self.textcolor,text=button,command=func)
            #         tk_buttons[button].pack(side=LEFT, padx=(10,10),pady=(10,10))
    
    def on_closing(self):
        if self.allow_exit:
            self.controller.unfreeze()
            self.top.destroy()
    def reset(self):
        dict=self.buttons['reset']
        self.execute(dict,close=False)
        
    def close(self):
        #Might fail if controller==None (happens if server isn't connected at startup)
        try:
            self.controller.unfreeze()
        except:
            pass
        self.top.destroy()
    
    def retry(self):
        self.close()
        dict=self.buttons['retry']
        self.execute(dict,False)
        
    def exit(self):
        self.top.destroy()
        exit()
        
    def cont(self):
        dict=self.buttons['continue']
        self.execute(dict,close=False)
        
    def pause(self):
        dict=self.buttons['pause']
        self.execute(dict,close=False)

    def ok(self):
        dict=self.buttons['ok']
        self.execute(dict)
        
    def yes(self):
        dict=self.buttons['yes']
        self.execute(dict)
        
    def yes_to_all(self):
        dict=self.buttons['yes to all']
        self.execute(dict)
        
    def no(self):
        dict=self.buttons['no']
        self.execute(dict)
            
    def cancel(self):
        dict=self.buttons['cancel']
        self.execute(dict)
        
    def cancel_queue(self):
        dict=self.buttons['cancel_queue']
        self.execute(dict,close=False)
        
    def execute(self,dict,close=True):
        for func in dict:
            args=dict[func]
            func(*args)

        if close:
            self.close()
    
    def work_offline(self):
        self.close()
        dict=self.buttons['work offline']
        self.execute(dict,close=False)
        
    
class VerticalScrolledDialog(Dialog):

    def __init__(self, controller, title, label, buttons={}, button_width=None, min_height=810, width=370, height=820):
        screen_height = controller.master.winfo_screenheight()
        if height>screen_height-150:
            height=screen_height-150

        super().__init__(controller, title, label, buttons, button_width=button_width, width=width, height=height)

        self.frame=VerticalScrolledFrame(controller, self.top, width=width, min_height=min_height, height=height)
        self.frame.config(height=height)
        self.frame.canvas.config(height=height)
        self.frame.pack()
        self.interior=self.frame.interior
        
    def update(self):
        self.frame.update(controller_resize=False)
        
class WaitDialog(Dialog):
    def __init__(self, controller, title='Working...', label='Working...', buttons={}):
        super().__init__(controller, title, label,buttons,width=400, height=150, allow_exit=False)

        
        self.frame=Frame(self.top, bg=self.bg, width=200, height=30)
        self.frame.pack()
  
        style=ttk.Style()
        style.configure('Horizontal.TProgressbar', background='white')
        self.pbar = ttk.Progressbar(self.frame, mode='indeterminate', name='pb2', style='Horizontal.TProgressbar' )
        self.pbar.start([10])
        self.pbar.pack(padx=(10,10),pady=(10,10))
        
        
    def interrupt(self,label):
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({'ok':{}})#self.controller.unfreeze:[]}})
        
    def reset(self, title='Working...', label='Working...', buttons={}):
        self.set_label_text(label)
        self.set_buttons(buttons)
        self.set_title(title)
        self.pbar.start([10])

class CommandHandler():
    def __init__(self, controller, title='Working...', label='Working...', buttons={}, timeout=30):
        self.controller=controller
        self.text_only=self.controller.text_only
        self.label=label
        self.title=title
        #Either update the existing wait dialog, or make a new one.
        if label=='test':
            print('testy test!')
        try:
            self.controller.wait_dialog.reset(title=title, label=label, buttons=buttons)
        except:
            self.controller.wait_dialog=WaitDialog(controller,title,label)
        self.wait_dialog=self.controller.wait_dialog 
        self.controller.freeze()
        
        #if self.controller.manual_automatic.get()==1 and len(self.controller.queue)>1:
        if len(self.controller.queue)>1:
            buttons={
                'pause':{
                    self.pause:[]
                },
                'cancel_queue':{
                    self.cancel:[]
                }
            }
            self.wait_dialog.set_buttons(buttons)
        else:
            self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))
   
        #We'll keep track of elapsed time so we can cancel the operation if it takes too long
        # self.t0=time.perf_counter()
        # self.t=time.perf_counter()
        self.timeout_s=timeout
        
        #The user can pause or cancel if we're executing a list of commands.
        self.pause=False
        self.cancel=False

        #A Listener object is always running a loop in a separate thread. It  listens for files dropped into a command folder and changes its attributes based on what it finds.
        self.timeout_s=timeout

        #Start the wait function, which will watch the listener to see what attributes change and react accordingly. If this isn't in its own thread, the dialog box doesn't pop up until after it completes.
        self.thread = Thread(target =self.wait)
        self.thread.start()
        
    @property
    def timeout_s(self):
        return self.__timeout_s
        
    @timeout_s.setter
    def timeout_s(self, val):
        self.__timeout_s=val
        
    def wait(self):
        while True:
            print('waiting in super...')
            self.timeout_s-=1
            if self.timeout_s<0:
                self.timeout()
            time.sleep(1)
               
    def timeout(self, log_string=None, retry=True, dialog=True, dialog_string='Error: Operation timed out'):
        if self.text_only:
            #self.cmd_complete=True
            self.script_failed=True
        if log_string==None:
            self.controller.log('Error: Operation timed out')
        else:
            self.controller.log(log_string)
        if dialog:
            self.wait_dialog.interrupt(dialog_string)
            if retry:
                buttons={
                    'retry':{
                        self.controller.next_in_queue:[]
                    },
                    'cancel':{
                        self.finish:[]
                    }
                }
                self.wait_dialog.set_buttons(buttons)

    def finish(self):
        self.controller.reset()
        self.wait_dialog.close()
        
    def pause(self):
        self.pause=True
        self.wait_dialog.label='Pausing after command completes...'
    
    def cancel(self):
        self.cancel=True
        self.controller.reset()
        self.wait_dialog.label='Canceling...'
        
    def interrupt(self,label, info_string=None, retry=False):
        self.allow_exit=True
        self.wait_dialog.interrupt(label)
        if info_string!=None:
            self.log(info_string)
        if retry:
            buttons={
                'retry':{
                    self.controller.next_in_queue:[]
                },
                'cancel':{
                    self.finish:[]
                }
            }
            self.wait_dialog.set_buttons(buttons)
        self.controller.freeze()

        
    def remove_retry(self, need_new=True):
        if need_new:
            self.controller.wait_dialog=None
        removed=self.controller.rm_current()
        if removed: 
            numstr=str(self.controller.spec_num)
            if numstr=='None':
                numstr=self.controller.spec_startnum_entry.get()
            while len(numstr)<NUMLEN:
                numstr='0'+numstr
            self.controller.log('Warning: overwriting '+self.controller.spec_save_path+'\\'+self.controller.spec_basename+numstr+'.asd.')
            
            #If we are retrying taking a spectrum or white references, don't do input checks again.
            if self.controller.take_spectrum in self.controller.queue[0]:
                garbage=self.controller.queue[0][self.controller.take_spectrum][2]
                self.controller.queue[0]={self.controller.take_spectrum:[True,True,garbage]}
                
            elif self.controller.wr in self.controller.queue[0]:
                self.controller.queue[0]={self.controller.wr:[True,True]}
            self.controller.next_in_queue()
        else:
            dialog=ErrorDialog(self.controller,label='Error: Failed to remove file. Choose a different base name,\nspectrum number, or save directory and try again.')
            #self.wait_dialog.set_buttons({'ok':{}})
            
    def success(self,close=True):
        try:
            self.controller.complete_queue_item()

        except Exception as e:
            print(e)
            print('canceled by user?')

        if self.cancel:
            self.interrupt('Canceled.')
            self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))
            self.controller.reset()
        elif self.pause:
            buttons={
                'continue':{
                    self.controller.next_in_queue:[]
                },
                'cancel':{
                    self.finish:[]
                }
            }
            self.interrupt('Paused.')
            self.wait_dialog.set_buttons(buttons)
        elif len(self.controller.queue)>0:
            self.controller.next_in_queue()
        elif self.controller.script_running:
            self.controller.log('Success!')
            self.controller.script_running=False
            self.finish()
        else:
            self.controller.reset()
            self.interrupt('Success!')
            
    def set_text(self,widget, text):
        state=widget.cget('state')
        widget.configure(state='normal')
        widget.delete(0,'end')
        widget.insert(0,text)
        widget.configure(state=state)
            

class InstrumentConfigHandler(CommandHandler):
    def __init__(self, controller, title='Configuring instrument...', label='Configuring instrument...', timeout=30):
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=timeout)
        
    def wait(self):
        while self.timeout_s>0:
            if 'iconfigsuccess' in self.listener.queue:
                self.listener.queue.remove('iconfigsuccess')
                self.success()
                return
            elif 'iconfigfailure' in self.listener.queue:
                self.listener.queue.remove('iconfigfailure')
                self.interrupt('Error: Failed to configure instrument.',retry=True)
                self.controller.log('Error: Failed to configure instrument.')
                return
                
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        self.timeout()

    def success(self):
        self.controller.spec_config_count=self.controller.instrument_config_entry.get()

        self.controller.log('Instrument configured to average '+str(self.controller.spec_config_count)+' spectra.',write_to_file=True)
        

        super(InstrumentConfigHandler, self).success()
        
class OptHandler(CommandHandler):
    def __init__(self, controller, title='Optimizing...', label='Optimizing...'):

        if controller.spec_config_count!=None:
            timeout_s=int(controller.spec_config_count)/9+50+BUFFER
        else:
            timeout_s=1000
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=timeout_s)
        self.first_try=True #Occasionally, optimizing and white referencing may fail for reasons I haven't figured out. I made it do one automatic retry, which has yet to fail.
        
        


    def wait(self):
        while self.timeout_s>0:
            if 'nonumspectra' in self.listener.queue:
                print("NONUM")
                self.listener.queue.remove('nonumspectra')
                self.controller.queue.insert(0,{self.controller.configure_instrument:[]})
                self.controller.configure_instrument()
                return
                
            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
                self.controller.queue.insert(0,{self.controller.set_save_config:[]})
                self.controller.set_save_config()
                return
                
                
            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
                #If the next thing we're going to do is take a spectrum then set override to True - we will already have checked in with the user about those things when we first decided to take a spectrum.
                
                self.controller.queue.insert(0,{self.controller.set_save_config:[]})
                self.controller.set_save_config()
                return  
                
            if 'optsuccess' in self.listener.queue:
                self.listener.queue.remove('optsuccess')
                self.success()
                return
                
            elif 'optfailure' in self.listener.queue:
                self.listener.queue.remove('optfailure')
                
                if self.first_try==True and not self.cancel and not self.pause: #Actually this is always true since a new OptHandler gets created for each attempt
                    self.controller.log('Error: Failed to optimize instrument. Retrying.')
                    self.first_try=False
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt('Error: There was a problem with\noptimizing the instrument.\n\nPaused.',retry=True)
                    self.wait_dialog.top.geometry('376x165')
                    self.controller.log('Error: There was a problem with optimizing the instrument.')
                elif not self.cancel:
                    self.interrupt('Error: There was a problem with\noptimizing the instrument.',retry=True)
                    self.wait_dialog.top.geometry('376x165')
                    self.controller.log('Error: There was a problem with optimizing the instrument.')
                else: #You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt('Error: There was a problem with\noptimizing the instrument.\n\nData acquisition canceled.',retry=False)
                    self.wait_dialog.top.geometry('376x165')
                    self.controller.log('Error: There was a problem with optimizing the instrument.')
                return
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        self.timeout()
                
    def success(self):
        self.controller.opt_time=int(time.time())
        self.controller.log('Instrument optimized.',write_to_file=True)# \n\ti='+self.controller.active_incidence_entries[0].get()+'\n\te='+self.controller.active_emission_entries[0].get())
        super(OptHandler, self).success()

        
class WhiteReferenceHandler(CommandHandler):
    def __init__(self, controller, title='White referencing...',
    label='White referencing...'):
        
        timeout_s=int(controller.spec_config_count)/9+30+BUFFER
        self.listener=controller.spec_listener
        self.first_try=True
        super().__init__(controller, title, label,timeout=timeout_s)
        self.controller.white_referencing=True
        

        

    def wait(self):
        while self.timeout_s>0:
            if 'wrsuccess' in self.listener.queue:
                self.listener.queue.remove('wrsuccess')
                self.success()
                return
            elif 'nonumspectra' in self.listener.queue:
                self.listener.queue.remove('nonumspectra')
                self.controller.queue.insert(0,{self.controller.configure_instrument:[]})
                self.controller.configure_instrument()
                return
            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
                #If the next thing we're going to do is take a spectrum then set override to True - we will already have checked in with the user about those things when we first decided to take a spectrum.
                if self.controller.wr in self.controller.queue[0]:
                    self.controller.queue[0][self.controller.wr][0]=True
                else:
                    print('here is the queue')
                    for item in self.controller.queue:
                        print(item)
                self.controller.queue.insert(0,{self.controller.set_save_config:[]})
                self.controller.set_save_config()
                return
            elif 'wrfailed' in self.listener.queue:
                self.listener.queue.remove('wrfailed')

                if self.first_try==True and not self.cancel: #Actually this is always true since a new OptHandler gets created for each attempt
                    self.controller.log('Error: Failed to take white reference. Retrying.')
                    self.first_try=False
                    time.sleep(15) #Might improve the odds that the second attempt will succeed (not sure).
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt('Error: Failed to take white reference.\n\nPaused.',retry=True)
                    self.wait_dialog.top.geometry('376x175')
                    self.controller.log('Error: Failed to take white reference.')
                elif not self.cancel:
                    self.interrupt('Error: Failed to take white reference.',retry=True)
                    self.set_text(self.controller.sample_label_entries[self.controller.current_sample_gui_index],self.controller.current_label)  
                else: #You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt('Error: Failed to take white reference.\n\nData acquisition canceled.',retry=False)
                    self.wait_dialog.top.geometry('376x175')
                    #Does nothing in automatic mode
                    self.controller.clear()
                
                return
                
            elif 'wrfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('wrfailedfileexists')
                
                if self.controller.overwrite_all:
                    #self.wait_dialog.top.destroy()
                    self.remove_retry(need_new=False) #No need for new wait dialog
                    
                elif self.controller.manual_automatic.get()==0 and self.controller.script_running==False:
                    self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                    buttons={
                        'yes':{
                            self.remove_retry:[]
                        },

                        'no':{
                            self.finish:[]
                        }
                    }
                        
                    self.wait_dialog.set_buttons(buttons)
                else:
                    self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                    buttons={
                        'yes':{
                            self.remove_retry:[]
                        },
                        'yes to all':{
                            self.controller.set_overwrite_all:[True],
                            self.remove_retry:[]
                        },
                        'no':{
                            self.finish:[]
                        }
                    }
                        
                    self.wait_dialog.set_buttons(buttons,button_width=10)
                self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 175, 107, 69))
                return
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        #Before timing out, set override to True so that if the user decides to retry they aren't reminded about optimizing, etc again.
        if self.controller.wr in self.controller.queue[0]:
            self.controller.queue[0][self.controller.wr][0]=True
        self.timeout()
                
    def success(self):
        self.controller.wr_time=int(time.time())
        super(WhiteReferenceHandler, self).success()
        
class DataHandler(CommandHandler):
    def __init__(self, controller, title='Transferring data...',label='Tranferring data...', source=None, temp_destination=None, final_destination=None):
        self.listener=controller.spec_listener
        super().__init__(controller, title, label, timeout=2*BUFFER)
        self.source=source
        self.temp_destination=temp_destination
        self.final_destination=final_destination
        self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))
        
    def wait(self):
        while self.timeout_s>0:
            #self.spec_commander.get_data(filename)
            if 'datacopied' in self.listener.queue:
                self.listener.queue.remove('datacopied')

                if self.temp_destination!=None and self.final_destination!=None:
                    try:
    
                        shutil.move(self.temp_destination, self.final_destination)
                        #self.timeout('Error: Operation timed out while trying to transfer data.') #This is for testing
                        self.success()
                        return
                        
                    except Exception as e:
                        print('1')
                        print(e)
                        
                        self.interrupt('Error transferring data',retry=True)
                        return

            elif 'datafailure' in self.listener.queue:
                self.listener.queue.remove('datafailure')
                self.interrupt('Error transferring data',retry=True)
                #dialog=ErrorDialog(self.controller,label='Error: Failed to acquire data.\nDoes the file exist? Do you have permission to use it?')
                return
            time.sleep(INTERVAL)
            self.timeout_s=self.timeout_s-INTERVAL
        self.timeout()

    def success(self):
        self.controller.complete_queue_item()
        self.interrupt('Data transferred successfully.')
        if len(self.controller.queue)>0:
            self.controller.next_in_queue()

class ProcessHandler(CommandHandler):
    def __init__(self, controller, title='Processing...', label='Processing...'):
        
        self.listener=controller.spec_listener
        super().__init__(controller, title, label,timeout=20000+BUFFER)
        self.outputfile=self.controller.output_file_entry.get()
        dir=self.controller.output_dir_entry.get()
        if (self.controller.opsys=='Linux' or self.controller.opsys=='Mac') and self.controller.plot_local_remote=='local':
            if dir[-1]!='/':dir+='/'
        else:
            if dir[-1]!='\\': dir+='\\'
        self.outputfile=dir+self.outputfile
        self.wait_dialog.set_buttons({})
        self.wait_dialog.top.wm_geometry('376x130')
         #Normally we have a pause and a cancel option if there are additional items in the queue, but it doesn't make much sense to cancel processing halfway through, so let's just not have the option.
        
    def wait(self):
        while True: #self.timeout_s>0: Never going to timeout
            if self.timeout_s%20==0:
                print(self.timeout_s)
            if 'processsuccess' in self.listener.queue or 'processsuccessnocorrection' in self.listener.queue or 'processsuccessnolog' in self.listener.queue:
                warnings=''
                if 'processsuccess' in self.listener.queue:
                    self.listener.queue.remove('processsuccess')
                if 'processsuccessnolog' in self.listener.queue:
                    self.listener.queue.remove('processsuccessnolog')
                    warnings='No log found in data directory.\n First line of log file should be  #AutoSpec log'
                if 'processsuccessnocorrection' in self.listener.queue:
                    self.listener.queue.remove('processsuccessnocorrection')
                    warnings='Correction for non-Lambertian properties of\nSpectralon was not applied.'
                
                if '.' not in self.outputfile:
                    self.outputfile+='.csv'

                self.controller.log('Files processed. '+warnings.replace('\n',' ' )+'\n\t'+self.outputfile)
                if self.controller.proc_local_remote=='local': #Move on to finishing the process by transferring the data from temp to final destination
                    print('local!')
                    try:
                        self.controller.complete_queue_item()
                        self.controller.next_in_queue()
                        self.success()
                        if warnings !='':
                            self.wait_dialog.top.wm_geometry('376x185')
                    except Exception as e:
                        print(e)
                        self.interrupt('Error: Could not transfer data to local folder.')

                        #Leave the temp data directory clean
                        try:
                            os.remove(self.controller.spec_temp_loc+'proc_temp.csv')
                            os.remove(self.controller.spec_temp_loc+'proc_temp_log.txt')
                        except:
                            pass
                else: #if the final destination was remote then we're already done.
                    print('remote')
                    self.success(warnings=warnings)
                    if warnings !='':
                        self.wait_dialog.top.wm_geometry('376x185')
                return
                
            elif 'processerrorfileexists' in self.listener.queue:

                self.listener.queue.remove('processerrorfileexists')
                self.interrupt('Error processing files: Output file already exists')
                self.controller.log('Error processing files: output file exists.')
                return
                
            elif 'processerrornodirectory' in self.listener.queue:

                self.listener.queue.remove('processerrornodirectory')
                self.interrupt('Error processing files:\nInput directory does not exist.')
                self.controller.log('Error processing files: Input directory does not exist.')
                return
                
            elif 'processerrorwropt' in self.listener.queue:

                self.listener.queue.remove('processerrorwropt')
                self.interrupt('Error processing files.\n\nDid you optimize and white reference before collecting data?')
                self.wait_dialog.top.wm_geometry('376x150')
                self.log('Error processing files')
                return
                
            elif 'processerror' in self.listener.queue:

                self.listener.queue.remove('processerror')
                self.wait_dialog.top.wm_geometry('376x175')
                self.interrupt('Error processing files.\n\nIs ViewSpecPro running? Do directories exist?',retry=True)
                self.controller.log('Error processing files')
                return
                
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL

        self.timeout()
        
    def success(self,warnings=''):
        #self.controller.complete_queue_item()
        interrupt_string='Data processed successfully'
        if warnings!='':
            interrupt_string+='\n\n'+warnings
        self.interrupt(interrupt_string)
        self.controller.plot_input_file=self.outputfile
        print(self.controller.proc_local_remote)
        print(self.controller.plot_local_remote)
        if self.controller.proc_local_remote=='remote':
            self.controller.plot_local_remote='remote'
        else:
            self.controller.plot_local_remote='local'
        self.wait_dialog.top.wm_geometry('376x130')
        
        # if len(self.controller.queue)>0:
        #     self.controller.next_in_queue()
        while len(self.controller.queue)>0:
            self.controller.complete_queue_item()
        self.controller.process_top.destroy()
        self.wait_dialog.top.lift()
        
    
        
        
class CloseHandler(CommandHandler):
    def __init__(self, controller, title='Closing...', label='Setting to default geometry and closing...', buttons={'cancel':{}}):
        self.listener=controller.pi_listener
        super().__init__(controller, title, label,timeout=90+BUFFER)
        

        
    def wait(self):
        while self.timeout_s>0:
            if 'donemoving' in self.listener.queue:
                self.listener.queue.remove('donemoving')
                self.success()
                return

            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        
        self.timeout()
    def success(self):
        self.controller.complete_queue_item()
        if len(self.controller.queue)==0:
            self.interrupt('Finished. Ready to exit')
            self.wait_dialog.set_buttons({'exit':{exit_func:[]}})
        else:
            self.controller.next_in_queue()
            
class MotionHandler(CommandHandler):
    def __init__(self, controller, title='Moving...', label='Moving...', buttons={'cancel':{}}, timeout=90, new_sample_loc='foo', steps=False, destination=None):
        self.steps=steps
        self.listener=controller.pi_listener
        try:
            super().__init__(controller, title, label,timeout=timeout)
        except:
            print('exception in super init in motion handler') #There has been an erro rthat has come up a couple of times saying the motion handler has no attribute self.steps. Maybe because the call to super is silently failing so this method never finishes?
        self.new_sample_loc=new_sample_loc
        self.steps=steps
        self.destination=destination




    def wait(self):
        while self.timeout_s>0:
            if 'donemoving' in self.listener.queue:
                self.listener.queue.remove('donemoving')
                self.success()
                return
            elif 'nopiconfig' in self.listener.queue:
                print('nopiconfig')
                self.listener.queue.remove('nopiconfig')
                #self.controller.queue.append({self.controller.set_manual_automatic:[]})
                self.controller.set_manual_automatic(self,force=1)
                
                return

            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
            
        
        self.timeout()
    def success(self):

        if 'emission' in self.label:
            self.controller.angles_change_time=time.time()
            self.controller.e=self.destination
            try:
                self.controller.log('Goniometer moved to an emission angle of '+str(self.destination)+' degrees.')
            except:
                self.controller.log('Emission set')
        elif 'incidence' in self.label:
            self.controller.angles_change_time=time.time()
            self.controller.i=self.destination
            try:
                self.controller.log('Goniometer moved to an incidence angle of '+str(self.destination)+' degrees.')
            except:
                self.controller.log('Incidence set')
                
        elif 'azimuth' in self.label:
            self.controller.angles_change_time=time.time()
            self.controller.az=self.destination
            try:
                self.controller.log('Goniometer moved to an azimuth angle of '+str(self.destination)+' degrees.')
            except:
                self.controller.log('Azimuth set')
            
        elif 'tray' in self.label:
            try:
                print(self.steps) #For some reason sometimes get an error saying MotionHandler has no attribute self.steps
            except:
                self.steps=False
            if self.steps==False: #If we're specifying a position, not a number of motor steps
                self.controller.log('Sample tray moved to '+str(self.new_sample_loc)+' position.')
                try:
                    self.controller.sample_tray_index=self.controller.available_sample_positions.index(self.new_sample_loc)
                    self.controller.goniometer_view.set_current_sample(self.controller.available_sample_positions[self.controller.sample_tray_index])
    
                except:
                    self.controller.sample_tray_index=-1 #White reference
                    self.controller.goniometer_view.set_current_sample('WR')
                samples_in_gui_order=[]
                for var in self.controller.sample_pos_vars:
                    samples_in_gui_order.append(var.get())
    
                try:
                    i=samples_in_gui_order.index(self.new_sample_loc)
                    self.controller.current_sample_gui_index=i
                except:
                    self.controller.current_sample_gui_index=0
                self.controller.current_label=self.controller.sample_label_entries[self.controller.current_sample_gui_index].get()
            else: #If we specified steps, don't change the tray index, but still tell the goniometer view to change back from 'Moving'
                if self.controller.sample_tray_index>-1:
                    self.controller.goniometer_view.set_current_sample(self.controller.available_sample_positions[self.controller.sample_tray_index])
                else:
                    self.controller.goniometer_view.set_current_sample('WR')
                
                self.controller.log('Sample tray moved '+str(self.new_sample_loc)+' steps.')


        else:
            self.controller.log('Something moved! Who knows what?')

        super(MotionHandler,self).success()
        
        
class SaveConfigHandler(CommandHandler):
    def __init__(self, controller, title='Setting Save Configuration...', label='Setting save configuration...', timeout=30):
        self.listener=controller.spec_listener
        self.keep_around=False
        self.unexpected_files=[]
        self.listener.new_dialogs=False
        super().__init__(controller, title, label=label,timeout=timeout)

    def wait(self):
        t=30
        while 'donelookingforunexpected' not in self.listener.queue and t>0:
            t=t-INTERVAL
            time.sleep(INTERVAL)
        if t<=0:
            self.timeout()
            return
            
        if len(self.listener.unexpected_files)>0:
            self.keep_around=True
            self.unexpected_files=list(self.listener.unexpected_files)
            self.listener.unexpected_files=[]
            
        self.listener.new_dialogs=True
        self.listener.queue.remove('donelookingforunexpected')

        
        while self.timeout_s>0:
            self.timeout_s-=INTERVAL
            if 'saveconfigsuccess' in self.listener.queue:

                self.listener.queue.remove('saveconfigsuccess')
                self.success()
                return
                
            elif 'saveconfigfailedfileexists' in self.listener.queue:
                
                self.listener.queue.remove('saveconfigfailedfileexists')
                self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                
                if self.controller.overwrite_all:
                    #self.wait_dialog.top.destroy()
                    self.remove_retry(need_new=False) #No need for new wait dialog
                    
                elif self.controller.manual_automatic.get()==0 and self.controller.script_running==False:
                    self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                    buttons={
                        'yes':{
                            self.remove_retry:[]
                        },

                        'no':{
                            self.finish:[]
                        }
                    }
                        
                    self.wait_dialog.set_buttons(buttons)
                    
                else:
                    self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                    buttons={
                        'yes':{
                            self.remove_retry:[]
                        },
                        
                        'yes to all':{
                            self.controller.set_overwrite_all:[True],
                            self.remove_retry:[]
                        },
                        'no':{
                            self.finish:[]
                        }
                    }
                    

                    self.wait_dialog.set_buttons(buttons,button_width=10)
                self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 175, 107, 69))
                return

            elif 'saveconfigfailed' in self.listener.queue:
                self.listener.queue.remove('saveconfigfailed')
                self.interrupt('Error: There was a problem setting the save configuration.\nIs the spectrometer connected?\nIs the spectrometer computer awake and unlocked?',retry=True)
                self.controller.log('Error: There was a problem setting the save configuration.')
                self.controller.spec_save_path=''
                self.controller.spec_basename=''
                self.controller.spec_num=None

                return
                
            elif 'saveconfigerror' in self.listener.queue:
                self.listener.queue.remove('saveconfigerror')
                self.interrupt('Error: There was a problem setting the save configuration.\n\nIs the spectrometer connected?\nIs the spectrometer computer awake and unlocked?',retry=True)
                self.controller.log('Error: There was a problem setting the save configuration.')
                self.controller.spec_save_path=''
                self.controller.spec_basename=''
                self.controller.spec_num=None

                return
                
            time.sleep(INTERVAL)
            
        self.timeout(log_string='Error: Operation timed out while waiting to set save configuration.')
        

    def success(self):

        self.controller.spec_save_path=self.controller.spec_save_dir_entry.get()
        self.controller.spec_basename = self.controller.spec_basename_entry.get()
        spec_num=self.controller.spec_startnum_entry.get()
        self.controller.spec_num=int(spec_num)
        
        self.allow_exit=True
        self.controller.log('Save configuration set.\n\tDirectory: '+self.controller.spec_save_dir_entry.get()+'\n\tBasename: '+self.controller.spec_basename_entry.get()+'\n\tStart number: '+self.controller.spec_startnum_entry.get(),write_to_file=True)
        
        if self.keep_around:
            dialog=WaitDialog(self.controller, title='Warning: Untracked Files',buttons={'ok':[]})
            dialog.top.geometry('400x300')
            dialog.interrupt('There are untracked files in the\ndata directory. Do these belong here?\n\nIf the directory already contains an AutoSpec\nlog file, metadata will be appended to that file.')
            

            
            self.controller.log('Untracked files in data directory:\n\t'+'\n\t'.join(self.unexpected_files))
            
            listbox=ScrollableListbox(dialog.top,self.wait_dialog.bg,self.wait_dialog.entry_background, self.wait_dialog.listboxhighlightcolor,)
            for file in self.unexpected_files:
                listbox.insert(END,file)
                
            listbox.config(height=1)


        super(SaveConfigHandler, self).success()


                
    
class SpectrumHandler(CommandHandler):
    def __init__(self, controller, title='Saving Spectrum...', label='Saving spectrum...'):
        timeout=int(controller.spec_config_count)/8+BUFFER #This timeout grows a little faster than the actual time to take a spectrum grows, which would be numspectra/9
        self.listener=controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout)

        

        
    def wait(self):
        while self.timeout_s>0:
                

            if 'failedtosavefile' in self.listener.queue:
                self.listener.queue.remove('failedtosavefile')
                self.interrupt('Error: Failed to save file.\nAre you sure the spectrometer is connected?',retry=True)
                self.wait_dialog.top.wm_geometry('420x130')
                return

            elif 'noconfig' in self.listener.queue:
                self.listener.queue.remove('noconfig')
                #If the next thing we're going to do is take a spectrum then set override to True - we will already have checked in with the user about those things when we first decided to take a spectrum.
                if self.controller.take_spectrum in self.controller.queue[0]:
                    print('setting override to true')
                    self.controller.queue[0][self.controller.take_spectrum][0]=True
                else:
                    for item in self.controller.queue:
                        print(item)
                self.controller.queue.insert(0,{self.controller.set_save_config:[]})
                self.controller.set_save_config()#self.controller.take_spectrum, [True])
                return
                
            elif 'nonumspectra' in self.listener.queue:
                self.listener.queue.remove('nonumspectra')
                self.controller.queue.insert(0,{self.controller.configure_instrument:[]})
                self.controller.configure_instrument()
                return
                
            elif 'savedfile' in self.listener.queue:
                self.listener.queue.remove('savedfile')

                self.success()
                return
            elif 'savespecfailedfileexists' in self.listener.queue:

                self.listener.queue.remove('savespecfailedfileexists')
                self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                self.wait_dialog.top.wm_geometry('420x145')
                
                if self.controller.overwrite_all:
                    #self.wait_dialog.top.destroy()
                    self.remove_retry(need_new=False) #No need for a new wait_dialog
                    
                elif self.controller.manual_automatic.get()==0 and self.controller.script_running==False:
                    self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                    self.wait_dialog.top.wm_geometry('420x130')
                    buttons={
                        'yes':{
                            self.remove_retry:[]
                        },

                        'no':{
                            self.finish:[]
                        }
                    }
                        
                    self.wait_dialog.set_buttons(buttons)
                    
                else:
                    self.interrupt('Error: File exists.\nDo you want to overwrite this data?')
                    self.wait_dialog.top.wm_geometry('420x130')
                    buttons={
                        'yes':{
                            self.remove_retry:[]
                        },
                        'yes to all':{
                            self.controller.set_overwrite_all:[True],
                            self.remove_retry:[]
                        },
                        'no':{
                            self.finish:[]
                        }
                    }
                    
                    self.wait_dialog.set_buttons(buttons,button_width=10)
                return
                
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL
        dialog_string='Error: Operation timed out while waiting to save spectrum.\n\nIf it completes later, an unexpected file could be saved to the data directory.\nThis could cause errors. Restart the software to be safe.'
        log_string='Error: Operation timed out while waiting to save spectrum.\n\tIf it completes later, an unexpected file could be saved to the data directory.\n\tThis could cause errors. Restart the software to be safe.'
        self.timeout(log_string=log_string, dialog_string=dialog_string,retry=True)
        self.wait_dialog.top.wm_geometry("680x173")

        
    def success(self):
        self.allow_exit=True
        
        #Build a string that tells the number for the spectrum that was just saved. We'll use this in the log (maybe)
        lastnumstr=str(self.controller.spec_num)
        while len(lastnumstr)<NUMLEN:
            lastnumstr='0'+lastnumstr
        
        #Increment the spectrum number
        self.controller.spec_num+=1
        self.controller.spec_startnum_entry.delete(0,'end')
        spec_num_string=str(self.controller.spec_num)
        while len(spec_num_string)<NUMLEN:
            spec_num_string='0'+spec_num_string
        self.set_text(self.controller.spec_startnum_entry,spec_num_string)
        
        self.controller.plot_input_dir=self.controller.spec_save_dir_entry.get()
        
        #Use the last saved spectrum number for the log file.
        numstr=str(self.controller.spec_num-1)
        while len(numstr)<NUMLEN:
            numstr='0'+numstr
        
        #Log whether it was a white reference or a regular spectrum that just got saved. 
        info_string=''
        label=''
        if self.controller.white_referencing: 
            self.controller.white_referencing=False
            info_string='White reference saved.'
            label='White reference'
        else:
            info_string='Spectrum saved.'
            label=self.controller.sample_label_entries[self.controller.current_sample_gui_index].get()
        
        info_string+='\n\tSpectra averaged: ' +str(self.controller.spec_config_count)+'\n\ti: '+str(self.controller.i)+'\n\te: '+str(self.controller.e)+'\n\tfilename: '+self.controller.spec_save_path+'\\'+self.controller.spec_basename+lastnumstr+'.asd'+'\n\tLabel: '+label+'\n'
        #If it was a garbage spectrum, we don't need all of the information about it. Instead, just delete it and log that it happened.
        if 'garbage' in self.wait_dialog.label:
                
            self.controller.spec_commander.delete_spec(self.controller.spec_save_path,self.controller.spec_basename,lastnumstr)
            
            t=BUFFER
            while t>0:
                if 'rmsuccess' in self.listener.queue:
                    self.listener.queue.remove('rmsuccess')
                    self.controller.log('\nSaved and deleted a garbage spectrum ('+self.controller.spec_basename+lastnumstr+'.asd).')
                    break
                elif 'rmfailure' in self.listener.queue:
                    self.listener.queue.remove('rmfailure')
                    self.controller.log('\nError: Failed to remove placeholder spectrum ('+self.controller.spec_basename+lastnumstr+'.asd. This data is likely garbage. ')
                    break
                t=t-INTERVAL
                time.sleep(INTERVAL)
            if t<=0:
                self.controller.log('\nError: Operation timed out removing placeholder spectrum ('+self.controller.spec_basename+lastnumstr+'.asd). This data is likely garbage.')
        else:
            self.controller.log(info_string,True)
            
        self.controller.clear()
        super(SpectrumHandler, self).success()
        
class ErrorDialog(Dialog):
    def __init__(self, controller, title='Error', label='Error!', buttons={'ok':{}}, listener=None,allow_exit=False, info_string=None, topmost=True, button_width=30, width=None,height=None):
        
        #buttons['ok']={controller.unfreeze:[]}
        
        self.listener=None
        if info_string==None:
            self.info_string=label+'\n'
        else:
            self.info_string=info_string
        if width==None or height==None:
            super().__init__(controller, title, label,buttons,allow_exit=False, info_string=None, button_width=button_width)#self.info_string)
        else:
            super().__init__(controller, title, label,buttons,allow_exit=False, info_string=None, button_width=button_width,width=width, height=height)
        if topmost==True:
            try:
                self.top.attributes("-topmost", True)
            except(Exception):
                print(str(Exception))

def limit_len(input, max):
    return input[:max]
    
def validate_int_input(input, min, max):
    try:
        input=int(input)
    except:
        return False
    if input>max: return False
    if input<min: return False
    return True
    

class RemoteFileExplorer(Dialog):
    def __init__(self,controller, target=None,title='Select a directory',label='Select a directory',buttons={'ok':{},'cancel':{}}, directories_only=True):

        super().__init__(controller, title=title, buttons=buttons,label=label, button_width=20)
        
        self.timeout_s=BUFFER
        self.controller=controller
        self.remote_directory_worker=self.controller.remote_directory_worker
        self.listener=self.controller.spec_listener
        self.target=target
        self.current_parent=None
        self.directories_only=directories_only
        
        self.nav_frame=Frame(self.top,bg=self.bg)
        self.nav_frame.pack()
        self.new_button=Button(self.nav_frame, fg=self.textcolor,text='New Folder',command=self.askfornewdir, width=10)
        self.new_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.new_button.pack(side=RIGHT, pady=(5,5),padx=(0,10))

        self.path_entry_var = StringVar()
        self.path_entry_var.trace('w', self.validate_path_entry_input)
        self.path_entry=Entry(self.nav_frame, width=50,bg=self.entry_background,textvariable=self.path_entry_var,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.path_entry.pack(padx=(5,5),pady=(5,5),side=RIGHT)
        self.back_button=Button(self.nav_frame, fg=self.textcolor,text='<-',command=self.back,width=1)
        self.back_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
        self.back_button.pack(side=RIGHT, pady=(5,5),padx=(10,0))
        
        self.listbox=ScrollableListbox(self.top,self.bg,self.entry_background, self.listboxhighlightcolor,)
        self.listbox.bind("<Double-Button-1>", self.expand)
        self.path_entry.bind('<Return>',self.go_to_path)
        
        if target.get()=='':
            self.expand(newparent='C:\\Users')
            self.current_parent='C:\\Users'
        else:
            if directories_only:
                self.expand(newparent=target.get().replace('/','\\'))
            else:
                path=target.get().replace('/','\\')
                if '\\' in path:
                    path_el=path.split('\\')
                    if '.' in path_el[-1]:
                        path='\\'.join(path_el[:-1])
                    self.expand(newparent=path)
                else:
                    self.expand(newparent=path)
            
    def validate_path_entry_input(self,*args):
        text=self.path_entry.get()
        text=rm_reserved_chars(text)

        self.path_entry.delete(0,'end')
        self.path_entry.insert(0,text)      
        
    def askfornewdir(self):
        input_dialog=NewDirDialog(self.controller, self)

    def mkdir(self, newdir):
        status=self.remote_directory_worker.mkdir(newdir)
        print('Make dir status:')
        print(status)

        if status=='mkdirsuccess':
            self.expand(None,'\\'.join(newdir.split('\\')[0:-1]))
            self.select(newdir.split('\\')[-1])
        elif status=='mkdirfailedfileexists':
            dialog=ErrorDialog(self.controller,title='Error',label='Could not create directory:\n\n'+newdir+'\n\nFile exists.')
            self.expand(newparent=self.current_parent)
        elif status=='mkdirfailed':
            dialog=ErrorDialog(self.controller,title='Error',label='Could not create directory:\n\n'+newdir)
            self.expand(newparent=self.current_parent)
        
    def back(self):
        if len(self.current_parent)<4:
            return
        parent='\\'.join(self.current_parent.split('\\')[0:-1])
        self.expand(newparent=parent)
        
    def go_to_path(self, source):
        parent=self.path_entry.get().replace('/','\\')
        self.path_entry.delete(0,'end')
        self.expand(newparent=parent)
        
    
    def expand(self, source=None, newparent=None, buttons=None,select=None, timeout=5,destroy=False):

        global CMDNUM
        if newparent==None:
            index=self.listbox.curselection()[0]
            if self.listbox.itemcget(index, 'foreground')=='darkblue':
                return
            newparent=self.current_parent+'\\'+self.listbox.get(index)
        if newparent[1:2]!=':' or len(newparent)>2 and newparent[1:3]!=':\\':
            dialog=ErrorDialog(self.controller,title='Error: Invalid input',label='Error: Invalid input.\n\n'+newparent+'\n\nis not a valid filename.')
            if self.current_parent==None:
                self.expand(newparent='C:\\Users')
            return
        if newparent[-1]=='\\':
            newparent=newparent[:-1]
        #Send a command to the spec compy asking it for directory contents
        if self.directories_only==True:
            status=self.remote_directory_worker.get_contents(newparent)
        else:
            status=self.remote_directory_worker.get_contents(newparent)
        
        #if we succeeded, the status will be a list of the contents of the directory
        if type(status)==list:

            self.listbox.delete(0,'end')
            for dir in status:
                if dir[0:2]=='~:':
                    self.listbox.insert(END,dir[2:])
                    self.listbox.itemconfig(END, fg='darkblue')
                else:
                    self.listbox.insert(END,dir)
            self.current_parent=newparent
            
            self.path_entry.delete(0,'end')
            self.path_entry.insert('end',newparent)
            if select!=None:
                self.select(select)
            
            if destroy:
                self.close()

                
        elif status=='listdirfailed':
            if self.current_parent==None:
                print('setting to RiceData')
                self.current_parent='R:\\RiceData'
                # self.current_parent='\\'.join(newparent.split('\\')[:-1])
                # if self.current_parent=='':
                #     self.current_parent='C:\\Users'
            if buttons==None:
                print('setting buttons')

                buttons={
                    'yes':{
                        self.mkdir:[newparent]
                    },
                    'no':{
                        self.expand:[None,self.current_parent]
                    }
                }
            dialog=ErrorDialog(self.controller,title='Error',label=newparent+'\ndoes not exist. Do you want to create this directory?',buttons=buttons)
            return
        elif status=='listdirfailedpermission':
            dialog=ErrorDialog(self.controller,label='Error: Permission denied for\n'+newparent)
            return
        elif status=='timeout':
            dialog=ErrorDialog(self.controller, label='Error: Operation timed out.\nCheck that the automation script is running on the spectrometer computer.')
            self.cancel()
            
    def select(self,text):
        if '\\' in text:
            text=text.split('\\')[0]
            

        try:
            index = self.listbox.get(0, 'end').index(text)
        except:
            #time.sleep(0.5)
            print('except')
            #self.select(text)
            index=0

        self.listbox.selection_set(index)
        self.listbox.see(index)
        
    def ok(self):
        index=self.listbox.curselection()
        if len(index)>0 and self.directories_only:
            if self.listbox.itemcget(index[0], 'foreground')=='darkblue':
                index=[]
        elif len(index)==0 and not self.directories_only:
            return
                
        self.target.delete(0,'end')

        if self.directories_only:
            if len(index)>0 and self.path_entry.get()==self.current_parent:
                self.controller.unfreeze()
                self.target.delete(0,'end')
                self.target.insert(0,self.current_parent+'\\'+self.listbox.get(index[0]))
                self.close()
            elif self.path_entry.get()==self.current_parent:
                self.controller.unfreeze()
                self.target.delete(0,'end')
                self.target.insert(0,self.current_parent)
                self.close()
            else:
                buttons={
                    'yes':{
                        self.mkdir:[self.path_entry.get()],
                        self.expand:[None,'\\'.join(self.path_entry.get().split('\\')[0:-1])],
                        self.select:[self.path_entry.get().split('\\')[-1]],
                        self.ok:[]
                    },
                    'no':{
                    }
                }
                self.expand(newparent=self.path_entry.get(), buttons=buttons, destroy=True)
                self.controller.unfreeze()
                self.target.delete(0,'end')
                self.target.insert(0,self.current_parent)

        else:
            if len(self.listbox.curselection())>0 and self.path_entry.get()==self.current_parent and  self.listbox.itemcget(index[0], 'foreground')=='darkblue':
                self.controller.unfreeze()
                self.target.delete(0,'end')
                self.target.insert(0,self.current_parent+'\\'+self.listbox.get(index[0]))
                self.close()
    

            
class RemoteDirectoryWorker():
    def __init__(self, spec_commander, read_command_loc, listener):
        self.read_command_loc=read_command_loc
        self.spec_commander=spec_commander
        self.listener=listener
        self.timeout_s=BUFFER
    def reset_timeout(self):
        self.timeout_s=BUFFER
    def wait_for_contents(self,cmdfilename):
        #Wait to hear what the listener finds
        self.reset_timeout()
        while self.timeout_s>0:
            #print('looking for '+cmdfilename)
            #If we get a file back with a list of the contents, replace the old listbox contents with new ones.
            #The cmdfilename should be e.g. listdir&R=+RiceData+Kathleen+spectral_data
            if cmdfilename in self.listener.queue:
                contents=[]
                with open(self.read_command_loc+cmdfilename,'r') as f:
                    next=f.readline().strip('\n')
                    while next!='':
                        contents.append(next)
                        next=f.readline().strip('\n')
                self.listener.queue.remove(cmdfilename)
                return contents
                
            elif 'listdirfailed' in self.listener.queue:
                self.listener.queue.remove('listdirfailed')
                return 'listdirfailed'
                
            elif 'listdirfailedpermission' in self.listener.queue:
                self.listener.queue.remove('listdirfailedpermission')
                return 'listdirfailedpermission'
            
            elif 'listfilesfailed' in self.listener.queue:
                self.listener.queue.remove('listfilesfailed')
                return 'listfilesfailed'
            
            time.sleep(INTERVAL)
            self.timeout_s-=INTERVAL 
        return 'timeout'
        
        
    #Assume parent has already been validated, but don't assume it exists
    def get_dirs(self,parent):
        
        cmdfilename=self.spec_commander.listdir(parent)
        status=self.wait_for_contents(cmdfilename)
        return status
        
    def get_contents(self,parent):
 
        cmdfilename=self.spec_commander.list_contents(parent)
        return self.wait_for_contents(cmdfilename)
        
    def mkdir(self, newdir):

        self.spec_commander.mkdir(newdir)
                
        while True:
            if 'mkdirsuccess' in self.listener.queue:
                self.listener.queue.remove('mkdirsuccess')
                return 'mkdirsuccess'
            elif 'mkdirfailedfileexists' in self.listener.queue:
                self.listener.queue.remove('mkdirfailedfileexists')
                return 'mkdirfailedfileexists'
            elif 'mkdirfailed' in self.listener.queue:
                self.listener.queue.remove('mkdirfailed')
                return 'mkdirfailed'
                
        time.sleep(INTERVAL)

class ScrollableListbox(Listbox):
    def __init__(self, frame, bg, entry_background, listboxhighlightcolor,selectmode=SINGLE):
        
        self.scroll_frame=Frame(frame,bg=bg)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        self.scrollbar = Scrollbar(self.scroll_frame, orient=VERTICAL)
        self.scrollbar.pack(side=RIGHT, fill=Y,padx=(0,10))
        self.scrollbar.config(command=self.yview)
        
        super().__init__(self.scroll_frame,yscrollcommand=self.scrollbar.set, selectmode=selectmode,bg=entry_background, selectbackground=listboxhighlightcolor, height=15,exportselection=0)
        self.pack(side=LEFT,expand=True, fill=BOTH,padx=(10,0))
    
    def destroy(self):
        self.scrollbar.destroy()
        super().destroy()


                
class IntInputDialog(Dialog):
    def __init__(self,controller,title,label,values={},buttons={'ok':{},'cancel':{}}):
        super().__init__(controller,title,label,buttons,allow_exit=False)
        self.values=values
        self.entry_frame=Frame(self.top,bg=self.bg)
        self.entry_frame.pack(pady=(10,20))
        self.labels={}
        self.entries={}
        self.mins={}
        self.maxes={}
        for val in values:
            frame=Frame(self.entry_frame,bg=self.bg)
            frame.pack(pady=(5,5))
            self.labels[val]=Label(frame, text='{0:>15}'.format(val)+': ',fg=self.textcolor,bg=self.bg)
            self.labels[val].pack(side=LEFT,padx=(3,3))
            if val !='Tray position':
                self.entries[val]=Entry(frame,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
                self.entries[val].pack(side=LEFT)
            else:
                self.entries[val]=StringVar()
                self.entries[val].set('White reference')
                menu = OptionMenu(frame, self.entries[val],'{0:15}'.format('White reference'), '{0:18}'.format('1'),'2          ','3          ','4          ','5          ')
                menu.configure(width=15,highlightbackground=self.controller.highlightbackgroundcolor)
                menu.pack()
                
            
        self.set_buttons(buttons)
            
    def ok(self):
        bad_vals=[]
        for val in self.values:
            self.mins[val]=self.values[val][1]
            self.maxes[val]=self.values[val][2]
            valid=validate_int_input(self.entries[val].get(),self.mins[val],self.maxes[val]) #Weird for tray position - not valid for white reference

                
            valid_sep=True
            if valid:
                #self.values[val][0]=self.entries[val].get()
                if val=='Incidence' or val=='Emission' or val=='Azimuth':
                    valid_sep=self.controller.validate_distance(self.entries['Incidence'].get(),self.entries['Emission'].get(), self.entries['Azimuth'].get())
                        
                elif val=='Tray position':
                    self.controller.sample_tray_index=int(self.entries[val].get())-1
                    
            elif val=='Tray position': #This is a weird way of handling this. Happens whenever the user selects White Reference from drop down list.
                if 'White reference' in self.entries[val].get():
                    self.controller.sample_tray_index=-1
                else: #We should never get here
                    print(self.entries[val].get())
                    self.controller.sample_tray_index=int(self.entries[val].get())-1
            else:
                bad_vals.append(val)
        if len(bad_vals)==0 and valid_sep:
            incidence=int(self.entries['Incidence'].get())
            emission=int(self.entries['Emission'].get())
            azimuth=int(self.entries['Azimuth'].get())
            

            self.controller.e=emission
            self.controller.i=incidence
            self.controller.az=azimuth
            
        if len(bad_vals)==0 and valid_sep:
            self.top.destroy()
            dict=self.buttons['ok']
            for func in dict:
                args=dict[func]
                func(*args)
        else:
            err_str='Error: Invalid '
            if len(bad_vals)==1:
                for val in bad_vals:
                    err_str+=val.lower()+' value.\nPlease enter a number from '+str(self.mins[val]) +' to '+str(self.maxes[val])+'.'
            elif valid_sep:
                err_str+='input. Please enter the following:\n\n'
                for val in bad_vals:
                    err_str+=val+' from '+str(self.mins[val])+' to '+str(self.maxes[val])+'\n'
            else:
                err_str+='angular separation.\nEmission must be at least '+str(self.controller.required_angular_separation)+' degrees different than incidence.'
            dialog=ErrorDialog(self.controller,title='Error: Invalid Input',label=err_str)
        
            
class NewDirDialog(Dialog):
    def __init__(self, controller, fexplorer,label='Enter input', title='Enter input'):
        super().__init__(controller,label=label,title=title, buttons={'ok':{self.get:[]},'cancel':{}},button_width=15)
        self.dir_entry=Entry(self.top,width=40,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
        self.dir_entry.pack(padx=(10,10))
        self.listener=self.controller.spec_listener
        self.fexplorer=fexplorer


    def get(self):
        subdir=self.dir_entry.get()
        if subdir[0:3]!='C:\\':
            self.fexplorer.mkdir(self.fexplorer.current_parent+'\\'+subdir) 
        else:self.fexplorer.mkdir(subdir)
        
        
class Listener(Thread):
    def __init__(self, read_command_loc, OFFLINE, test=False):
        Thread.__init__(self)
        self.read_command_loc=read_command_loc
        self.controller=None
        self.queue=[]
        self.cmdfiles0=[]
        if not OFFLINE:
            self.cmdfiles0=os.listdir(self.read_command_loc)

    def run(self):
        while True:
            if not OFFLINE:
                connection=self.connection_checker.check_connection(False)
            time.sleep(INTERVAL)
            
    def listen(self):
        pass

    def set_controller(self,controller):
        self.controller=controller
        self.connection_checker.controller=controller

    
class PiListener(Listener):
    def __init__(self, read_command_loc,test=False):
       

        super().__init__(read_command_loc,PI_OFFLINE)
        self.connection_checker=PiConnectionChecker(read_command_loc,controller=self.controller, func=self.listen)
        
    def run(self):
        while True:
            if not PI_OFFLINE:
                connection=self.connection_checker.check_connection(False)
            time.sleep(INTERVAL)
            
    def listen(self):
        try:
            self.cmdfiles=os.listdir(self.read_command_loc) 
            if 'delme' in self.cmdfiles:
                cmdfiles.remove('delme')
            #print(self.cmdfiles)
            if self.controller.opsys=='Windows': #these lines at one point eliminated the lag that is otherwise present when running this software from windows computers. THen the lag came back. It happens because windows is reading from a cache, but I don't know how to force windows to clear the cache for the directory before looking again.
                with open(self.read_command_loc+'delme', 'w',0) as f:
                    f.write(self.cmdfiles) 
                #os.remove(self.read_command_loc+'delme')
                
        except:#Happens if there is a network disconnect that hasn't been registered yet.
            self.cmd_files=self.cmdfiles0
        if self.cmdfiles==self.cmdfiles0:
            pass
        else:
            for cmdfile in self.cmdfiles:
                try:
                    os.remove(self.read_command_loc+cmdfile)
                except:
                    #happens if the file is still in use, e.g. not done writing
                    if cmdfile!='delme':
                        print('failed to remove '+self.read_command_loc+cmdfile)
                  
                if cmdfile not in self.cmdfiles0 and cmdfile !='delme':
                    cmd, params=decrypt(cmdfile)

                    print('Pi read command: '+cmd)
                    if 'donemoving' in cmd:
                        self.queue.append('donemoving')
                    elif 'piconfigsuccess' in cmd:
                        self.queue.append('piconfigsuccess')
                    elif 'nopiconfig' in cmd:
                        self.queue.append('nopiconfig')
        self.cmdfiles0=list(self.cmdfiles)
                    

                        
                        
class SpecListener(Listener):
    def __init__(self, read_command_loc):
        super().__init__(read_command_loc,SPEC_OFFLINE)
        self.connection_checker=SpecConnectionChecker(read_command_loc,controller=self.controller, func=self.listen)
        self.unexpected_files=[]
        self.wait_for_unexpected_count=0

        self.alert_lostconnection=True
        self.new_dialogs=True
        
    def run(self):
        while True:
            if not SPEC_OFFLINE:
                connection=self.connection_checker.check_connection(False)
            time.sleep(INTERVAL)

            
    def listen(self):
        try:
            self.cmdfiles=os.listdir(self.read_command_loc)  
        except:
            print('Warning! Error finding files. Lost connection?')
            self.cmdfiles=self.cmdfiles0
        if self.cmdfiles==self.cmdfiles0:
            pass
        else:
            for cmdfile in self.cmdfiles:
                if cmdfile not in self.cmdfiles0:
                    cmd, params=decrypt(cmdfile)
                    if 'lostconnection' not in cmd:
                        print('Spec read command: '+cmd)
                    if 'savedfile' in cmd:
                        #self.saved_files.append(params[0])
                        self.queue.append('savedfile')
                    elif 'listdir' in cmd:
                        if 'listdirfailed' in cmd:
                            if 'permission' in cmd:
                                self.queue.append('listdirfailedpermission')
                            else:
                                self.queue.append('listdirfailed')
                        else:
                            #RemoteDirectoryWorker in wait_for_contents is waiting for a file that contains a list of the contents of a given folder on the spec compy. This file will have an encrypted version of the parent directory's path in its title e.g. listdir&R=+RiceData+Kathleen+spectral_data
                            print('read form quee')
                            print(cmdfile)
                            print('DONE')
                            self.queue.append(cmdfile)  

                    elif 'wrfailedfileexists' in cmd:
                        self.queue.append('wrfailedfileexists')
                    elif 'wrfailed' in cmd:
                        self.queue.append('wrfailed')
                        
                    elif 'failedtosavefile' in cmd:
                        self.queue.append('failedtosavefile')
                    elif 'processsuccessnocorrection' in cmd:
                        self.queue.append('processsuccessnocorrection')
                    elif 'processsuccessnolog' in cmd:

                        self.queue.append('processsuccessnolog')
                    elif 'processsuccess' in cmd:
                        print('processsuccess')
                        self.queue.append('processsuccess')
                        
                    elif 'processerrorfileexists' in cmd:
                        self.queue.append('processerrorfileexists')
                    
                    elif 'processerrorwropt' in cmd:
                        self.queue.append('processerrorwropt')
                    elif 'processerrornodirectory' in cmd:
                        self.queue.append('processerrornodirectory')
                    elif 'processerror' in cmd:
                        self.queue.append('processerror')
                    
                    elif 'wrsuccess' in cmd:
                        self.queue.append('wrsuccess')
                    
                    elif 'donelookingforunexpected' in cmd:
                        self.queue.append('donelookingforunexpected')
                    
                    elif 'saveconfigerror' in cmd:
                        self.queue.append('saveconfigerror')
                    
                    elif 'saveconfigsuccess' in cmd:
                        self.queue.append('saveconfigsuccess')
                    
                    elif 'noconfig' in cmd:
                        print("Spectrometer computer doesn't have a file configuration saved (python restart over there?). Setting to current configuration.")
                        self.queue.append('noconfig')
                    
                    elif 'nonumspectra' in cmd:
                        print("Spectrometer computer doesn't have an instrument configuration saved (python restart over there?). Setting to current configuration.")
                        self.queue.append('nonumspectra')
                    
                    elif 'saveconfigfailedfileexists' in cmd:
                        self.queue.append('saveconfigfailedfileexists')
                        
                    elif 'saveconfigfailed' in cmd:
                        self.queue.append('saveconfigfailed')
                        
                    elif 'savespecfailedfileexists' in cmd:
                        self.queue.append('savespecfailedfileexists')
                    
    
                    elif 'listcontents' in cmd:
                        self.queue.append(cmdfile)  
                    
                    elif 'mkdirsuccess' in cmd:
                        self.queue.append('mkdirsuccess')
                    
                    elif 'mkdirfailedfileexists' in cmd:
                        self.queue.append('mkdirfailedfileexists')
                    elif 'mkdirfailed' in cmd:
                        self.queue.append('mkdirfailed')
                    
                    elif 'iconfigsuccess' in cmd:
                        self.queue.append('iconfigsuccess')
                        
                    elif 'datacopied' in cmd:
                        self.queue.append('datacopied')
                        
                    elif 'datafailure' in cmd:
                        self.queue.append('datafailure')
                    
                    elif 'iconfigfailure' in cmd:
                        self.queue.append('iconfigfailure')
                        
                    elif 'optsuccess' in cmd:
                        self.queue.append('optsuccess')
                    
                    elif 'optfailure' in cmd:
                        self.queue.append('optfailure')
                        
                    elif 'notwriteable' in cmd:
                        self.queue.append('notwriteable')
                        
                    elif 'yeswriteable' in cmd:
                        self.queue.append('yeswriteable')
                        
                    elif 'lostconnection' in cmd:
                        try:
                            os.remove(self.read_command_loc+cmdfile)
                        except:
                            pass #This is probably because the lostconnection file was already removed by spec compy.

                        self.cmdfiles.remove(cmdfile)
                        if self.alert_lostconnection:
                            print('Spec read command: lostconnection')
                            self.alert_lostconnection=False

                            buttons={
                                'retry':{
                                    self.set_alert_lostconnection:[True]
                                    },
                                'work offline':{
                                },
                                'exit':{
                                    exit_func:[]
                                }
                            }
                            try:
                                dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: RS3 has no connection with the spectrometer.\nCheck that the spectrometer is on.\n\nNote that RS3 can take some time to connect to the spectrometer.\nBe patient and wait for the dot at the lower right of RS3 to turn green.',buttons=buttons,button_width=15, width=600)
                            except:
                                print('Ignoring an error in Listener when I make a new error dialog')
                    elif 'rmsuccess' in cmd:
                        self.queue.append('rmsuccess')
    
                    elif 'rmfailure' in cmd:
                        self.queue.append('rmfailure')
                        
                    elif 'unexpectedfile' in cmd:
                        if self.new_dialogs:
                            try:
                                dialog=ErrorDialog(self.controller, title='Untracked Files',label='There is an untracked file in the data directory.\nDoes this belong here?\n\n'+params[0])
                            except:
                                print('Ignoring an error in Listener when I make a new error dialog')
                        else:
                            self.unexpected_files.append(params[0])
                    else:
                        print('unexpected cmd: '+cmdfile)
            #This line always prints twice if it's uncommented, I'm not sure why.
            #print('forward!')

        self.cmdfiles0=list(self.cmdfiles)

    def set_alert_lostconnection(self,bool):
        self.alert_lostconnection=bool
        
      
def decrypt(encrypted):
    cmd=encrypted.split('&')[0]
    params=encrypted.split('&')[1:]
    i=0
    for param in params:
        params[i]=param.replace('+','\\').replace('=',':')
        params[i]=params[i].replace('++','+')
        i=i+1
    return cmd,params

    
def rm_reserved_chars(input):
    output= input.replace('&','').replace('+','').replace('=','').replace('$','').replace('^','').replace('*','').replace('(','').replace(',','').replace(')','').replace('@','').replace('!','').replace('#','').replace('{','').replace('}','').replace('[','').replace(']','').replace('|','').replace(',','').replace('?','').replace('~','').replace('"','').replace("'",'').replace(';','').replace('`','')
    return output
    
def numbers_only(input):
    output=''
    for digit in input:
        if digit=='1' or digit=='2' or digit=='3' or digit=='4'or digit=='5'or digit=='6' or digit=='7' or digit=='8' or digit=='9' or digit=='0':
            output+=digit
    return output
    
class Commander():
    def __init__(self, write_command_loc,listener):
        self.write_command_loc=write_command_loc
        self.listener=listener
        self.cmdnum=0
        
    def send(self,filename):
        try:
            file=open(self.write_command_loc+filename,'w')
        except OSError as e: #For some reason, I am only able to create files, not write content. And when I do create files, I get permission errors all the time. Probably not best, but it works...
            if e.errno==22 or e.errno==2:
                pass
            else:
                raise e
        except FileNotFoundError as e:
            pass
        except Exception as e:
            raise e
            
    def remove_from_listener_queue(self,commands):
        for command in commands:
            while command in self.listener.queue:
                self.listener.queue.remove(command)
            
    def encrypt(self,cmd,parameters=[]):
        filename=cmd+str(self.cmdnum)
        self.cmdnum+=1
        for param in parameters:
            param=str(param)
            param=param.replace('/','+')
            param=param.replace('\\','+')
            param=param.replace(':','=')
            filename=filename+'&'+param
        return filename
    
class PiCommander(Commander):
    def __init__(self,write_command_loc,listener):
        super().__init__(write_command_loc,listener)
    
    def configure(self,i,e,az,pos):

        self.remove_from_listener_queue(['piconfigsuccess'])
        filename=self.encrypt('configure',[i,e,az,pos])
        self.send(filename)
        return filename
        
    #We may specify either an incidence angle to move to, or a number of steps to move
    def set_incidence(self, num,type='angle'):
        self.remove_from_listener_queue(['donemoving','nopiconfig'])
        if type=='angle':
            incidence=num
            filename=self.encrypt('movelight',[incidence])
        else:
            steps=num
            filename=self.encrypt('movelight',[steps,'steps'])
        self.send(filename)
        return filename
    
    #We may specify either an azimuth angle to move to, or a number of steps to move
    def set_azimuth(self, num,type='angle'):
        self.remove_from_listener_queue(['donemoving','nopiconfig'])
        if type=='angle':
            azimuth=num
            filename=self.encrypt('movelight',[azimuth])
        else:
            steps=num
            filename=self.encrypt('movelight',[steps,'steps'])
        self.send(filename)
        return filename
    
    #We may specify either an emission angle to move to, or a number of steps to move
    def set_emission(self, num,type='angle'):
        self.remove_from_listener_queue(['donemoving','nopiconfig'])
        if type=='angle':
            emission=num
            filename=self.encrypt('movedetector',[emission])
        else:
            steps=num
            filename=self.encrypt('movedetector',[steps,'steps'])
        self.send(filename)
        return filename
    
    #pos can be either a sample position, or a number of motor steps.
    
    def move_tray(self, pos, type):
        self.remove_from_listener_queue(['donemoving'])
        if type=='position':
            positions={'wr':'wr','Sample 1':'one','Sample 2':'two','Sample 3':'three','Sample 4':'four','Sample 5':'five'}
            if pos in positions:
                filename=self.encrypt('movetray',[positions[pos]])
        else:
            filename=self.encrypt('movetray',[pos,'steps'])
        self.send(filename)
        
    

class SpecCommander(Commander):
    def __init__(self,write_command_loc,listener):
        super().__init__(write_command_loc,listener)
    
    def take_spectrum(self, path, basename, num, label, i, e):
        self.remove_from_listener_queue(['nonumspectra','noconfig','savedfile','failedtosavefile','savespecfailedfileexists'])

        if i==None:i=''
        if e==None:e=''
        filename=self.encrypt('spectrum',[path,basename,num, label, i, e])
        self.send(filename)
        return filename
        
    def white_reference(self):
        print('clear queue')
        self.remove_from_listener_queue(['nonumspectra','noconfig','wrsuccess','wrfailedfileexists','wrfailed'])
        filename=self.encrypt('wr')
        self.send(filename)
        return filename
        
    def optimize(self):
        self.remove_from_listener_queue(['nonumspectra','optsuccess','optfailure'])
        filename=self.encrypt('opt')
        self.send(filename)
        return filename
            
    def set_save_path(self, path, basename, startnum):
        self.remove_from_listener_queue(['saveconfigsuccess','donelookingforunexpected','saveconfigfailed','saveconfigfailedfileexists','saveconfigerror'])
        filename=self.encrypt('saveconfig',[path,basename,startnum])
        self.send(filename)
        return filename
        
    def configure_instrument(self,number):
        self.remove_from_listener_queue(['iconfigsuccess','iconfigfailure'])
        filename=self.encrypt('instrumentconfig',[number])
        self.send(filename)
        return filename
        
    def listdir(self,parent):
        self.remove_from_listener_queue(['listdirfailedpermission','listdirfailed'])
        filename=self.encrypt('listdir',parameters=[parent])
        self.send(filename)
        return filename

    def list_contents(self,parent):
        self.remove_from_listener_queue(['listdirfailedpermission','listfilesfailed','listdirfailed'])
        filename=self.encrypt('listcontents',parameters=[parent])
        self.send(filename)
        return filename
        
    def check_writeable(self,dir):
        self.remove_from_listener_queue(['yeswriteable','notwriteable'])
        filename=self.encrypt('checkwriteable',[dir])
        self.send(filename)
        return filename
    
    def mkdir(self,newdir):
        self.remove_from_listener_queue(['mkdirsuccess','mkdirfailedfileexists','mkdirfailed'])
        filename=self.encrypt('mkdir',[newdir])
        self.send(filename)
        return filename
        
    def delete_spec(self,savedir, basename, num):
        self.remove_from_listener_queue(['rmsuccess','rmfailure'])
        filename=self.encrypt('rmfile',[savedir,basename,num])
        self.send(filename)
        return filename
        
    def transfer_data(self,source, temp_destination_dir, temp_destination_file):
        self.remove_from_listener_queue(['datacopied','datafailure'])
        filename=self.encrypt('transferdata',parameters=[source,temp_destination_dir, temp_destination_file])
        self.send(filename)
        return filename
    
    # def send_data(self, source,destination)
    #     self.remove_from_listener_queue(['datareceived','datafailure'])
    #     filename=self.encrypt('getdata',parameters=[source,destination])
    #     self.send(filename)
    #     return filename
        
    def process(self,input_dir, output_dir, output_file):
        self.remove_from_listener_queue(['processsuccess','processerrorfileexists','processerrorwropt','processerror','processsuccess1unknownsample','processsuccessunknownsamples'])
        filename=self.encrypt('process',[input_dir,output_dir,output_file])
        self.send(filename)
        return filename
        
        
class ConnectionChecker():
    def __init__(self,dir,controller=None, func=None):
        self.dir=dir
        self.controller=controller
        self.func=func
        self.busy=False
    def alert_lost_connection(self, signum=None, frame=None):
        buttons={
            'retry':{
                self.release:[],
                self.check_connection:[False]
                },
            'work offline':{
                self.set_work_offline:[]
            },
            'exit':{
                exit_func:[]
            }
        }
        self.lost_dialog(buttons)


    def alert_not_connected(self, signum=None, frame=None):
        buttons={
            'retry':{
                self.release:[],
                self.check_connection:[True]
            },
            'work offline':{
                self.set_work_offline:[],
                self.func:[]
            },
            'exit':{
                exit_func:[]
            }
        }
        self.no_dialog(buttons)
        

    def have_internet(self):
        conn = httplib.HTTPConnection("www.google.com", timeout=5)
        try:
            conn.request("HEAD", "/")
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    
    def check_connection(self,firstconnection, attempt=0):
        if self.get_offline():
            self.func()
            return True
        if self.busy:
            return

            
        self.busy=True
        connected=True
        if self.have_internet()==False:
            connected=False
        else: 
            connected=os.path.isdir(self.dir)                
        if connected==False:
            #For some reason reconnecting only seems to work on the second attempt. This seems like a pretty poor way to handle that, but I just call check_connection twice if it fails the first time.
            if attempt>0 and firstconnection==True:
                self.alert_not_connected(None, None)
                return False
            elif attempt>0 and firstconnection==False:
                self.alert_lost_connection(None, None)
                return False
            else:
                time.sleep(0.5)
                self.release()
                self.check_connection(firstconnection, attempt=1)
        else:
            if self.func !=None:
                self.func()
            self.release()
            return True
    def release(self):
        self.busy=False

    def lost_dialog(self):
        pass
        
    def no_dialog(self):
        pass
        
    def get_offline(self):
        pass
        
    def set_work_offline(self):
        pass


        

        
class PretendEvent():
    def __init__(self, widget, width, height):
        self.widget=widget
        self.width=width
        self.height=height

class SpecConnectionChecker(ConnectionChecker):
    def __init__(self,dir,controller=None, func=None):
        super().__init__(dir,controller=controller, func=func)
        
    def set_work_offline(self):
        global SPEC_OFFLINE
        SPEC_OFFLINE=True
        
    def offline(self):
        return SPEC_OFFLINE
            
    def lost_dialog(self,buttons):
        try:
            dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: Lost connection with spec compy.\n\nCheck that you and the spectrometer computer are\nboth on the correct WiFi network and the\nSpecShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
    #Bring this up if there is no connection with the spectrometer computer
    def no_dialog(self,buttons):
        try:
            dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: No connection with Spec Compy.\n\nCheck that you and the spectrometer computer are\nboth on the correct WiFi network and the\nSpecShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
class PiConnectionChecker(ConnectionChecker):
    def __init__(self,dir,controller=None, func=None):
        super().__init__(dir,controller=controller, func=func)
        
    def set_work_offline(self):
        global PI_OFFLINE
        PI_OFFLINE=True
        
    def offline(self):
        return PI_OFFLINE
    def lost_dialog(self,buttons):
        try:
            dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: Lost connection with Raspberry Pi.\n\nCheck you and the Raspberry Pi are\nboth on the correct WiFi network and the\nPiShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
        
    def no_dialog(self,buttons):
        try:
            dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: Raspberry Pi not connected.\n\nCheck you and the Raspberry Pi are\nboth on the correct WiFi network and the\nPiShare folder is mounted on your computer',buttons=buttons,button_width=15)
        except:
            pass
            
class PrivateEntry():
    def __init__(self, text):
        self.text=text
    def get(self):
        return self.text
        
class SampleFrame():
    def __init__(self,controller):
        self.position='Sample 1'


from tkinter import *   # from x import * is bad practice
from tkinter import ttk

# http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame

class VerticalScrolledFrame(Frame):

    #Use the 'interior' attribute to place widgets inside the scrollable frame
    #Construct and pack/place/grid normally
    #This frame only allows vertical scrolling

    def __init__(self, controller, parent, min_height=600, width=468,*args, **kw):
        self.controller=controller
        Frame.__init__(self, parent, *args, **kw)        
        
        self.min_height=min_height #Miniumum height for interior frame to show all elements. Changes as new samples or viewing geometries are added.    

        # create a canvas object and a vertical scrollbar for scrolling it
        self.scrollbar = Scrollbar(self, orient=VERTICAL)
        
        self.canvas=canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=self.scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        canvas.config(width=width)
        #canvas.config(height=height)        
        self.scrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        # initialize height to the bigger of 1) screen height 2) 700 px

        self.interior = interior = Frame(canvas)
        interior.pack_propagate(0) #This makes it so we can easily manually set the interior frame's size as needed. See _configure_canvas() for how it's done.
        self.interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)
        self.canvas.bind('<Configure>', self._configure_canvas)


    def _configure_canvas(self,event):
        if self.canvas.winfo_height()>self.min_height:
            self.interior.config(height=self.canvas.winfo_height())
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.pack_forget()
        else:
            self.interior.config(height=self.min_height)
            self.scrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
            #canvas.itemconfigure(interior_id, height=900)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())
    
    def update(self, controller_resize=True):
        self._configure_canvas(None)
        if controller_resize:
            self.controller.resize()
        
class StringVarWithEntry(StringVar):
    def __init__(self):
        super().__init__()
        self.entry=None

if __name__=='__main__':
    main()