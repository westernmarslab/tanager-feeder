# see reference: http://www.petercollingridge.co.uk/tutorials/3d/pygame/nodes-and-edges/
import math
from typing import Dict, Tuple

from tanager_feeder.goniometer_view.wireframe_components import Node, Edge, Face


class Wireframe:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.faces = []
        self.center = {"scale": (0, 0, 0), "rotate": (0, 0, 0), "translate": (0, 0, 0)}
        self.scale = 1
        self.az = 0
        self.el = 0
        self.home_azimuth = 90  # used for rotating

    def set_center(self, center: Dict[str: Tuple[int, int, int]]):
        self.center = center

    def set_rotation_center(self, center):
        self.center["rotate"] = center

    def add_nodes(self, node_list):
        for node in node_list:
            self.nodes.append(Node(node))

    def add_edges(self, edge_list):
        for (start, stop) in edge_list:
            self.edges.append(Edge(self.nodes[start], self.nodes[stop]))

    def add_faces(self, face_list, color=(80, 80, 80)):
        for corners in face_list:
            node_list = []
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
            print("to (%.2f, %.2f, %.2f)" % (edge.stop.x, edge.stop.y, edge.stop.z))

    def scale(self, scale):
        # Scale the wireframe from the centre of the screen.
        for node in self.nodes:
            node.x = self.center["scale"][0] + scale * (node.x - self.center["scale"][0])
            node.y = self.center["scale"][1] + scale * (node.y - self.center["scale"][1])
            node.z *= scale

    def translate(self, axis, d):
        # Translate each node of a wireframe by d along a given axis.
        if axis in ["x", "y", "z"]:
            for node in self.nodes:
                setattr(node, axis, getattr(node, axis) + d)

    def move_to(self, center: Tuple[int, int, int]):
        diff = Dict[str: int]
        diff["x"] = center[0] - self.center["translate"][0]
        diff["y"] = center[1] - self.center["translate"][1]
        diff["z"] = center[2] - self.center["translate"][2]
        for node in self.nodes:
            for axis in ["x", "y", "z"]:
                setattr(node, axis, getattr(node, axis) + diff[axis])
        self.center["translate"] = center
        rotate = Tuple[int, int, int]
        for i, val in enumerate(diff.values()):
            rotate += (self.center["rotate"][i] + val,)
        self.center["rotate"] = rotate

    def set_scale(self, scale):
        diff = scale / self.scale
        for node in self.nodes:
            node.x = self.center["scale"][0] + diff * (node.x - self.center["scale"][0])
            node.y = self.center["scale"][1] + diff * (node.y - self.center["scale"][1])
            node.z = self.center["scale"][2] + diff * (node.z - self.center["scale"][2])
        rotate = Tuple[int, int, int]
        translate = Tuple[int, int, int]
        for i in range(0, 3):
            rotate += (self.center["rotate"][i] * diff,)
            translate += (self.center["translate"][i] * diff,)
        self.center["rotate"] = rotate
        self.center["translate"] = translate
        self.scale = scale

    def rotate_az(self, degrees):
        radians = degrees / 180 * math.pi
        for node in self.nodes:
            x = node.x - self.center["rotate"][0]
            z = node.z - self.center["rotate"][2]
            d = math.hypot(x, z)
            theta = math.atan2(x, z) + radians
            node.z = self.center["rotate"][2] + d * math.cos(theta)
            node.x = self.center["rotate"][0] + d * math.sin(theta)
        self.az = self.az + degrees

    def rotate_el(self, degrees):
        radians = degrees / 180 * math.pi
        for node in self.nodes:
            y = node.y - self.center["rotate"][1]
            z = node.z - self.center["rotate"][2]
            d = math.hypot(y, z)
            theta = math.atan2(y, z) + radians
            node.z = self.center["rotate"][2] + d * math.cos(theta)
            node.y = self.center["rotate"][1] + d * math.sin(theta)

    def set_azimuth(self, az):
        diff = az - self.az
        self.rotate_az(diff)
        self.az = az

    def set_elevation(self, el):
        az = self.az
        self.set_azimuth(self.home_azimuth)
        diff = self.el - el
        self.rotate_el(diff)
        self.el = el
        self.set_azimuth(az)
