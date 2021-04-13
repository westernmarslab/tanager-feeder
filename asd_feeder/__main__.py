import os

from asd_feeder.spec_compy_controller import SpecCompyController


def main():
    computer = "desktop"
    computer = "new"
    home_loc = os.path.expanduser("~")
    temp_data_loc = os.path.join(home_loc,"Tanager", "temp_data")
    if not os.path.isdir(temp_data_loc):
        print(f"Creating temporary data directory at {temp_data_loc}")
        os.makedirs(temp_data_loc)

    data_loc = os.path.join(os.path.split(__file__)[0], "spectralon_data")
    spectralon_data_loc = os.path.join(data_loc, "spectralon.csv")
    print(spectralon_data_loc)

    RS3_loc = ""
    ViewSpecPro_loc = ""

    if computer == "old":
        RS3_loc = r"C:\Program Files\ASD\RS3\RS3.exe"
        ViewSpecPro_loc = r"C:\Program Files\ASD\ViewSpecPro\ViewSpecPro.exe"

    elif computer == "new":
        RS3_loc = r"C:\Program Files (x86)\ASD\RS3\RS3.exe"
        ViewSpecPro_loc = r"C:\Program Files (x86)\ASD\ViewSpecPro\ViewSpecPro.exe"

    elif computer == "desktop":
        RS3_loc = r"C:\Program Files (x86)\ASD\RS3\RS3.exe"
        ViewSpecPro_loc = r"C:\Program Files (x86)\ASD\ViewSpecPro\ViewSpecPro.exe"

    controller = SpecCompyController(temp_data_loc, spectralon_data_loc, RS3_loc, ViewSpecPro_loc, computer)
    controller.listen()

if __name__ == "__main__":
    main()
