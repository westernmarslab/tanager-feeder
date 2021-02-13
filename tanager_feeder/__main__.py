# The controller runs the main thread controlling the program.
# It opens a Tkinter GUI with options for instrument control parameters and sample configuration
# The user can use the GUI to operate the goniometer motors and the spectrometer software.

import ctypes
import os
import platform
import sys

from tanager_feeder.controller import Controller
from tanager_feeder import utils
from tanager_feeder.connection_checkers.pi_connection_checker import PiConnectionChecker
from tanager_feeder.connection_checkers.spec_connection_checker import SpecConnectionChecker


def main():
    # Figure out where this file is hanging out and tell python to look there for custom modules. This will depend on
    # what operating system you are using.
    opsys: str = platform.system()
    if opsys == "Darwin":
        opsys = "Mac"  # For some reason Macs identify themselves as Darwin. I don't know why but I think this is more
        # intuitive.

    if opsys == "Windows":
        # Note that if running this script from an IDE, __file__ may not be defined.
        rel_package_loc = "\\".join(__file__.split("\\")[:-1]) + "\\"
        if "c:" in rel_package_loc.lower():
            package_loc = rel_package_loc
        else:
            package_loc = os.getcwd() + "\\" + rel_package_loc

    elif opsys == "Linux":
        rel_package_loc = "/".join(__file__.split("/")[:-1]) + "/"
        if rel_package_loc[0] == "/":
            package_loc = rel_package_loc
        else:
            package_loc = os.getcwd() + "/" + rel_package_loc

    elif opsys == "Mac":
        rel_package_loc = "/".join(__file__.split("/")[:-1]) + "/"
        if rel_package_loc[0] == "/":
            package_loc = rel_package_loc
        else:
            package_loc = os.getcwd() + "/" + rel_package_loc

    sys.path.append(package_loc)

    home_loc = os.path.expanduser("~")

    if opsys == "Linux":
        x11 = ctypes.cdll.LoadLibrary("libX11.so")
        x11.XInitThreads()

        home_loc += "/"
        local_config_loc = home_loc + ".tanager_config/"  # package_loc+'local_config/'
        global_config_loc = package_loc + "global_config/"

    elif opsys == "Windows":
        home_loc += "\\"
        local_config_loc = home_loc + ".tanager_config\\"  # package_loc+'local_config\\'
        global_config_loc = package_loc + "global_config\\"

    elif opsys == "Mac":
        home_loc += "/"
        local_config_loc = home_loc + ".tanager_config/"  # package_loc+'local_config/'
        global_config_loc = package_loc + "global_config/"

    if not os.path.isdir(local_config_loc):
        print("Attempting to make config directory:")
        print(local_config_loc)
        os.mkdir(local_config_loc)

    try:
        with open(local_config_loc + "ip_addresses.txt", "r") as ip_config:
            spec_ip = ip_config.readline().strip("\n")
            pi_ip = ip_config.readline().strip("\n")
        connection_tracker = utils.ConnectionTracker(spec_ip, pi_ip)
    except FileNotFoundError:
        print("Failed to load ip config.")
        with open(local_config_loc + "ip_addresses.txt", "w+") as ip_config:
            ip_config.write("spec_compy_ip\n")
            ip_config.write("raspberrypi")
        connection_tracker = utils.ConnectionTracker()

    icon_loc = package_loc + "exception"  # eventually someone should make this icon thing work. I haven't!
    config_info = utils.ConfigInfo(local_config_loc, global_config_loc, icon_loc, utils.NUMLEN, opsys)

    check_spec_connection(connection_tracker, config_info)


def check_spec_connection(connection_tracker, config_info):
    # Check if you are connected to the server. If not, put up dialog box and wait. If you are connected,
    # go on to checking pi connection.
    spec_connection_checker = SpecConnectionChecker(
        connection_tracker, config_info, func=check_pi_connection, args=[connection_tracker, config_info]
    )
    print("Checking spectrometer computer connection...")
    connected = spec_connection_checker.check_connection()
    if not connected:
        connection_tracker.spec_offline = True
        print("Not connected")


# repeat check for raspi
def check_pi_connection(connection_tracker, config_info):
    pi_connection_checker = PiConnectionChecker(
        connection_tracker, config_info, func=launch, args=[connection_tracker, config_info]
    )
    print("Checking raspberry pi connection...")
    connected = pi_connection_checker.check_connection()
    if not connected:
        connection_tracker.pi_offline = True
        print("Not connected")


def launch(connection_tracker, config_info):
    # Create a listener, which listens for commands, and a controller, which manages the model (which writes commands)
    # and the view.
    Controller(connection_tracker, config_info)


if __name__ == "__main__":
    main()
