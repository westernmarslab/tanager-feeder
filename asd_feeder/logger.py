import datetime

class Logger:
    def __init__(self):
        self.logfile = ""

    def log_spectrum(self, numspectra, i, e, az, filename, calfile, label):
        if label == "GARBAGE":  # These are about to be deleted. No need to log them.
            return

        if "White reference" in label:
            info_string = "White reference saved."
        else:
            info_string = "Spectrum saved."

        info_string += (
            "\n\tSpectra averaged: "
            + numspectra
            + "\n\ti: "
            + i
            + "\n\te: "
            + e
            + "\n\taz: "
            + az
            + "\n\tSpectralon calibration: "
            + calfile
            + "\n\tData file: "
            + filename
            + "\n\tLabel: "
            + label
            + "\n"
        )

        self.log(info_string)

    def log_opt(self):
        self.log("Instrument optimized.")

    def log(self, info_string):

        datestring = ""
        datestringlist = str(datetime.datetime.now()).split(".")[:-1]
        for d in datestringlist:
            datestring = datestring + d

        while info_string[0] == "\n":
            info_string = info_string[1:]

        space = str(80)
        if "\n" in info_string:
            lines = info_string.split("\n")

            lines[0] = ("{1:" + space + "}{0}").format(datestring, lines[0])
            info_string = "\n".join(lines)
        else:
            info_string = ("{1:" + space + "}{0}").format(datestring, info_string)

        if info_string[-2:-1] != "\n":
            info_string += "\n"

        print(info_string)
        print("\n")
        print(self.logfile)
        with open(self.logfile, "a") as log:
            log.write(info_string)
            log.write("\n")