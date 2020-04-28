
#I don't want pygame to print a welcome message when it loads.
import contextlib
with contextlib.redirect_stdout(None):
    import pygame

import threading
from threading import Lock
import time
import numpy as np
from tkinter import *
import os
import tkinter as tk

#Animated graphic of goniometer
class GoniometerView():
    def __init__(self,controller,notebook):
        self.width=1800
        self.height=1200
        self.controller=controller
        self.master=self.controller.master
        self.notebook=notebook
        
        self.embed=Frame(self.notebook,width=self.width,height=self.height)
        self.embed.pack(fill=BOTH,expand=True)
        
        self.double_embed=Frame(self.embed,width=self.width,height=self.height)
        self.double_embed.pack(fill=BOTH,expand=True)
        
        
        self.notebook.add(self.embed,text='Goniometer view')
        
        self.master.update()
        
        os.environ['SDL_WINDOWID'] = str(self.double_embed.winfo_id())
        if self.controller.opsys=='Windows':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        self.screen = pygame.display.set_mode((self.width,self.height))
        
        self.light=pygame.Rect(30,30,60,60)
        self.theta_l=-30
        self.theta_d=0
        self.d_up=False
        self.l_up=False
        self.current_sample=''
        
        pygame.init()

        
    def tab_switch(self,event):
        
        self.master.update()
        os.environ['SDL_WINDOWID'] = str(self.double_embed.winfo_id())
        if self.controller.opsys=='Windows':
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        self.flip()
        
    def flip(self,event=None):

        pygame.display.update()
        pygame.display.flip()
        

        
    #draws everything not just one circle
    def draw_circle(self,width,height):
        self.width=width
        self.height=height
        self.char_len=self.height
        scale=1.12
        if self.width-120<self.height:
            self.char_len=self.width-120
        try:
            i_str='i='+str(int(self.theta_l))
            e_str='e='+str(int(self.theta_d))
            sample_str=self.current_sample

            
            text_size=np.max([int(self.char_len/18),20])
            largeText = pygame.font.Font('freesansbold.ttf',text_size)
            sample_font=pygame.font.Font('freesansbold.ttf',int(0.75*text_size))
            i_text=largeText.render(i_str, True, pygame.Color(self.controller.textcolor))
            e_text=largeText.render(e_str, True, pygame.Color(self.controller.textcolor))
            sample_text=sample_font.render(sample_str, True, pygame.Color(self.controller.textcolor))
        except:
            print('no pygame font')
        
        #pivot point of goniometer arms. Used as reference for drawing everyting else
        pivot = (int(self.width/2),int(0.8*self.height))
        light_len = int(5*self.char_len/8)#300
        light_width=24  #needs to be an even number
        
        back_radius=int(self.char_len/2)#250
        border_thickness=1
        
        x_l = pivot[0] + np.sin(np.radians(self.theta_l)) * light_len
        x_l_text=pivot[0] + np.sin(np.radians(self.theta_l)) * (light_len/scale)
        y_l = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len
        y_l_text = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len*scale-abs(np.sin(np.radians(self.theta_l))*light_len/12)
        
        detector_len=light_len
        detector_width=light_width
        x_d = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len
        x_d_text = pivot[0] + np.sin(np.radians(self.theta_d)) * (detector_len/scale)
        y_d = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len
        y_d_text = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len*scale-abs(np.sin(np.radians(self.theta_d))*detector_len/12)
        if np.abs(y_d_text-y_l_text)<self.char_len/30 and np.abs(x_d_text-x_l_text)<self.char_len/15:
            if self.d_up:
                y_d_text-=self.char_len/20
            elif self.l_up:
                y_l_text-=self.char_len/20
            elif y_d_text<y_l_text:
                y_d_text-=self.char_len/20
                self.d_up=True
            else:
                self.l_up=True
                y_l_text-=self.char_len/20
        else:
            self.d_up=False
            self.l_up=False
        
        #deltas to give arm width.
        delta_y_l=light_width/2*np.sin(np.radians(self.theta_l))
        delta_x_l=light_width/2*np.cos(np.radians(self.theta_l))
        
        delta_y_d=detector_width/2*np.sin(np.radians(self.theta_d))
        delta_x_d=detector_width/2*np.cos(np.radians(self.theta_d))
        
        self.screen.fill(pygame.Color(self.controller.bg))
        
        #Draw goniometer
        pygame.draw.circle(self.screen, pygame.Color('darkgray'), pivot, back_radius+border_thickness)
        pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
        pygame.draw.rect(self.screen, pygame.Color(self.controller.bg),(pivot[0]-back_radius,pivot[1]+int(self.char_len/10-5),2*back_radius,2*back_radius))
        pygame.draw.rect(self.screen, (0,0,0),(pivot[0]-back_radius,pivot[1],2*back_radius,int(self.char_len/6.5)))
        
        #draw border around bottom part of goniometer
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius-1,pivot[1]),(pivot[0]-back_radius-1,pivot[1]+int(self.char_len/6.5)))
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+back_radius,pivot[1]),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)))
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius,pivot[1]+int(self.char_len/6.5)),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)))

        
        #draw light arm
        points=((pivot[0]-delta_x_l,pivot[1]-delta_y_l),(x_l-delta_x_l,y_l-delta_y_l),(x_l+delta_x_l,y_l+delta_y_l),(pivot[0]+delta_x_l,pivot[1]+delta_y_l))
        pygame.draw.polygon(self.screen, pygame.Color('black'), points)
        pygame.draw.polygon(self.screen, pygame.Color('darkgray'), points, border_thickness)
        
        #draw detector arm
        points=((pivot[0]-delta_x_d,pivot[1]-delta_y_d),(x_d-delta_x_d,y_d-delta_y_d),(x_d+delta_x_d,y_d+delta_y_d),(pivot[0]+delta_x_d,pivot[1]+delta_y_d))
        pygame.draw.polygon(self.screen, pygame.Color('black'), points)
        pygame.draw.polygon(self.screen, pygame.Color('darkgray'), points, border_thickness)

        
        
        self.screen.blit(i_text,(x_l_text,y_l_text))
        self.screen.blit(e_text,(x_d_text,y_d_text))
        if self.current_sample=='WR':
            self.screen.blit(sample_text,(pivot[0]-text_size, pivot[1]+text_size))
        else:
            self.screen.blit(sample_text,(pivot[0]-int(1.5*text_size), pivot[1]+text_size))
        
        #border around screen
        pygame.draw.rect(self.screen,pygame.Color('darkgray'),(2,2,self.width-6,self.height+15),2)

        
    def move_light(self, theta, config=False):
        while np.abs(theta-self.theta_l)>0:
            self.theta_l=self.theta_l+0.5*np.sign(theta-self.theta_l)
            if not config:
                time.sleep(0.16)
            else:
                time.sleep(.005)
            self.draw_circle(self.width,self.height)
            self.flip()
            
    def set_current_sample(self, sample):
            self.current_sample=sample
            self.draw_circle(self.width,self.height)
            self.flip()
            
    def move_detector(self, theta,config=False):
        while np.abs(theta-self.theta_d)>0:
            self.theta_d=self.theta_d+0.5*np.sign(theta-self.theta_d)
            if not config:
                time.sleep(0.16)
            else:
                time.sleep(.005)
            self.draw_circle(self.width,self.height)
            self.flip()
                
    def quit(self):
        pygame.display.quit()
        pygame.quit()
        
        

