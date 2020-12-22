import time
from tanager_feeder.dialogs.wait_dialog import WaitDialog

class CommandHandler:
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
        try:
            self.wait_dialog.ok_button.focus_set()
        except:
            self.wait_dialog.top.focus_set()

        if self.controller.audio_signals:
            if 'Success' in label:
                playsound.playsound('beep.wav')
            else:
                playsound.playsound('broken.wav')

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
