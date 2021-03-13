import numpy as np

from tanager_feeder.plotter.sample import Sample

class DataIO:
    def __init__(self):
        self.samples = {}
        self.sample_objects = []

    def load_samples(self, dataset_name, file):
        try:
            wavelengths, reflectance, labels = self.read_csv(file)
        except OSError:
            return False

        if dataset_name not in self.samples:
            self.samples[dataset_name] = {}

        for i, spectrum_label in enumerate(labels):
            sample_label = spectrum_label.split(" (i")[0]

            # Check if we've already got the sample in question in the dataset.
            # If it doesn't exist, make it. If it does, just add this spectrum and label into its data
            # dictionary.
            sample_exists = False
            for sample in self.samples[dataset_name]:
                if self.samples[dataset_name][sample].name == sample_label:
                    sample_exists = True

            if not sample_exists:
                new = Sample(sample_label, file, dataset_name)
                self.samples[dataset_name][sample_label] = new
                self.sample_objects.append(new)

            # if spectrum_label not in self.samples[dataset_name][sample_label].geoms: #This should do better and actually
            # check that all the data is an exact duplicate, but that seems hard. Just don't label things exactly the
            # same and save them in the same file with the same viewing geometry.
            spectrum_label = spectrum_label.replace(")", "").replace("(", "")
            if "i=" in spectrum_label.replace(" ", ""):
                incidence = float(spectrum_label.split("i=")[1].split(" ")[0])
            else:
                incidence = None
            if "e=" in spectrum_label.replace(" ", ""):
                emission = float(spectrum_label.split("e=")[1].split(" ")[0])
            else:
                emission = None
            if "az=" in spectrum_label.replace(" ", ""):
                azimuth = float(spectrum_label.split("az=")[1])
            else:
                azimuth = None
            geom = (incidence, emission, azimuth)
            self.samples[dataset_name][sample_label].add_spectrum(geom, reflectance[i], wavelengths)

        return True

    @staticmethod
    def read_csv(file, file_format="spectral_database_csv", skip_vals = 60):
        labels = []
        # This is the format I was initially using. It is a simple .tsv file with a single row of headers
        # e.g. Wavelengths     Sample_1 (i=0 e=30)     Sample_2 (i=0 e=30).
        if file_format == "simple_tsv":
            data = np.genfromtxt(file, names=True, dtype=float, encoding=None, delimiter="\t", deletechars="")
            labels = list(data.dtype.names)[1:]  # the first label is wavelengths
            for i, label in enumerate(labels):
                labels[i] = label.replace("_(i=", " (i=").replace("_e=", " e=").replace("( i", "(i")
        # This is the current format, which is compatible with the WWU spectral library format.
        elif file_format == "spectral_database_csv":
            skip_header = 1

            labels_found = False  # We want to use the Sample Name field for labels, but if we haven't found
            # that yet we may use Data ID, Sample ID, or mineral name instead.
            with open(file, "r") as file2:
                line = file2.readline()
                i = 0
                while (
                    line.split(",")[0].lower() != "wavelength" and line != "" and line.lower() != "wavelength\n"
                ):  # Formatting can change slightly if you edit your .csv in libreoffice or some other editor,
                    # this captures different options. line will be '' only at the end of the file (it is \n for
                    # empty lines)
                    i += 1
                    if line[0:11].lower() == "sample name":
                        labels = line.split(",")[1:]
                        labels[-1] = labels[-1].strip("\n")
                        labels_found = True  #
                    elif line[0:16].lower() == "viewing geometry":
                        for i, geom in enumerate(line.split(",")[1:]):
                            geom = geom.strip("\n").replace(" i", "i")
                            labels[i] += " (" + geom + ")"
                    elif line[0:7].lower() == "data id":
                        if not labels_found:  # Only use Data ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    elif line[0:9].lower() == "sample id":
                        if not labels_found:  # Only use Sample ID for labels if we haven't found the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    elif line[0:12].lower() == "mineral name":
                        if not labels_found:  # Only use mineral ID for labels if we haven't found
                            # the Sample Name field.
                            labels = line.split(",")[1:]
                            labels[-1] = labels[-1].strip("\n")
                    skip_header += 1
                    line = file2.readline()
        try:
            data = np.genfromtxt(
                file, skip_header=skip_header, dtype=float, delimiter=",", encoding=None, deletechars=""
            )
        except ValueError as e:
            raise e

        data = zip(*data)
        wavelengths = []
        reflectance = []
        for i, d in enumerate(data):
            if i == 0 and len(d) > 500:
                wavelengths = d[
                    skip_vals:
                ]  # the first column in my .csv (now first row) was wavelength in nm. Exclude the first 60 values
                # because they are typically very noisy.
            elif i == 0:
                wavelengths = d
            elif len(d) > 500:  # the other columns are all reflectance values
                d = np.array(d)
                reflectance.append(d[skip_vals:])
            else:
                d = np.array(d)
                reflectance.append(d)
        return wavelengths, reflectance, labels

    def get_headers(self, file):
        headers = []
        with open(file, "r") as f:
            line = f.readline().strip("\n")
            headers.append(line)
            while line.split(",")[0].lower() != "wavelength" and line != "" and line.lower() != "wavelength\n":
                line = f.readline().strip("\n")
                headers.append(line)
        return headers


    def write_samples(self, file, samples, headers):
        for j, line in enumerate(headers):
            line = line.split(",")
            if line[0] == "Viewing Geometry" or line[0] == "Sample Name":
                headers[j] = [line[0]]
            else:
                headers[j] = line
        corrected_data = []
        for sample in samples:
            for geom in sample.geoms:
                i, e, az = str(geom[0]), str(geom[1]), str(geom[2])
                n = 1
                for j, line in enumerate(headers):
                    if len(line) == 0:
                        continue
                    if line[0] == "Viewing Geometry":
                        line.append("i=" + i + " e=" + e + " az=" + az)
                    elif line[0] == "Sample Name":
                        line.append(sample.name)

                if corrected_data == []:
                    corrected_data.append(sample.data[geom]["wavelength"])
                elif corrected_data[0] != sample.data[geom]["wavelength"]:
                    raise Exception("Samples do not have data at the same wavelengths.")
                corrected_data.append(sample.data[geom]["reflectance"])


        for j, line in enumerate(headers):
            headers[j] = ",".join(line)

        with open(file, "w+") as f:
            for line in headers:
                f.write(line+"\n")
            data_lines = zip(*corrected_data)
            for line in data_lines:
                line = [str(val) for val in line]
                line = ",".join(line)
                f.write(line+"\n")

    @staticmethod
    def get_index(array, val):
        index = (np.abs(array - val)).argmin()
        return index