
#I don't want pygame to print a welcome message when it loads.
# import contextlib
# with contextlib.redirect_stdout(None):
#     import pygame
import pathlib, pygame
print(pathlib.Path(pygame.__file__).resolve().parent)
import threading
from threading import Lock
import time
import numpy as np
from tkinter import *
import os
import tkinter as tk
import math

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
#        Needed for pygame 1.9.6, breaks 2.0.0.dev8
#         if self.controller.opsys=='Windows':
#             os.environ['SDL_VIDEODRIVER'] = 'windib'
        self.screen = pygame.display.set_mode((self.width,self.height))
        
        self.light=pygame.Rect(30,30,60,60)
        self.theta_l=-30
        self.theta_d=0
        self.d_up=False
        self.l_up=False
        self.current_sample=''
        
        self.wireframes = {}
        self.displayNodes = True
        self.displayEdges = True
        self.nodeColour = (255,255,255)
        self.edgeColour = (200,200,200)
        self.nodeRadius = 4
        self.define_wireframes()
        pygame.init()

        
    def tab_switch(self,event):
        self.master.update()
        os.environ['SDL_WINDOWID'] = str(self.double_embed.winfo_id())
#        Needed for pygame 1.9.6, breaks 2.0.0.dev8
#         if self.controller.opsys=='Windows':
#             os.environ['SDL_VIDEODRIVER'] = 'windib'
        self.flip()
        
    def flip(self,event=None):
        pygame.display.update()
        pygame.display.flip()
        
    def define_wireframes(self):
        i_wireframe = Wireframe()
        e_wireframe=Wireframe()
        
        i_nodes=[]
        e_nodes=[]
        
        for angle in np.arange(0,math.pi,0.1):
            x=math.cos(angle)
            y=-math.sin(angle)
            i_nodes.append((x,y,0))
            if angle<math.pi/2:
                e_nodes.append((x,y,0))
                
        x=math.cos(math.pi)
        y=-math.sin(math.pi)
        i_nodes.append((x,y,0))
        i_wireframe.add_nodes(i_nodes)
        
        x=math.cos(math.pi/2)
        y=-math.sin(math.pi/2)
        e_nodes.append((x,y,0))
        e_wireframe.add_nodes(e_nodes)
        
        i_edges=[]
        e_edges=[]
        
        for n in range(len(i_nodes)):
            if n<len(i_nodes)-1:
                i_edges.append((n, n+1))
            if n<len(e_nodes)-1:
                e_edges.append((n,n+1))
                
        i_wireframe.add_edges(i_edges)
        e_wireframe.add_edges(e_edges)
        
        i_wireframe.az=90
        e_wireframe.az=90
        

        #i_wireframe.set_elevation(0)
        e_wireframe.set_azimuth(0)
        
        self.wireframes['i']=i_wireframe
        self.wireframes['e']=e_wireframe
        
    def draw_3D_goniometer(self, width, height):
        self.width=width
        self.height=height
        self.char_len=self.height #characteristic length we use to scale drawings
        scale=1.12
        if self.width-120<self.height:
            self.char_len=self.width-120
            
        pivot = (int(self.width/2),int(0.8*self.height),0)
        light_len = int(5*self.char_len/8)
        
        i_radius=int(self.char_len/3)#250
        e_radius=int(i_radius*0.75)
        
        self.wireframes['i'].set_scale(i_radius)
        self.wireframes['e'].set_scale(e_radius)


        self.screen.fill(pygame.Color(self.controller.bg))
        
        
        for wireframe in self.wireframes.values():
            wireframe.move_to(pivot)
            if self.displayEdges:
                for edge in wireframe.edges:
                    pygame.draw.aaline(self.screen, self.edgeColour, (edge.start.x, edge.start.y), (edge.stop.x, edge.stop.y), 1)
            if self.displayNodes:
                for node in wireframe.nodes:
                    pygame.draw.circle(self.screen, self.nodeColour, (int(node.x), int(node.y)), self.nodeRadius, 0)
        
    #draws the side view of the goniometer
    def draw_side_view(self,width,height):
        self.draw_3D_goniometer(width, height)
        return 
    
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
        #pygame.draw.circle(self.screen, pygame.Color('darkgray'), pivot, back_radius+border_thickness, 3)
        pygame.draw.arc(self.screen, pygame.Color('darkgray'), [pivot[0]-back_radius, pivot[1]-back_radius, 2*back_radius, 2*back_radius], 0,3.14159, 3)
        #pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
        pygame.draw.rect(self.screen, pygame.Color(self.controller.bg),(pivot[0]-back_radius,pivot[1]+int(self.char_len/10-5),2*back_radius,2*back_radius))
        #pygame.draw.rect(self.screen, (0,0,0),(pivot[0]-back_radius,pivot[1],2*back_radius,int(self.char_len/6.5)))
        
        #draw border around bottom part of goniometer
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius-1,pivot[1]),(pivot[0]-back_radius-1,pivot[1]+int(self.char_len/6.5)), 3)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+back_radius,pivot[1]),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)), 3)
        pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius,pivot[1]+int(self.char_len/6.5)),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)), 3)

        
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
            self.draw_side_view(self.width,self.height)
            self.flip()
            
    def set_current_sample(self, sample):
            self.current_sample=sample
            self.draw_side_view(self.width,self.height)
            self.flip()
            
    def move_detector(self, theta,config=False):
        while np.abs(theta-self.theta_d)>0:
            self.theta_d=self.theta_d+0.5*np.sign(theta-self.theta_d)
            if not config:
                time.sleep(0.16)
            else:
                time.sleep(.005)
            self.draw_side_view(self.width,self.height)
            self.flip()
                
    def quit(self):
        pygame.display.quit()
        pygame.quit()
       
