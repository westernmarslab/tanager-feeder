
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
        self.display_nodes = False
        self.display_edges = False
        self.display_faces=True
        self.nodeColour = (255,255,255)
        self.edge_color = (200,200,200)
        self.nodeRadius = 4
        self.define_goniometer_wireframes()
        self.define_sample_tray_wireframes()
        self.tilt=0 #tilt of entire goniometer
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
        
    def define_sample_tray_wireframes(self):
        tray_wireframe=Wireframe()
        spectralon_wireframe=Wireframe()
        
        tray_nodes=[]
        spectralon_nodes=[]
        for angle in np.arange(0,math.pi*2,math.pi/8):
            x=math.cos(angle)
            y1=0.03
            y2=0.1
            y3=0
            z=math.sin(angle)
            tray_nodes.append((-0.5+x,y1,z))
            tray_nodes.append((-0.5+x,y2,z))
            spectralon_nodes.append((0.25*x, y3, 0.25*z))
            spectralon_nodes.append((.25*x, y1, 0.25*z))
            
        tray_wireframe.add_nodes(tray_nodes)
        spectralon_wireframe.add_nodes(spectralon_nodes)
        
#         tray_faces=[(0,),(1,)]
#         spectralon_faces=[(0,),(1,)]
        tray_faces=[]
        spectralon_faces=[]

        for n in range(len(spectralon_nodes)):
            if n<len(spectralon_nodes)-3:
                if n%2==0:
                    spectralon_faces.append((n,n+1, n+3, n+2))
                    tray_faces.append((n,n+1, n+3, n+2))
#             if n==0 or n==1: 
#                 continue
#             elif n%2==0 and n<len(spectralon_nodes)-1:
#                 spectralon_faces[0]+=(n,)
#                 spectralon_faces.append((n,n+1))
#                 tray_faces[0]+=(n,)
#             else:
#                 spectralon_faces[1]+=(n,)
#                 tray_faces[1]+=(n,)
        for n in range(len(tray_nodes)):
            if n==0:
                tray_faces.append((0,))
                spectralon_faces.append((0,))
            elif n%2==0:
                tray_faces[-1]+=(n,)
                spectralon_faces[-1]+=(n,)
        print(tray_faces[-1])
        #tray_faces.append((0,2,4,6,8,10,12,14,16,18))
        tray_wireframe.add_faces(tray_faces)
        spectralon_wireframe.add_faces(spectralon_faces, color=(200,200,200))
        
        self.wireframes['tray']=tray_wireframe
        self.wireframes['spectralon']=spectralon_wireframe
        
        
    def define_goniometer_wireframes(self):
        i_wireframe = Wireframe()
        e_wireframe=Wireframe()
        
        i_nodes=[]
        e_nodes=[]
        
