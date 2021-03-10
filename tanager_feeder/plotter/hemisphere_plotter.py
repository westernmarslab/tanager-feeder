from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl

from tanager_feeder.utils import cos, sin

class HemispherePlotter:
    def __init__(self):
        pass

    def plot(self, geoms, data):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Make data
        azimuths = np.linspace(0, 359, 360)
        emissions = np.linspace(0, 89, 90)

        for j, az in enumerate(azimuths):
            azimuths[j] = int(az)
        for j, e in enumerate(emissions):
            emissions[j] = int(e)

        R = {}

        for i, tup in enumerate(geoms):
            e = int(tup[1])
            az = int(tup[2])
            if e < 0:
                az = az + 180
                e = np.abs(e)
            if az not in R:
                R[az] = {}
            else:
                R[az][e] = data[i]

        data = np.array(data)
        avg = np.mean(data)
        norm = mpl.colors.Normalize(vmin=np.min(data), vmax=np.max(data))

        x = []
        y = []
        z = []
        r = []

        scatter_x = []
        scatter_y = []
        scatter_z = []

        winnowed_az = []
        winnowed_e = []

        for i, az in enumerate(azimuths):
            if az in R:
                winnowed_az.append(az)
                for j, e in enumerate(emissions):
                    if e in R[az]:
                        if e not in winnowed_e:
                            winnowed_e.append(e)
        winnowed_az = sorted(winnowed_az)
        winnowed_e = sorted(winnowed_e)

        for i, az in enumerate(winnowed_az):
            x.append([])
            y.append([])
            z.append([])
            r.append([])

            for j, e in enumerate(winnowed_e):
                if e in R[az]:
                    x[-1].append(cos(az) * sin(e) * R[az][e])
                    y[-1].append(sin(az) * sin(e) * R[az][e])
                    z[-1].append(cos(e) * R[az][e])
                    r[-1].append(R[az][e])

                    scatter_x.append(cos(az) * sin(e) * R[az][e])
                    scatter_y.append(sin(az) * sin(e) * R[az][e])
                    scatter_z.append(cos(e) * R[az][e])
                # To have nicely behaved 2D arrays, all should represent the same az, e pairs (I think)
                else:
                    x[-1].append(None)
                    y[-1].append(None)
                    z[-1].append(None)
                    r[-1].append(None)

        for j in range(len(r)):
            for k in range(len(r[j])):
                if r[j][k] is None:
                    close_rs = []
                    search_index = j
                    while search_index >= 0 and r[search_index][k] is None:
                        search_index -= 1
                    if search_index > -1:
                        close_rs.append(r[search_index][k])

                    search_index = j
                    while search_index < len(r) and r[search_index][k] is None:
                        search_index += 1
                    if search_index < len(r):
                        close_rs.append(r[search_index][k])

                    search_index = k
                    while search_index >= 0 and r[j][search_index] is None:
                        search_index -= 1
                    if search_index > -1:
                        close_rs.append(r[j][search_index])

                    search_index = k
                    while search_index < len(r[j]) and r[j][search_index] is None:
                        search_index += 1

                    if search_index < len(r[j]):
                        close_rs.append(r[j][search_index])

                    avg = np.mean(close_rs)
                    az = winnowed_az[j]
                    e = winnowed_e[k]

                    x[j][k] = cos(az) * sin(e) * avg
                    y[j][k] = sin(az) * sin(e) * avg
                    z[j][k] = cos(e) * avg
                    r[j][k] = avg

        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

        jet = plt.cm.jet
        colors = []
        num_az = len(winnowed_az)
        num_e = len(winnowed_e)

        for i in range(num_az):
            colors.append([])
            for j in range(num_e):
                vals_to_avg = [norm(r[i][j])]
                if i < num_az - 1:
                    vals_to_avg.append(norm(r[i + 1][j]))
                    if j < num_e - 1:
                        vals_to_avg.append(norm(r[i][j + 1]))
                        vals_to_avg.append(norm(r[i + 1][j + 1]))
                    else:
                        pass  # e values do not wrap around (it's a hemisphere, not a sphere)
                elif winnowed_az[i] > 330:  # az values can wrap around.
                    vals_to_avg.append(norm(r[0][j]))
                    if j < num_e - 1:
                        vals_to_avg.append(norm(r[i][j + 1]))
                        vals_to_avg.append(norm(r[0][j + 1]))
                    else:
                        pass  # e values do not wrap around (it's a hemisphere, not a sphere)
                val = np.mean(vals_to_avg)
                colors[i].append(jet(val))

        # u = np.linspace(0, 2 * np.pi, 30)
        # v = np.linspace(0, np.pi/2, 15)
        # back_x = np.outer(np.cos(u), np.sin(v))
        # back_y = np.outer(np.sin(u), np.sin(v))
        # back_z = np.outer(np.ones(np.size(u)), 0)
        # backdrop = ax.plot_surface(back_x, back_y, back_z, alpha=0.8, zorder=0)

        # Plot the surface
        ax.plot_surface(x, y, z,
                        linewidth=1, alpha=1, facecolors=colors, zorder=100)
        ax.scatter(scatter_x, scatter_y, scatter_z, s=1, c='black', zorder=200)

        x = []
        y = []
        z = []
        for az in winnowed_az:
            x.append([])
            y.append([])
            z.append([])
            for e in winnowed_e:
                x[-1].append(cos(az) * sin(e))
                y[-1].append(sin(az) * sin(e))
                z[-1].append(0)

        x, y, z = np.array(x), np.array(y), np.array(z)

        ax.plot_surface(x, y, z,
                        linewidth=1, alpha=1, zorder=0)

        ax.set_ylabel("y")
        ax.set_xlabel("x")
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_zticks([])
        ax.axis("off")
        ax.auto_scale_xyz([-0.8, 0.8], [-0.8, 0.8], [0, 1.6])
        plt.show(block=False)