#see reference: http://www.petercollingridge.co.uk/tutorials/3d/pygame/nodes-and-edges/ 
class Node:
    def __init__(self, coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.z = coordinates[2]
        
class Edge:
    def __init__(self, start, stop):
        self.start = start
        self.stop  = stop
        
class Wireframe:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.center=(0,0,0)
        self.scale=1
        self.az=0
        self.el=0
        
    def set_center(self, center):
        self.center=center
        
    def add_nodes(self, nodeList):
        for node in nodeList:
            self.nodes.append(Node(node))
            
    def add_edges(self, edgeList):
        for (start, stop) in edgeList:
            self.edges.append(Edge(self.nodes[start], self.nodes[stop]))

    def output_nodes(self):
        print("\n --- Nodes --- ")
        for i, node in enumerate(self.nodes):
            print(" %d: (%.2f, %.2f, %.2f)" % (i, node.x, node.y, node.z))
                
    def output_edges(self):
        print("\n --- Edges --- ")
        for i, edge in enumerate(self.edges):
            print(" %d: (%.2f, %.2f, %.2f)" % (i, edge.start.x, edge.start.y, edge.start.z))
            print("to (%.2f, %.2f, %.2f)" % (edge.stop.x,  edge.stop.y,  edge.stop.z))
            
    def scale(self, scale):
        #Scale the wireframe from the centre of the screen.
        for node in self.nodes:
            node.x = self.center[0] + scale * (node.x - self.center[0])
            node.y = self.center[1] + scale * (node.y - self.center[1])
            node.z *= scale
            
    def translate(self, axis, d):
    #Translate each node of a wireframe by d along a given axis.
        if axis in ['x', 'y', 'z']:
            for node in self.nodes:
                setattr(node, axis, getattr(node, axis) + d)
                
    def move_to(self, center):
        diff={}
        diff['x']=center[0]-self.center[0]
        diff['y']=center[1]-self.center[1]
        diff['z']=center[2]-self.center[2]
        for node in self.nodes:
            for axis in ['x', 'y', 'z']:
                setattr(node, axis, getattr(node, axis) + diff[axis])
        self.center=center
        
    def set_scale(self, scale):
        diff=scale/self.scale
        for node in self.nodes:
            node.x = self.center[0] + diff*(node.x - self.center[0])
            node.y = self.center[1] + diff*(node.y - self.center[1])
            node.z = self.center[2] + diff*(node.z - self.center[2])
        self.scale=scale
        
    def rotate_az(self, degrees):
        radians=degrees/180*math.pi
        for node in self.nodes:
            x      = node.x - self.center[0]
            z      = node.z - self.center[2]
            d      = math.hypot(x, z)
            theta  = math.atan2(x, z) + radians
            node.z = self.center[2] + d * math.cos(theta)
            node.x = self.center[0] + d * math.sin(theta)
            
    def rotate_el(self, degrees):
        radians=degrees/180*math.pi
        for node in self.nodes:
            y      = node.y - self.center[1]
            z      = node.z - self.center[2]
            d      = math.hypot(y, z)
            theta  = math.atan2(y, z) + radians
            node.z = self.center[2] + d * math.cos(theta)
            node.y = self.center[1] + d * math.sin(theta)
    
    def set_azimuth(self, az):
        diff=az-self.az
        self.rotate_az(diff)
        self.az=az
        
    def set_elevation(self, el):
        print('set elevation to')
        print(el)
        az=self.az
        self.set_azimuth(90)
        diff=el-self.el
        self.rotate_el(diff)
        self.el=el
        self.set_azimuth(az)
        
        