#         i_nodes.append((1,0.1, -0.1))
#         i_nodes.append((1,0.1, 0.1))
        for angle in np.arange(0,math.pi,math.pi/30):
            x=math.cos(angle)
            y=-math.sin(angle)
            i_nodes.append((x,y,-0.1))
            i_nodes.append((x,y,0.1))
            i_nodes.append((x*0.95, y*0.95, -0.1))
            i_nodes.append((x*0.95, y*0.95, 0.1))
            
            if angle<=math.pi/2:
                e_nodes.append((x,y,-0.1))
                e_nodes.append((x,y,0.1))
                e_nodes.append((x*0.95, y*0.95, -0.1))
                e_nodes.append((x*0.95, y*0.95, 0.1))
                
        x=math.cos(math.pi)
        y=-math.sin(math.pi)
        i_nodes.append((x,y,-0.1))
        i_nodes.append((x,y,0.1))
        i_nodes.append((x*0.95, y*0.95, -0.1))
        i_nodes.append((x*0.95, y*0.95, 0.1))
        
        
        i_wireframe.add_nodes(i_nodes)
        
        x=math.cos(math.pi/2)
        y=-math.sin(math.pi/2)
        e_nodes.append((x-0.05,y,-0.1))
        e_nodes.append((x-0.05,y,0.1))
        e_nodes.append((x*0.95-.05, y*0.95, -0.1))
        e_nodes.append((x*0.95-.05, y*0.95, 0.1))
        

        e_wireframe.add_nodes(e_nodes)
        
        i_edges=[]
        e_edges=[]

        for n in range(len(i_nodes)-4):
            i_edges.append((n, n+4))
            if n<len(e_nodes)-4:
                e_edges.append((n, n+4))
                
        i_wireframe.add_edges(i_edges)
        e_wireframe.add_edges(e_edges)
        
        i_faces=[]
        e_faces=[]
        for n in range(len(i_nodes)-7):
            if n%4==0:
                i_faces.append((n, n+2, n+6, n+4))
                i_faces.append((n, n+1, n+5, n+4))
                i_faces.append((n+2, n+6, n+7, n+3))
                i_faces.append((n+1, n+3, n+7, n+5))
                if n<len(e_nodes)-7:
                    e_faces.append((n, n+2, n+6, n+4))
                    e_faces.append((n, n+1, n+5, n+4))
                    e_faces.append((n+2, n+6, n+7, n+3))
                    e_faces.append((n+1, n+3, n+7, n+5))
        
        i_wireframe.add_faces(i_faces)
        e_wireframe.add_faces(e_faces)

        self.wireframes['e']=e_wireframe
        self.wireframes['i']=i_wireframe
        
        i_base_wireframe=Wireframe()
        e_base_wireframe=Wireframe()
        
        i_base_nodes=[]
        e_base_nodes=[]
        
        for angle in np.arange(0,math.pi*2,math.pi/30):
            x1=math.cos(angle)*1.01
            x2=math.cos(angle)*0.99
            y=0
            z1=math.sin(angle)*1.01
            z2=math.sin(angle)*0.99
            i_base_nodes.append((x1,y,z1))
            i_base_nodes.append((x2,y,z2))
            e_base_nodes.append((x1,y,z1))
            e_base_nodes.append((x2,y,z2))
            
        i_base_wireframe.add_nodes(i_base_nodes)
        e_base_wireframe.add_nodes(e_base_nodes)
        
        i_base_edges=[]
        e_base_edges=[]
        
        for n in range(len(i_base_nodes)-2):
            i_base_edges.append((n, n+2))
            e_base_edges.append((n, n+2))
        i_base_edges.append((-2,0))
        e_base_edges.append((-2,0))
        i_base_edges.append((-1,1))
        e_base_edges.append((-1,1))
        
        #i_base_wireframe.add_edges(i_base_edges)
        #e_base_wireframe.add_edges(e_base_edges)
        
        e_base_faces=[]
        i_base_faces=[]
        for n in range(len(e_base_nodes)-3):
            if n%2==0:
                i_base_faces.append((n, n+1, n+3, n+2))
                e_base_faces.append((n, n+1, n+3, n+2))
                
        i_base_faces.append((-2, -1, 1, 0))
        e_base_faces.append((-2, -1, 1, 0))
        
        i_base_wireframe.add_faces(i_base_faces)
        e_base_wireframe.add_faces(e_base_faces)
        
        self.wireframes['i_base']=i_base_wireframe
        self.wireframes['e_base']=e_base_wireframe
        
        light_wireframe=Wireframe()
        detector_wireframe=Wireframe()
        
        light_nodes=[]
        detector_nodes=[]
        for angle in np.arange(0,math.pi*2,math.pi/30):
            x=math.cos(angle)*0.03
            y1=-1
            y2=-0.6
            z=math.sin(angle)*.03
            light_nodes.append((x,y1,z))
            light_nodes.append((x,y2,z))
            detector_nodes.append((x,y1,z))
            detector_nodes.append((x,y2,z))
            
        light_wireframe.add_nodes(light_nodes)
        detector_wireframe.add_nodes(detector_nodes)
        
        light_edges=[]
        detector_edges=[]
        
        for n in range(len(light_nodes)-2):
            if n%2==0:
                light_edges.append((n, n+1))
                light_edges.append((n, n+2))
        #light_wireframe.add_edges(light_edges)
        
        light_faces=[]
        detector_faces=[]
        
        for n in range(len(light_nodes)-3):
            if n%2==0:
                light_faces.append((n, n+1, n+3, n+2))
                detector_faces.append((n, n+1, n+3, n+2))
        light_wireframe.add_faces(light_faces, color=(150,50,50))
        detector_wireframe.add_faces(detector_faces)
        
        self.wireframes['light']=light_wireframe
        self.wireframes['detector']=detector_wireframe
        
        
        e_wireframe.az=90
        detector_wireframe.az=90
        e_wireframe.set_azimuth(130)
        detector_wireframe.set_azimuth(130)
        
        i_wireframe.az=90
        light_wireframe.az=90
        i_wireframe.set_elevation(-20)
        light_wireframe.set_elevation(-20)
        i_wireframe.set_azimuth(40)
        light_wireframe.set_azimuth(40)
        
        
        
            
        
    def draw_3D_goniometer(self, width, height):
        self.width=width
        self.height=height
        self.char_len=self.height #characteristic length we use to scale drawings
        scale=1.12
        if self.width-120<self.height:
            self.char_len=self.width-120
            
        pivot = (int(self.width/2),int(0.7*self.height),0)
        light_len = int(5*self.char_len/8)
        
        i_radius=int(self.char_len/2)#250
        e_radius=int(i_radius*0.75)
        tray_radius=(i_radius*0.25)
        
        self.wireframes['i'].set_scale(i_radius)
        self.wireframes['i_base'].set_scale(i_radius)
        self.wireframes['light'].set_scale(i_radius)
        self.wireframes['e'].set_scale(e_radius)
        self.wireframes['e_base'].set_scale(e_radius)
        self.wireframes['detector'].set_scale(e_radius)
        self.wireframes['spectralon'].set_scale(tray_radius)
        self.wireframes['tray'].set_scale(tray_radius)


        self.screen.fill(pygame.Color(self.controller.bg))
        slopes=[]
        for wireframe in self.wireframes.values():
            for edge in wireframe.edges:
                slopes.append(abs(edge.delta_y))
        for wireframe in self.wireframes.values():
            wireframe.move_to(pivot)
            if self.display_edges:
                shade=(200,200,200)
                
