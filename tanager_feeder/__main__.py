#The controller runs the main thread controlling the program.
#It opens a Tkinter GUI with options for instrument control parameters and sample configuration
#The user can use the GUI to operate the goniometer motors and the spectrometer software.

import os
import platform
    

import time
from threading import Thread
from tkinter.filedialog import *
from tkinter import *   # from x import * is bad practice

import shutil
import playsound

from tanager_tcp import TanagerClient
from tanager_tcp import TanagerServer
from tanager_feeder.controller import Controller


#Figure out where this file is hanging out and tell python to look there for custom modules. This will depend on what operating system you are using.
opsys=platform.system()
if opsys=='Darwin': opsys='Mac' #For some reason Macs identify themselves as Darwin. I don't know why but I think this is more intuitive.

if opsys=='Windows':
    #Note that if running this script from an IDE, __file__ may not be defined.
    rel_package_loc='\\'.join(__file__.split('\\')[:-1])+'\\'
    if 'c:' in rel_package_loc.lower():
        package_loc=rel_package_loc
    else:
        package_loc=os.getcwd()+'\\'+rel_package_loc

elif opsys=='Linux':
    rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
    if rel_package_loc[0]=='/':
        package_loc=rel_package_loc
    else:
        package_loc=os.getcwd()+'/'+rel_package_loc

elif opsys=='Mac':
    rel_package_loc='/'.join(__file__.split('/')[:-1])+'/'
    if rel_package_loc[0]=='/':
        package_loc=rel_package_loc
    else:
        package_loc=os.getcwd()+'/'+rel_package_loc

sys.path.append(package_loc)


computer = 'new'
#Server and share location. Can change if spectroscopy computer changes.
server=''
global NUMLEN #number of digits in the raw data filename. Could change from one version of software to next.

NUMLEN=500
if computer=='old':
    #Number of digits in spectrum number for spec save config
    NUMLEN=3
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    PI_BUFFER=20

elif computer=='desktop':
    #Number of digits in spectrum number for spec save config
    NUMLEN=5
    #Time added to timeouts to account for time to read/write files
    server='melissa' #old computer
elif computer=='new':
    #Number of digits in spectrum number for spec save config
    NUMLEN=5
    #Time added to timeouts to account for time to read/write files
    BUFFER=15
    PI_BUFFER=20
    server='geol-chzc5q2' #new computer
    BUFFER=15
    PI_BUFFER=20
    server='marsinsight' #new computer

pi_server='raspberrypi'
home_loc=os.path.expanduser('~')

if opsys=='Linux':
    import ctypes
    x11 = ctypes.cdll.LoadLibrary('libX11.so')
    x11.XInitThreads()
    
    home_loc+='/'
    delimiter='/'
    local_config_loc=home_loc+'.tanager_config/' #package_loc+'local_config/'
    global_config_loc=package_loc+'global_config/'
    log_loc=package_loc+'log/'
    
elif opsys=='Windows':
    home_loc+='\\'
    local_config_loc=home_loc+'.tanager_config\\' #package_loc+'local_config\\'
    global_config_loc=package_loc+'global_config\\'
    log_loc=package_loc+'log\\'
    
elif opsys=='Mac':
    home_loc+='/'
    delimiter='/'
    local_config_loc=home_loc+'.tanager_config/' #package_loc+'local_config/'
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
    try:
        with open(local_config_loc+'ip_addresses.txt','r') as ip_config:
            spec_ip=ip_config.readline().strip('\n')
            pi_ip=ip_config.readline().strip('\n')
        connection_tracker = tanager_feeder.utils.ConnectionTracker(spec_ip, pi_ip)
    except:
        print('Failed to load ip config.')
        connection_tracker = tanager_feeder.utils.ConnectionTracker()



    icon_loc=package_loc+'exception'#eventually someone should make this icon thing work. I haven't!
    config_info = tanager_feeder.utils.ConfigInfo(local_config_loc, global_config_loc, icon_loc, opsys)
    
    #Check if you are connected to the server. If not, put up dialog box and wait. If you are connected, go on to main part 2.
    spec_connection_checker=SpecConnectionChecker(connection_tracker, config_info, func=main_part_2, args = [connection_tracker, config_info])
    print('Checking spectrometer computer connection...')
    connected = spec_connection_checker.check_connection(listening_port=tanager_feeder.utils.SPEC_PORT)
    if not connected:
        connection_tracker.spec_offline = True
        print('Not connected')

 
