from tkinter import *

class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, controller, parent, *args, **kw):
        self.controller=controller
        Frame.__init__(self, parent, *args, **kw)        
        
        self.min_height=600 #Miniumum height for interior frame to show all elements. Changes as new samples or viewing geometries are added.    

        # create a canvas object and a vertical scrollbar for scrolling it
        self.scrollbar = Scrollbar(self, orient=VERTICAL)
        
        self.canvas=canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=self.scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        canvas.config(width=100) #I have this set so the actual width is always greater than this. There is an issue where the scrollbar will disappear with horizontal resize otherwise.
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

        if self.canvas.winfo_height()>=self.min_height:
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
    
    def update(self):
        self._configure_canvas(None)
        self.controller.resize()