#                 for edge in wireframe.edges:
#                     try:
#                         slopes.append(edge.delta_y*edge.delta_y/(edge.delta_x*edge.delta_x+edge.delta_z*edge.delta_z))
#                     except:
#                         pass
#                 for edge in wireframe.edges:
#                     try:
#                         slope=edge.delta_y*edge.delta_y/(edge.delta_x*edge.delta_x+edge.delta_z*edge.delta_z)
#                         scale=1-slope/max(slopes)
#                     except:
#                         scale=0
#                         print('vertical')

                for edge in wireframe.edges:
                    slope=abs(edge.delta_y)
                    scale=1-slope/max(slopes)
                    shade=(100+100*scale, 100+100*scale, 100+100*scale)
                    #print(shade)
                    pygame.draw.line(self.screen, shade, (edge.start.x, edge.start.y), (edge.stop.x, edge.stop.y), 2)
            if self.display_nodes:
                for node in wireframe.nodes:
                    pygame.draw.circle(self.screen, self.nodeColour, (int(node.x), int(node.y)), self.nodeRadius, 0)
                    
                
        if self.display_faces:
            
            self.draw_wireframes([self.wireframes['tray']])
            draw_me=[]
            for w in self.wireframes.values():
                if w!=self.wireframes['tray']:
                    draw_me.append(w)
            print(w)
            self.draw_wireframes(draw_me)
            self.set_goniometer_tilt(20)
            
    def draw_wireframes(self, wireframes):
        faces_to_draw=[]
        for wireframe in wireframes:
            faces_to_draw+=wireframe.faces
        faces_to_draw=sorted(faces_to_draw, key=lambda face: -face.min_z)
            
        for face in faces_to_draw:
            shade=(200,200,200)
            light=np.array([-0.7,-0.7,-0.3])
            nodes=face.nodes
            color=face.color
            normal=face.normal
            if False: #normal[2]>0: 
                continue #if it is facing away from us don't draw it
            else:
                theta = np.dot(face.normal, light)
                
                theta=int(theta*100)
                if theta < 0:
                    shade = color
                else:
                    r=min([255,theta+color[0]])
                    g=min([255,theta+color[1]])
                    b=min([255,theta+color[2]])
                    shade = (r,g,b)
                pygame.draw.polygon(self.screen, shade, [(node.x, node.y) for node in nodes], 0)

    def set_goniometer_tilt(self, degrees):
        diff=self.tilt-degrees
        for wireframe in self.wireframes.values():
            wireframe.rotate_el(diff)
        self.tilt=degrees
        
    #draws the side view of the goniometer
    def draw_side_view(self,width,height):
        self.draw_3D_goniometer(width, height)
        return 
