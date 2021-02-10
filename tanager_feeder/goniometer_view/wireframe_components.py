# see reference: http://www.petercollingridge.co.uk/tutorials/3d/pygame/nodes-and-edges/

class Node:
    def __init__(self, coordinates):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.z = coordinates[2]


class Edge:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop
        self.delta_x = self.stop.x - self.start.x
        self.delta_y = self.stop.y - self.start.y
        self.delta_z = self.stop.z - self.start.z


class Face:
    def __init__(self, node_list, color=(80, 80, 80)):
        self.nodes = node_list
        self.color = color
        self.delta_x = self.nodes[2].x - self.nodes[0].x
        self.delta_y = self.nodes[2].y - self.nodes[0].y
        self.delta_z = self.nodes[2].z - self.nodes[0].z

    def get_normal(self):
        v1 = np.array(
            [self.nodes[1].x - self.nodes[0].x, self.nodes[1].y - self.nodes[0].y, self.nodes[1].z - self.nodes[0].z]
        )
        v2 = np.array(
            [self.nodes[3].x - self.nodes[0].x, self.nodes[3].y - self.nodes[0].y, self.nodes[3].z - self.nodes[0].z]
        )
        normal = np.cross(v1, v2)
        mag = sum(normal * normal) ** 0.5
        normal = normal / mag
        return normal

    def set_normal(self, val):
        return None

    def get_min_z(self):
        z_vals = []
        for node in self.nodes:
            z_vals.append(node.z)
        return min(z_vals)

    def set_min_z(self, val):
        return None

    def get_max_z(self):
        z_vals = []
        for node in self.nodes:
            z_vals.append(node.z)
        return max(z_vals)

    def set_max_z(self, val):
        return None

    normal = property(get_normal, set_normal)
    min_z = property(get_min_z, set_min_z)
    max_z = property(get_max_z, set_max_z)