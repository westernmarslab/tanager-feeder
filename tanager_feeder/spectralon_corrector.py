import os

import numpy as np

from tanager_data_io.data_io import DataIO

class SpectralonCorrector:

    def __init__(self, spectralon_data_loc):
        self.data_io = DataIO()
        self.spectralon_data_loc = spectralon_data_loc

    def correct(self, data_to_correct_loc):
        self.data_io.load_samples("spectralon", self.spectralon_data_loc, 0)
        self.data_io.load_samples("data to correct", data_to_correct_loc, 0)

        samples_to_write = []
        spectralon = self.data_io.samples["spectralon"][" Spectralon"]
        for sample_name in self.data_io.samples["data to correct"]:
            sample = self.data_io.samples["data to correct"][sample_name]
            for geom in sample.data:
                i, e, az = geom[0], geom[1], geom[2]
                comparison_geom = None
                closest_dist = None
                for spec_geom in spectralon.data:
                    dist = self.get_distance(geom, spec_geom)
                    if closest_dist is None or dist < closest_dist:
                        comparison_geom = spec_geom
                        closest_dist = dist
                avg_spec_value = np.mean(spectralon.data[comparison_geom]["reflectance"])
                sample.data[geom]["reflectance"] = np.array(sample.data[geom]["reflectance"])*avg_spec_value

        for sample_name in self.data_io.samples["data to correct"]:
            samples_to_write.append(self.data_io.samples["data to correct"][sample_name])

        headers = self.data_io.get_headers(data_to_correct_loc)

        self.data_io.write_samples(data_to_correct_loc.strip(".csv")+"_corrected.csv", samples_to_write, headers)

    def get_distance(self, geom1, geom2):
        geom1 = list(geom1)
        geom2 = list(geom2)
        for i in range(2):
            for geom in (geom1, geom2):
                if geom[i] < 0:
                    geom[i] = -1*geom[i]
                    geom[2] = geom[2] + 180
                    if geom[2] >= 360:
                        geom[2] = geom[2] - 360
        dist = np.sqrt((geom1[0]-geom2[0])**2 + (geom1[1]-geom2[1])**2 + (geom1[2]-geom2[2])**2)
        return dist

data_loc = os.path.join(os.path.split(os.path.split(__file__)[0])[0], "data")
spectralon_data_loc = os.path.join(data_loc, "spectralon.csv")
data_to_correct_loc = os.path.join(data_loc, "processed_data\\basalt_3_10.csv")
spectralon_corrector = SpectralonCorrector(spectralon_data_loc)
spectralon_corrector.correct(data_to_correct_loc)