#     
#         self.width=width
#         self.height=height
#         self.char_len=self.height
#         scale=1.12
#         if self.width-120<self.height:
#             self.char_len=self.width-120
#         try:
#             i_str='i='+str(int(self.theta_l))
#             e_str='e='+str(int(self.theta_d))
#             sample_str=self.current_sample
# 
#             
#             text_size=np.max([int(self.char_len/18),20])
#             largeText = pygame.font.Font('freesansbold.ttf',text_size)
#             sample_font=pygame.font.Font('freesansbold.ttf',int(0.75*text_size))
#             i_text=largeText.render(i_str, True, pygame.Color(self.controller.textcolor))
#             e_text=largeText.render(e_str, True, pygame.Color(self.controller.textcolor))
#             sample_text=sample_font.render(sample_str, True, pygame.Color(self.controller.textcolor))
#         except:
#             print('no pygame font')
#         
#         #pivot point of goniometer arms. Used as reference for drawing everyting else
#         pivot = (int(self.width/2),int(0.8*self.height))
#         light_len = int(5*self.char_len/8)#300
#         light_width=24  #needs to be an even number
#         
#         back_radius=int(self.char_len/2)#250
#         border_thickness=1
#         
#         x_l = pivot[0] + np.sin(np.radians(self.theta_l)) * light_len
#         x_l_text=pivot[0] + np.sin(np.radians(self.theta_l)) * (light_len/scale)
#         y_l = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len
#         y_l_text = pivot[1] - np.cos(np.radians(self.theta_l)) * light_len*scale-abs(np.sin(np.radians(self.theta_l))*light_len/12)
#         
#         detector_len=light_len
#         detector_width=light_width
#         x_d = pivot[0] + np.sin(np.radians(self.theta_d)) * detector_len
#         x_d_text = pivot[0] + np.sin(np.radians(self.theta_d)) * (detector_len/scale)
#         y_d = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len
#         y_d_text = pivot[1] - np.cos(np.radians(self.theta_d)) * detector_len*scale-abs(np.sin(np.radians(self.theta_d))*detector_len/12)
#         if np.abs(y_d_text-y_l_text)<self.char_len/30 and np.abs(x_d_text-x_l_text)<self.char_len/15:
#             if self.d_up:
#                 y_d_text-=self.char_len/20
#             elif self.l_up:
#                 y_l_text-=self.char_len/20
#             elif y_d_text<y_l_text:
#                 y_d_text-=self.char_len/20
#                 self.d_up=True
#             else:
#                 self.l_up=True
#                 y_l_text-=self.char_len/20
#         else:
#             self.d_up=False
#             self.l_up=False
#         
#         #deltas to give arm width.
#         delta_y_l=light_width/2*np.sin(np.radians(self.theta_l))
#         delta_x_l=light_width/2*np.cos(np.radians(self.theta_l))
#         
#         delta_y_d=detector_width/2*np.sin(np.radians(self.theta_d))
#         delta_x_d=detector_width/2*np.cos(np.radians(self.theta_d))
#         
#         self.screen.fill(pygame.Color(self.controller.bg))
#         
#         #Draw goniometer
#         #pygame.draw.circle(self.screen, pygame.Color('darkgray'), pivot, back_radius+border_thickness, 3)
#         pygame.draw.arc(self.screen, pygame.Color('darkgray'), [pivot[0]-back_radius, pivot[1]-back_radius, 2*back_radius, 2*back_radius], 0,3.14159, 3)
#         #pygame.draw.circle(self.screen, (0,0,0), pivot, back_radius)
#         pygame.draw.rect(self.screen, pygame.Color(self.controller.bg),(pivot[0]-back_radius,pivot[1]+int(self.char_len/10-5),2*back_radius,2*back_radius))
#         #pygame.draw.rect(self.screen, (0,0,0),(pivot[0]-back_radius,pivot[1],2*back_radius,int(self.char_len/6.5)))
#         
#         #draw border around bottom part of goniometer
#         pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius-1,pivot[1]),(pivot[0]-back_radius-1,pivot[1]+int(self.char_len/6.5)), 3)
#         pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]+back_radius,pivot[1]),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)), 3)
#         pygame.draw.line(self.screen,pygame.Color('darkgray'),(pivot[0]-back_radius,pivot[1]+int(self.char_len/6.5)),(pivot[0]+back_radius,pivot[1]+int(self.char_len/6.5)), 3)
# 
#         
#         #draw light arm
#         points=((pivot[0]-delta_x_l,pivot[1]-delta_y_l),(x_l-delta_x_l,y_l-delta_y_l),(x_l+delta_x_l,y_l+delta_y_l),(pivot[0]+delta_x_l,pivot[1]+delta_y_l))
#         pygame.draw.polygon(self.screen, pygame.Color('black'), points)
#         pygame.draw.polygon(self.screen, pygame.Color('darkgray'), points, border_thickness)
#         
#         #draw detector arm
#         points=((pivot[0]-delta_x_d,pivot[1]-delta_y_d),(x_d-delta_x_d,y_d-delta_y_d),(x_d+delta_x_d,y_d+delta_y_d),(pivot[0]+delta_x_d,pivot[1]+delta_y_d))
#         pygame.draw.polygon(self.screen, pygame.Color('black'), points)
#         pygame.draw.polygon(self.screen, pygame.Color('darkgray'), points, border_thickness)
# 
#         
#         
#         self.screen.blit(i_text,(x_l_text,y_l_text))
#         self.screen.blit(e_text,(x_d_text,y_d_text))
#         if self.current_sample=='WR':
#             self.screen.blit(sample_text,(pivot[0]-text_size, pivot[1]+text_size))
#         else:
#             self.screen.blit(sample_text,(pivot[0]-int(1.5*text_size), pivot[1]+text_size))
#         
#         #border around screen
#         pygame.draw.rect(self.screen,pygame.Color('darkgray'),(2,2,self.width-6,self.height+15),2)

        
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
class Node():
    def __init__(self, coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.z = coordinates[2]
        
class Edge():
    def __init__(self, start, stop):
        self.start = start
        self.stop  = stop
        self.delta_x=self.stop.x-self.start.x
        self.delta_y=self.stop.y-self.start.y
        self.delta_z=self.stop.z-self.start.z
        
class Face():
    def __init__(self, node_list, color=(80,80,80)):
        self.nodes=node_list
        self.color=color
        self.delta_x=self.nodes[2].x-self.nodes[0].x
        self.delta_y=self.nodes[2].y-self.nodes[0].y
        self.delta_z=self.nodes[2].z-self.nodes[0].z
        
    def get_normal(self):
        v1=np.array([self.nodes[1].x-self.nodes[0].x, self.nodes[1].y-self.nodes[0].y, self.nodes[1].z-self.nodes[0].z])
        v2=np.array([self.nodes[3].x-self.nodes[0].x, self.nodes[3].y-self.nodes[0].y, self.nodes[3].z-self.nodes[0].z])
        normal= np.cross(v1,v2)
        mag=sum(normal*normal)**0.5
        normal=normal/mag
        return normal
    
    def set_normal(self, val):
        return None
    
    def get_min_z(self):
        z_vals=[]
        for node in self.nodes:
            z_vals.append(node.z)
        return min(z_vals)
    
    def set_min_z(self, val):
        return None
    
    def get_max_z(self):
        z_vals=[]
        for node in self.nodes:
            z_vals.append(node.z)
        return max(z_vals)
    
    def set_max_z(self, val):
        return None
    
    normal=property(get_normal,set_normal)
    min_z=property(get_min_z, set_min_z)
    max_z=property(get_max_z, set_max_z)
        
        
        

            
    
        
class Wireframe():
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.faces=[]
        self.center=(0,0,0)
        self.scale=1
        self.az=0
        self.el=0
        self.home_azimuth=90 #used for rotating
        
    def set_center(self, center):
        self.center=center
        
    def add_nodes(self, node_list):
        for node in node_list:
            self.nodes.append(Node(node))
            
    def add_edges(self, edge_list):
        for (start, stop) in edge_list:
            self.edges.append(Edge(self.nodes[start], self.nodes[stop]))
            
    def add_faces(self, face_list, color=(80,80,80)):
        for corners in face_list:
            node_list=[]
            for index in corners:
                node_list.append(self.nodes[index])
            self.faces.append(Face(node_list, color))

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
        self.az=self.az+degrees
            
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
        az=self.az
        self.set_azimuth(self.home_azimuth)
        diff=self.el-el
        self.rotate_el(diff)
        self.el=el
        self.set_azimuth(az)
        
        
