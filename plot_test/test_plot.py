'''
========================
3D surface (solid color)
========================

Demonstrates a very basic plot of a 3D surface using a solid color.
'''

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

size = 15

# Make data
az = np.linspace(0, 2 * np.pi, size)
e = np.linspace(0, np.pi/2, size)
r = []

for i, azimuth in enumerate(az):
    r.append([])
    for emission in e:
        r[i].append(1)

r[5][14] = 1.05
r[5][13] = 1.1
r[5][12] = 1.05

r[4][14] = 1.1
r[4][13] = 1.2
r[4][12] = 1.1

r[3][14] = 1.1
r[3][13] = 1.2
r[3][12] = 1.1

r[2][14] = 1.1
r[2][13] = 1.2
r[2][12] = 1.1

r[1][14] = 1.05
r[1][13] = 1.1
r[1][12] = 1.05

for i in range(size):
    r[i][1] = 0.9
    r[i][0] = 0.8

x = np.outer(np.cos(az), np.sin(e))
y = np.outer(np.sin(az), np.sin(e))
z = np.outer(np.ones(np.size(az)), np.cos(e))

for i, az_group in enumerate(r):
    for j, e_val in enumerate(r[i]):
        x[i][j] = x[i][j]*r[i][j]
        y[i][j] = y[i][j]*r[i][j]
        z[i][j] = z[i][j]*r[i][j]

jet = plt.cm.jet

# Create an empty array of strings with the same shape as the meshgrid, and
# populate it with two colors in a checkerboard pattern.
colortuple = ('y', 'b')
colors = np.empty(x.shape, dtype=str)
colors = []



R = np.sqrt(x**2 + y**2 + z**2)
avg = np.mean(R)
norm = mpl.colors.Normalize(vmin=np.min(R),vmax=np.max(R))

for i in range(size):
    colors.append([])
    for j in range(size):
        val1 = norm(R[i][j])
        if i < size - 1:
            val2 = norm(R[i+1][j])
            if j < size - 1:
                val3 = norm(R[i][j+1])
                val4 = norm(R[i+1][j+1])
            else:
                val3 = norm(R[i][0])
                val4 = norm(R[i+1][0])
        else:
            val2 = norm(R[0][j])
            if j < size - 1:
                val3 = norm(R[i][j + 1])
                val4 = norm(R[0][j + 1])
            else:
                val3 = norm(R[i][0])
                val4 = norm(R[0][0])
        val = 0.25*(val1 + val2 + val3 + val4)
        if val - 0.5 > 0.01:
            print(f"az {i}, e {j}")
            print(np.around(val, 3))
        colors[i].append(jet(val))

# Plot the surface
ax.plot_surface(x, y, z,
    linewidth=1, alpha=1, facecolors=colors)
ax.set_ylabel("y")
ax.set_xlabel("x")
ax.auto_scale_xyz([-1, 1], [-1, 1], [0, 2])
plt.show()