#repeat check for raspi
def main_part_2(connection_tracker, config_info):
    print("SPEC Off? "+str(connection_tracker.spec_offline))
    pi_connection_checker=PiConnectionChecker(connection_tracker, config_info, func=main_part_3, args = [connection_tracker, config_info])
    print('Checking raspberry pi connection...')
    connected=pi_connection_checker.check_connection()
    if not connected:
        connection_tracker.pi_offline = True
        print('Not connected')

def main_part_3():
    print("pi Off? "+str(connection_tracker.pi_offline))

    #Create a listener, which listens for commands, and a controller, which manages the model (which writes commands) and the view.
    spec_listener=SpecListener(connection_tracker)
    pi_listener=PiListener(connection_tracker)


    control=Controller(spec_listener, pi_listener, connection_tracker, config_info)

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


class ConnectionChecker():
    def __init__(self, which_compy, config_loc, controller=None, func=None, args=[]):
        self.which_compy=which_compy
        self.config_loc=config_loc
        self.controller=controller
        self.func=func
        self.busy=False
        self.args = args
        
    def alert_lost_connection(self):
        buttons={
            'retry':{
                self.release:[],
                self.check_connection:[6]
                },
            'work offline':{
                self.set_work_offline:[]
            },

            'exit':{
                exit_func:[]
            }
        }
        self.lost_dialog(buttons)
    
    def change_ip(self):
        pass

    def alert_not_connected(self):
        buttons={
            'retry':{
                self.release:[],
                self.check_connection:[6],
            },
            'work offline':{
                self.set_work_offline:[],
                self.func:self.args
            },
            'Change IP':{
                self.ask_ip:[]
            }
        }
        self.no_dialog(buttons)
    
    def check_connection(self, listening_port, timeout=3):
        if self.which_compy=='spec compy':
            server_ip = self.connection_tracker.spec_ip
            listening_port = self.connection_tracker.SPEC_PORT
        else:
            server_ip = self.connection_tracker.pi_ip
            listening_port = self.connection_tracker.PI_PORT
        connected = False

        try:
            client=TanagerClient((server_ip,12345),'test', listening_port, timeout=timeout)
            if self.which_compy=='spec compy':
                self.connection_tracker.spec_offline = False
            else:
                self.connection_tracker.pi_offline = False
            self.func(*self.args)
            connected = True
        except Exception as e:
            print(e)
            self.alert_not_connected()

        if connected:
            self.func(*self.args)

        return connected
        
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
    def __init__(self, config_loc, controller=None, func=None):
        super().__init__('spec compy', config_loc, controller=controller, func=func)
        
    def set_work_offline(self):
        global SPEC_OFFLINE
        SPEC_OFFLINE=True
        
    def offline(self):
        return SPEC_OFFLINE
            
    def lost_dialog(self, buttons):
        try:
            dialog=ErrorDialog(controller=self.controller, title='Lost Connection',label='Error: Lost connection with spec compy.\n\nCheck that you and the spectrometer computer are\nboth connected to the same network.',buttons=buttons,button_width=15)
        except:
            pass

    #Bring this up if there is no connection with the spectrometer computer
    def no_dialog(self, buttons):
        try:
            dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: No connection with Spec Compy.\n\nCheck that you and the spectrometer computer are\nboth connected to the same network.',buttons=buttons,button_width=15)
        except Exception as e:
            print(e)
            raise(e)
            pass
    
    def ask_ip(self):  
        try:
            dialog=ChangeIPDialog(controller=self.controller, title='Change IP',label='Enter the IP address for the spectrometer computer.\n\nThe IP address is displayed in the ASD feeder terminal at startup.', which_compy='spec compy', config_loc=self.config_loc)
        except:
            pass  

class PiConnectionChecker(ConnectionChecker):
    def __init__(self, config_loc, controller=None, func=None):
        super().__init__('pi', config_loc, controller=controller, func=func)
        
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
            dialog=Dialog(controller=self.controller, title='Not Connected',label='Error: Raspberry Pi not connected.\n\nCheck you and the Raspberry Pi are\nboth connected to the same network.',buttons=buttons,button_width=15)
        except:
            pass
        
    def ask_ip(self):  
        try:
            dialog=ChangeIPDialog(controller=self.controller, title='Change IP',label='Enter the IP address for the raspberry pi.\n\n.', which_compy='pi', config_loc=self.config_loc)
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
        self.width=width

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
            if self.canvas.winfo_height()<self.min_height:
                self.canvas.config(width=self.width-20)
#                 self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width()-20)
            else:
#                 self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())
                self.canvas.config(width=self.width)

            
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