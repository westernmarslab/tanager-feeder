

import time

from tkinter import ttk, Frame, BOTH
import os
import math
from typing import Dict, List, Tuple, Union

# I don't want pygame to print a welcome message when it loads.
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
import numpy as np

from tanager_feeder.goniometer_view.wireframe import Wireframe
from tanager_feeder.controller import Controller


# Animated graphic of goniometer
class GoniometerView:
    def __init__(self, controller: Controller, notebook: ttk.Notebook):
        self.movements = {"i": [], "e": [], "az": []}

        self.width = 1800
        self.height = 1200
        self.controller = controller
        self.master = self.controller.master
        self.notebook = notebook

        self.collision = False
        self.invalid = False

        self.embed = Frame(self.notebook, width=self.width, height=self.height)
        self.embed.pack(fill=BOTH, expand=True)

        self.double_embed = Frame(self.embed, width=self.width, height=self.height)
        self.double_embed.pack(fill=BOTH, expand=True)

        self.notebook.add(self.embed, text="Goniometer view")

        self.master.update()

        os.environ["SDL_WINDOWID"] = str(self.double_embed.winfo_id())
        #        Needed for pygame 1.9.6, breaks 2.0.0.dev8
        #         if self.controller.opsys=='Windows':
        #             os.environ['SDL_VIDEODRIVER'] = 'windib'
        self.screen = pygame.display.set_mode((self.width, self.height))

        self.light = pygame.Rect(30, 30, 60, 60)

        self.d_up = False
        self.l_up = False
        self.current_sample = "WR"
        self.tray_angle = 0

        self.wireframes = {}
        self.display_nodes = False
        self.display_edges = False
        self.display_faces = True
        self.nodeColour = (255, 255, 255)
        self.edge_color = (200, 200, 200)
        self.node_radius = 4
        self.char_len = self.height
        self.sample_names = ["spectralon"]
        for i in range(1, 6):
            self.sample_names.append("Sample " + str(i))
        self.define_goniometer_wireframes()
        self.define_sample_tray_wireframes()

        self.tilt = 0  # tilt of entire goniometer

        self.motor_i = 20
        self.science_i = 20
        self.motor_az = 90
        self.science_az = 90
        self.science_e = 0
        self.motor_e = 0
        self.define_az_guide_wireframes()

        self.samples = ["WR", "Sample 1", "Sample 2", "Sample 3", "Sample 4", "Sample 5"]
        self.standard_delay = 0.0001
        pygame.init()

    def tab_switch(self, event) -> None:
        print("here is the event!")
        print(event)
        print(type(event))
        # pylint: disable=unused-argument
        self.master.update()
        os.environ["SDL_WINDOWID"] = str(self.double_embed.winfo_id())
        #        Needed for pygame 1.9.6, breaks 2.0.0.dev8
        #         if self.controller.opsys=='Windows':
        #             os.environ['SDL_VIDEODRIVER'] = 'windib'
        self.flip()

    @staticmethod
    def flip(event=None) -> None:
        # pylint: disable=unused-argument
        pygame.display.update()
        pygame.display.flip()

    def define_sample_tray_wireframes(self) -> None:
        tray_wireframe = Wireframe()
        samples = Dict[str: Dict[str: Union[Tuple[int, int, int]], Wireframe, List]]
        samples["spectralon"] = {"color": (200, 200, 200)}
        samples["1"] = {"color": (120, 0, 20)}
        samples["2"] = {"color": (120, 80, 0)}
        samples["3"] = {"color": (80, 120, 0)}
        samples["4"] = {"color": (0, 80, 120)}
        samples["5"] = {"color": (20, 0, 120)}

        for sample_attribute_dictionary in samples.values():
            sample_attribute_dictionary["wireframe"] = Wireframe()
            sample_attribute_dictionary["nodes"] = []
            sample_attribute_dictionary["faces"] = []

        tray_nodes = []
        for angle in np.arange(0, math.pi * 2, math.pi / 8):
            x = math.cos(angle) - 0.6
            y1 = 0.03
            y2 = 0.1
            y3 = 0
            z = math.sin(angle)
            tray_nodes.append((x, y1, z))
            tray_nodes.append((x, y2, z))
            for i, sample in enumerate(samples.values()):
                theta = i * 2 * math.pi / 6  # angular position of sample on tray
                center_x = 0.6 * math.cos(theta) - 0.45
                center_z = 0.6 * math.sin(theta)
                sample["nodes"].append((0.25 * x + center_x, y3, 0.25 * z + center_z))
                sample["nodes"].append((0.25 * x + center_x, y1, 0.25 * z + center_z))

        tray_wireframe.add_nodes(tray_nodes)
        for sample in samples.values():
            sample["wireframe"].add_nodes(sample["nodes"])

        tray_faces = []

        for n in range(len(tray_nodes)):
            if n < len(tray_nodes) - 3:
                if n % 2 == 0:
                    tray_faces.append((n, n + 1, n + 3, n + 2))
                    for sample in samples.values():
                        sample["faces"].append((n, n + 1, n + 3, n + 2))

        for n in range(len(tray_nodes)):
            if n == 0:
                tray_faces.append((0,))
                for sample in samples.values():
                    sample["faces"].append((0,))
            elif n % 2 == 0:
                tray_faces[-1] += (n,)
                for sample in samples.values():
                    sample["faces"][-1] += (n,)
        tray_wireframe.add_faces(tray_faces)

        for sample in samples.values():
            sample["wireframe"].add_faces(sample["faces"], color=sample["color"])
            sample["wireframe"].set_rotation_center((-0.6, 0.0, 0))
            sample["wireframe"].az = 0

        self.wireframes["tray"] = tray_wireframe
        for i, sample in enumerate(samples.values()):
            self.wireframes[self.sample_names[i]] = sample["wireframe"]

    def define_goniometer_wireframes(self) -> None:
        i_wireframe = Wireframe()
        e_wireframe = Wireframe()

        i_nodes = []
        e_nodes = []

        def append_next_nodeset(node_list: List, x: float, y: float) -> None:
            node_list.append((x, y, -0.1))
            node_list.append((x, y, 0.1))
            node_list.append((x * 0.95, y * 0.95, -0.1))
            node_list.append((x * 0.95, y * 0.95, 0.1))

        for angle in np.arange(0, math.pi, math.pi / 30):
            next_x = math.cos(angle)
            next_y = -math.sin(angle)
            append_next_nodeset(i_nodes, next_x, next_y)
            if angle <= math.pi / 2:
                append_next_nodeset(e_nodes, next_x, next_y)

        next_x = math.cos(math.pi)
        next_y = -math.sin(math.pi)
        append_next_nodeset(i_nodes, next_x, next_y)

        i_wireframe.add_nodes(i_nodes)

        next_x = math.cos(math.pi / 2)
        next_y = -math.sin(math.pi / 2)
        e_nodes.append((next_x - 0.05, next_y, -0.1))
        e_nodes.append((next_x - 0.05, next_y, 0.1))
        e_nodes.append((next_x * 0.95 - 0.05, next_y * 0.95, -0.1))
        e_nodes.append((next_x * 0.95 - 0.05, next_y * 0.95, 0.1))

        e_wireframe.add_nodes(e_nodes)

        i_edges = []
        e_edges = []

        for next_n in range(len(i_nodes) - 4):
            i_edges.append((next_n, next_n + 4))
            if next_n < len(e_nodes) - 4:
                e_edges.append((next_n, next_n + 4))

        i_wireframe.add_edges(i_edges)
        e_wireframe.add_edges(e_edges)

        i_faces = []
        e_faces = []

        def append_next_faceset(face_list: List, n: int) -> None:
            face_list.append((n, n + 2, n + 6, n + 4))
            face_list.append((n, n + 1, n + 5, n + 4))
            face_list.append((n + 2, n + 6, n + 7, n + 3))
            face_list.append((n + 1, n + 3, n + 7, n + 5))

        for next_n in range(len(i_nodes) - 7):
            if next_n % 4 == 0:
                append_next_faceset(i_faces, next_n)
                if next_n < len(e_nodes) - 7:
                    append_next_faceset(e_faces, next_n)

        i_wireframe.add_faces(i_faces)
        e_wireframe.add_faces(e_faces)

        self.wireframes["e"] = e_wireframe
        self.wireframes["i"] = i_wireframe

        i_base_wireframe = Wireframe()
        e_base_wireframe = Wireframe()

        i_base_nodes = self.draw_arc(0, math.pi*2)
        e_base_nodes = self.draw_arc(0, math.pi*2)

        i_base_wireframe.add_nodes(i_base_nodes)
        e_base_wireframe.add_nodes(e_base_nodes)

        i_base_edges = []
        e_base_edges = []

        for next_n in range(len(i_base_nodes) - 2):
            i_base_edges.append((next_n, next_n + 2))
            e_base_edges.append((next_n, next_n + 2))
        i_base_edges.append((-2, 0))
        e_base_edges.append((-2, 0))
        i_base_edges.append((-1, 1))
        e_base_edges.append((-1, 1))

        e_base_faces = []
        i_base_faces = []
        for next_n in range(len(e_base_nodes) - 3):
            if next_n % 2 == 0:
                i_base_faces.append((next_n, next_n + 1, next_n + 3, next_n + 2))
                e_base_faces.append((next_n, next_n + 1, next_n + 3, next_n + 2))

        i_base_faces.append((-2, -1, 1, 0))
        e_base_faces.append((-2, -1, 1, 0))

        i_base_wireframe.add_faces(i_base_faces)
        e_base_wireframe.add_faces(e_base_faces)

        self.wireframes["i_base"] = i_base_wireframe
        self.wireframes["e_base"] = e_base_wireframe

        light_wireframe = Wireframe()
        detector_wireframe = Wireframe()

        light_guide_wireframe = Wireframe()
        detector_guide_wireframe = Wireframe()

        light_guide_nodes = []
        detector_guide_nodes = []
        x_vals = [-0.01, 0.01, -0.01, 0.01]
        z_vals = [-0.01, -0.01, 0.01, 0.01]
        for i in range(4):
            next_x = x_vals[i] / 4
            y1 = 0
            y2 = -0.6
            z = z_vals[i] / 4
            light_guide_nodes.append((next_x * 0.75, y1, z * 0.75))
            light_guide_nodes.append((next_x * 0.75, y2, z * 0.75))
            detector_guide_nodes.append((next_x, y1, z))
            detector_guide_nodes.append((next_x, y2, z))
        light_guide_wireframe.add_nodes(light_guide_nodes)
        detector_guide_wireframe.add_nodes(detector_guide_nodes)

        light_guide_faces = []
        detector_guide_faces = []
        for next_n in range(len(light_guide_nodes) - 3):
            light_guide_faces.append((next_n, next_n + 1, next_n + 3, next_n + 2))
            detector_guide_faces.append((next_n, next_n + 1, next_n + 3, next_n + 2))
        light_guide_wireframe.add_faces(light_guide_faces)
        detector_guide_wireframe.add_faces(detector_guide_faces)

        self.wireframes["light guide"] = light_guide_wireframe
        self.wireframes["detector guide"] = detector_guide_wireframe

        light_nodes = []
        detector_nodes = []
        for angle in np.arange(0, math.pi * 2, math.pi / 30):
            next_x = math.cos(angle) * 0.03
            y1 = -1
            y2 = -0.6

            z = math.sin(angle) * 0.03
            light_nodes.append((next_x, y1, z))
            light_nodes.append((next_x, y2, z))

            detector_nodes.append((next_x, y1, z))
            detector_nodes.append((next_x, y2, z))

        light_wireframe.add_nodes(light_nodes)
        detector_wireframe.add_nodes(detector_nodes)

        light_edges = []
        detector_edges = []

        for next_n in range(len(light_nodes) - 2):
            if next_n % 2 == 0:
                light_edges.append((next_n, next_n + 1))
                light_edges.append((next_n, next_n + 2))
                detector_edges.append((next_n, next_n + 1))
                detector_edges.append((next_n, next_n + 2))
        light_wireframe.add_edges(light_edges)
        detector_wireframe.add_edges(detector_edges)

        light_faces = []
        detector_faces = []

        for next_n in range(len(light_nodes) - 3):
            if next_n % 2 == 0:
                light_faces.append((next_n, next_n + 1, next_n + 3, next_n + 2))
                detector_faces.append((next_n, next_n + 1, next_n + 3, next_n + 2))

        # Uncomment if drawing the fiber optic sticking out above the top of the emission arm.
        #         for n in range(len(detector_nodes)-5):
        #             if n%3==0:
        #                 detector_faces.append((n, n+1, n+4, n+3))
        #                 detector_faces.append((n+1, n+2, n+5, n+4))

        light_wireframe.add_faces(light_faces, color=(150, 50, 50))
        detector_wireframe.add_faces(detector_faces)

        self.wireframes["light"] = light_wireframe
        self.wireframes["detector"] = detector_wireframe

        e_wireframe.az = 90
        detector_wireframe.az = 90
        detector_guide_wireframe.az = 90
        e_wireframe.set_azimuth(130)
        detector_wireframe.set_azimuth(130)
        detector_guide_wireframe.set_azimuth(130)

        i_wireframe.az = 90
        light_wireframe.az = 90
        light_guide_wireframe.az = 90

        i_wireframe.set_elevation(20)
        light_wireframe.set_elevation(20)
        light_guide_wireframe.set_elevation(20)

        i_wireframe.set_azimuth(220)
        light_wireframe.set_azimuth(220)
        light_guide_wireframe.set_azimuth(220)

    @staticmethod
    def draw_arc(first_arc_angle: float, last_angle: float) -> List[Tuple[float, float, float]]:
        if last_angle > first_arc_angle:
            increment = math.pi / 30
        else:
            increment = -1 * math.pi / 30

        node_list = []
        for angle in np.append(np.arange(first_arc_angle, last_angle, increment), last_angle):
            x1 = math.cos(angle) * 1.01
            x2 = math.cos(angle) * 0.99
            y = 0
            z1 = math.sin(angle) * 1.01
            z2 = math.sin(angle) * 0.99
            node_list.append((x1, y, z1))
            node_list.append((x2, y, z2))
        return node_list

    def define_az_guide_wireframes(self) -> None:
        # Draw a two circles, one showing the measured azimtuh angle and the other showing how far the goniometer has
        # actually rotated. Since the current mechanical design limits azimuth rotation to 0-170 degrees, these
        # will always be the same. In theory, if the goniometer was rotated past 180 degrees, the science az would
        # reset to 0 and incidence would then be -1 * incidence.
        motor_az_guide_wireframe = Wireframe()
        science_az_guide_wireframe = Wireframe()

        first_angle = -1 * (self.wireframes["detector"].az - 90) * math.pi / 180
        last_motor_angle = -1 * (self.wireframes["detector"].az + self.motor_az - 90) * math.pi / 180
        last_science_angle = -1 * (self.wireframes["detector"].az + self.science_az - 90) * math.pi / 180

        motor_az_guide_nodes = self.draw_arc(first_angle, last_motor_angle)
        science_az_guide_nodes = self.draw_arc(first_angle, last_science_angle)

        motor_az_guide_wireframe.add_nodes(motor_az_guide_nodes)
        science_az_guide_wireframe.add_nodes(science_az_guide_nodes)

        motor_az_guide_faces = []
        for n in range(len(motor_az_guide_nodes) - 3):
            if n % 2 == 0:
                motor_az_guide_faces.append((n, n + 1, n + 3, n + 2))

        if self.motor_az >= 0:
            motor_az_guide_wireframe.add_faces(motor_az_guide_faces, color=(100, 200, 255))
        else:
            motor_az_guide_wireframe.add_faces(motor_az_guide_faces, color=(255, 155, 255))

        science_az_guide_faces = []
        for n in range(len(science_az_guide_nodes) - 3):
            if n % 2 == 0:
                science_az_guide_faces.append((n, n + 1, n + 3, n + 2))
        science_az_guide_wireframe.add_faces(science_az_guide_faces, color=(200, 255, 155))

        self.wireframes["motor az guide"] = motor_az_guide_wireframe
        self.wireframes["science az guide"] = science_az_guide_wireframe
        motor_az_guide_wireframe.rotate_el(-1 * self.tilt)
        science_az_guide_wireframe.rotate_el(-1 * self.tilt)

    def draw_3D_goniometer(self, width: int, height: int) -> None:
        # pylint: disable=function-naming-style
        self.width = width
        self.height = height

        self.char_len = self.height  # characteristic length we use to scale drawings
        if self.width - 120 < self.height:
            self.char_len = self.width - 120

        pivot = (int(self.width / 2) - 20, int(0.7 * self.height), 0)

        i_radius = int(self.char_len / 2)  # 250
        e_radius = int(i_radius * 0.75)
        tray_radius = i_radius * 0.25

        if self.collision:
            for face in self.wireframes["i"].faces:
                face.color = (150, 50, 50)
            for face in self.wireframes["e"].faces:
                face.color = (150, 50, 50)
        elif self.invalid:
            for face in self.wireframes["i"].faces:
                face.color = (50, 50, 150)
            for face in self.wireframes["e"].faces:
                face.color = (50, 50, 150)
        else:
            for face in self.wireframes["i"].faces:
                face.color = (80, 80, 80)
            for face in self.wireframes["e"].faces:
                face.color = (80, 80, 80)

        self.wireframes["i"].set_scale(i_radius)
        self.wireframes["i_base"].set_scale(i_radius)
        self.wireframes["light"].set_scale(i_radius)
        self.wireframes["light guide"].set_scale(i_radius)
        try:
            self.wireframes["motor az guide"].set_scale(i_radius)
            self.wireframes["science az guide"].set_scale(e_radius)
        except Exception as e:
            # TODO: disable broad except
            raise e

        self.wireframes["e"].set_scale(e_radius)
        self.wireframes["e_base"].set_scale(e_radius)
        self.wireframes["detector"].set_scale(e_radius)
        self.wireframes["detector guide"].set_scale(e_radius)
        # self.wireframes['spectralon'].set_scale(tray_radius)

        for sample in self.sample_names:
            self.wireframes[sample].set_scale(tray_radius)
        self.wireframes["tray"].set_scale(tray_radius)

        self.screen.fill(pygame.Color(self.controller.bg))
        slopes = []
        for wireframe in self.wireframes.values():
            for edge in wireframe.edges:
                slopes.append(abs(edge.delta_y))
        for wireframe in self.wireframes.values():
            wireframe.move_to(pivot)
            if self.display_edges:
                for edge in wireframe.edges:
                    slope = abs(edge.delta_y)
                    scale = 1 - slope / max(slopes)
                    shade = (100 + 100 * scale, 100 + 100 * scale, 100 + 100 * scale)
                    pygame.draw.line(self.screen, shade, (edge.start.x, edge.start.y), (edge.stop.x, edge.stop.y), 2)

            if self.display_nodes:
                for node in wireframe.nodes:
                    pygame.draw.circle(self.screen, self.nodeColour, (int(node.x), int(node.y)), self.node_radius, 0)

        if self.display_faces:

            self.draw_wireframes([self.wireframes["tray"]])
            draw_me = [self.wireframes["e_base"], self.wireframes["i_base"]]
            for sample in self.sample_names:
                draw_me.append(self.wireframes[sample])
            self.draw_wireframes(draw_me)

            draw_me = []
            for w in self.wireframes.values():
                draw = True
                for sample in self.sample_names:
                    if w == self.wireframes[sample]:
                        draw = False
                if w == self.wireframes["tray"] or w == self.wireframes["e_base"] or w == self.wireframes["i_base"]:
                    draw = False
                if draw:
                    draw_me.append(w)
            self.draw_wireframes(draw_me)
            self.set_goniometer_tilt(20)

            i_str = "i=" + str(int(self.science_i))
            e_str = "e=" + str(int(self.science_e))
            az_str = "az=" + str(int(self.science_az))
            sample_str = self.current_sample

            text_size = np.max([int(self.char_len / 18), 20])
            large_text = pygame.font.Font("freesansbold.ttf", text_size)
            sample_font = pygame.font.Font("freesansbold.ttf", int(0.75 * text_size))
            i_text = large_text.render(i_str, True, pygame.Color(self.controller.textcolor))
            e_text = large_text.render(e_str, True, pygame.Color(self.controller.textcolor))
            az_text = large_text.render(az_str, True, pygame.Color(self.controller.textcolor))
            sample_text = sample_font.render(sample_str, True, pygame.Color(self.controller.textcolor))

            top_text_x = pivot[0] - 1.1 * i_radius
            top_text_y = pivot[1] - 1.1 * i_radius
            middle_text_x = top_text_x
            middle_text_y = top_text_y + int(text_size * 1.3)
            bottom_text_x = pivot[0] + 1.1 * i_radius
            bottom_text_y = pivot[1]

            x_l_text = top_text_x
            y_l_text = top_text_y
            x_d_text = middle_text_x
            y_d_text = middle_text_y
            x_az_text = bottom_text_x
            y_az_text = bottom_text_y

            self.screen.blit(i_text, (x_l_text, y_l_text))
            self.screen.blit(e_text, (x_d_text, y_d_text))
            self.screen.blit(az_text, (x_az_text, y_az_text))
            if self.current_sample == "WR":
                self.screen.blit(sample_text, (pivot[0] - int(0.7 * text_size), pivot[1] + int(1.2 * text_size)))
            else:
                self.screen.blit(sample_text, (pivot[0] - int(1.2 * text_size), pivot[1] + int(1.2 * text_size)))

    def draw_wireframes(self, wireframes: List[Wireframe]):
        faces_to_draw = []
        for wireframe in wireframes:
            faces_to_draw += wireframe.faces
        faces_to_draw = sorted(faces_to_draw, key=lambda face_to_draw: -face_to_draw.min_z)

        for face in faces_to_draw:
            light = np.array([-0.7, -0.7, -0.3])
            nodes = face.nodes
            color = face.color
            theta = np.dot(face.normal, light)
            try:
                theta = int(theta * 100)
            except ValueError:
                theta = -1
            if theta < 0:
                shade = color
            else:
                r = min([255, theta + color[0]])
                g = min([255, theta + color[1]])
                b = min([255, theta + color[2]])
                shade = (r, g, b)
            pygame.draw.polygon(self.screen, shade, [(node.x, node.y) for node in nodes], 0)

    def set_goniometer_tilt(self, degrees: int):
        diff = self.tilt - degrees
        for wireframe in self.wireframes.values():
            wireframe.rotate_el(diff)
        self.tilt = degrees

    # draws the side view of the goniometer
    def draw_side_view(self, width: int, height: int):
        self.draw_3D_goniometer(width, height)
        return

    def check_collision(self, i: int, e: int, az: int) -> None:
        self.collision = self.controller.check_if_good_measurement(i, e, az)

    def set_incidence(self, motor_i: int, config: bool = False) -> None:
        self.movements["i"].append(np.abs(self.motor_i - motor_i))

        def next_pos(delta_theta):
            self.motor_i = self.motor_i + delta_theta
            if 0 <= self.motor_az < 180:
                self.science_i = self.motor_i
            else:
                self.science_i = -1 * self.motor_i

            if not config:
                time.sleep(self.standard_delay)
            else:
                time.sleep(0.005)

            self.set_goniometer_tilt(0)

            self.wireframes["i"].set_elevation(self.motor_i)
            self.wireframes["light"].set_elevation(self.motor_i)
            self.wireframes["light guide"].set_elevation(self.motor_i)

            self.check_collision(self.science_i, self.science_e, self.science_az)

            self.set_goniometer_tilt(20)
            self.draw_3D_goniometer(self.width, self.height)
            self.flip()

        next_delta_theta = -1 * 5 * np.sign(self.motor_i - motor_i)
        while np.abs(self.motor_i - motor_i) >= 5:
            next_pos(next_delta_theta)

        next_delta_theta = -1 * np.sign(self.motor_i - motor_i)
        while np.abs(self.motor_i - motor_i) >= 1:
            next_pos(next_delta_theta)

    def set_azimuth(self, motor_az: int, config: bool = False) -> None:
        self.movements["az"].append(np.abs(self.motor_az - motor_az))
        if motor_az > self.controller.max_motor_az or motor_az < self.controller.min_motor_az:
            raise Exception("MOTOR AZ OUTSIDE RANGE: " + str(motor_az))

        def next_pos(delta_theta: int) -> None:
            next_drawing_az = self.wireframes["i"].az + delta_theta

            if not config:
                time.sleep(self.standard_delay)
            else:
                time.sleep(0.005)

            self.set_goniometer_tilt(0)
            self.wireframes["i"].set_azimuth(next_drawing_az)
            self.wireframes["light"].set_azimuth(next_drawing_az)
            self.wireframes["light guide"].set_azimuth(next_drawing_az)
            self.set_goniometer_tilt(20)
            self.motor_az = self.wireframes["i"].az - self.wireframes["e"].az
            if 0 <= self.motor_az < 180:
                self.science_az = self.motor_az
                self.science_i = self.motor_i
            elif self.motor_az >= 180:
                self.science_az = self.motor_az - 180
                self.science_i = -1 * self.motor_i
            elif self.motor_az < 0:
                self.science_az = self.motor_az + 180
                self.science_i = -1 * self.motor_i

            self.check_collision(self.science_i, self.science_e, self.science_az)
            self.define_az_guide_wireframes()
            self.draw_3D_goniometer(self.width, self.height)
            self.flip()

        next_delta_theta = 5 * np.sign(motor_az - self.motor_az)
        while np.abs(motor_az - self.motor_az) >= 5:
            next_pos(next_delta_theta)

        next_delta_theta = np.sign(motor_az - self.motor_az)
        while np.abs(motor_az - self.motor_az) >= 0.5:
            next_pos(next_delta_theta)

    def set_current_sample(self, sample: str) -> None:
        if self.current_sample == "wr":
            self.current_sample = "WR"
        if sample == "wr":
            sample = "WR"
        current_degrees = self.samples.index(self.current_sample) * 60
        self.current_sample = sample
        next_degrees = self.samples.index(sample) * 60

        delta_theta = np.sign(next_degrees - current_degrees) * 10
        degrees_moved = 0
        degrees_to_rotate = np.abs(next_degrees - current_degrees)
        while degrees_moved < degrees_to_rotate:
            self.rotate_tray(-1 * delta_theta)
            degrees_moved += np.abs(delta_theta)
            self.draw_3D_goniometer(self.width, self.height)
            self.flip()

    def set_emission(self, motor_e: int, config: bool = False) -> None:
        self.movements["e"].append(np.abs(self.motor_e - motor_e))

        def next_pos(delta_theta: int) -> None:
            self.motor_e = self.motor_e + delta_theta
            self.science_e = self.science_e + delta_theta
            if not config:
                time.sleep(self.standard_delay)
            else:
                time.sleep(0.005)

            self.set_goniometer_tilt(0)
            self.wireframes["e"].set_elevation(self.motor_e)
            self.wireframes["detector"].set_elevation(self.motor_e)
            self.wireframes["detector guide"].set_elevation(self.motor_e)

            self.check_collision(self.science_i, self.science_e, self.science_az)

            self.set_goniometer_tilt(20)
            self.draw_3D_goniometer(self.width, self.height)
            self.flip()

        next_delta_theta = 5 * np.sign(motor_e - self.motor_e)
        while np.abs(motor_e - self.motor_e) >= 5:
            next_pos(next_delta_theta)

        next_delta_theta = np.sign(motor_e - self.motor_e)
        while np.abs(motor_e - self.motor_e) >= 1:
            next_pos(next_delta_theta)

    def rotate_tray(self, degrees: float) -> None:
        tilt = self.tilt
        self.set_goniometer_tilt(0)
        for sample in self.sample_names:
            self.wireframes[sample].rotate_az(degrees)
        self.set_goniometer_tilt(tilt)

    def set_tray_position(self, theta: float) -> None:
        diff = self.tray_angle - theta
        self.rotate_tray(diff)
        self.tray_angle = theta

    @staticmethod
    def quit():
        pygame.display.quit()
        pygame.quit()
