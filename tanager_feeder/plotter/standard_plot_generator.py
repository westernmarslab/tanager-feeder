import os

import matplotlib.pyplot as plt

from tanager_feeder.plotter.plot import Plot
from tanager_feeder import utils

class StandardPlotGenerator:
    def __init__(self, plot_workbook, dataset_name, file):
        self.plot_workbook = plot_workbook
        self.dataset_name = dataset_name
        self.file = file
        self.samples = []
        for sample in self.plot_workbook.sample_objects:
            if sample.file == self.file:
                self.samples.append(sample)
        self.geoms = {
            "i": [],
            "e": [],
            "az": [],
        }
        for sample in self.samples:
            for geom in sample.geoms:
                i, e, az = utils.get_i_e_az(geom)
                if i not in self.geoms["i"]:
                    self.geoms["i"].append(i)
                if e not in self.geoms["e"]:
                    self.geoms["e"].append(e)
                if az not in self.geoms["az"]:
                    self.geoms["az"].append(az)

    def generate_plots(self, white_reference=True):
        oversize_legend = False
        plot_scale = 1
        plot_width = 150  # in characters
        ylim = None
        xlim = None

        root = os.path.split(self.file)[0]
        save_dir = os.path.join(root, "standard_plots")
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
        if white_reference:
            print(f"Saving standard figures to {save_dir}. White reference included.")
        else:
            print(f"Saving standard figures to {save_dir}. White reference excluded.")
        for az in self.geoms["az"]:
            for i in self.geoms["i"]:
                next_geom_list = {
                    "i": [i],
                    "az": [az],
                    "e": self.geoms["e"]
                }
                print(f"    i = {i}, az = {az}")
                dark_fig = plt.figure(figsize=(9, 5))
                with plt.style.context("default"):
                    white_fig = plt.figure(figsize=(9, 5))
                winnowed_samples = self.plot_workbook.get_winnowed_samples(
                    next_geom_list,
                    self.samples,
                    False,
                    0
                )
                final_winnowed_samples = []
                if not white_reference:
                    for sample in winnowed_samples:
                        if "White Reference" not in sample.name:
                            final_winnowed_samples.append(sample)
                else:
                    final_winnowed_samples = winnowed_samples

                plot = Plot(
                    self.plot_workbook,
                    dark_fig,
                    white_fig,
                    final_winnowed_samples,
                    self.dataset_name,
                    oversize_legend,
                    plot_scale,
                    plot_width,
                    x_axis="wavelength",
                    y_axis="reflectance",
                    xlim=xlim,
                    ylim=ylim,
                    exclude_artifacts=False,
                    draw=False,
                )
                plot.title = f"i = {i}, az = {az}"
                plot.legend_style = "gradient"
                plot.draw()
                if white_reference:
                    filename = os.path.join(save_dir, f"i{int(i)}_az{int(az)}.png")
                else:
                    filename = os.path.join(save_dir, f"i{int(i)}_az{int(az)}_no_ref.png")
                plot.save(white_fig, filename)
                plt.close(white_fig)
                plt.close(dark_fig)


