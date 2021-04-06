import os
import time
from tanager_tcp import TanagerServer
from tanager_tcp import TanagerClient
from threading import Thread
from pi_feeder import goniometer


INTERVAL = 0.25
ENCODER_CONFIG_PATH = os.path.join(os.path.split(__file__)[0], "config", "encoder_config.txt")


def main():
    pi_controller = PiController()
    pi_controller.listen()


class PiController:
    def __init__(self):
        self.server = TanagerServer(12345)
        self.client = TanagerClient(self.server.remote_server_address, 12345)

        try:
            with open(ENCODER_CONFIG_PATH, "r") as config_file:
                i_zero = float(config_file.readline())
                e_zero = float(config_file.readline())
                az_zero = float(config_file.readline())
                tray_zero = float(config_file.readline())
                self.goniometer = goniometer.Goniometer(i_zero, e_zero, az_zero, tray_zero)
        except (FileNotFoundError, NotADirectoryError):
            dir_path = os.path.split(ENCODER_CONFIG_PATH)[0]
            print(f"Encoder config file not found, creating new one at {ENCODER_CONFIG_PATH}")
            if not os.path.isdir(dir_path):
                os.mkdir(dir_path)
            self.write_encoder_config(0, 0, 0, 0)
            self.goniometer = goniometer.Goniometer()
        self.goniometer.home_azimuth()

        self.cmdfiles0 = []
        self.dir = "forward"

        thread = Thread(target=self.server.listen)
        thread.start()

    def listen(self):
        print("listening!")
        t = 0
        while True:
            while len(self.server.queue) > 0:
                if self.server.remote_server_address != self.client.server_address:
                    print("Setting control computer address:")
                    self.client.server_address = self.server.remote_server_address
                    print(self.client.server_address)
                message = self.server.queue.pop(0)

                cmd, params = self.decrypt(message)
                for x in range(10):
                    cmd = cmd.replace(str(x), "")
                if cmd != "test":
                    print(cmd)

                if cmd == "movetray":
                    if "steps" in params:
                        steps = int(params[0])
                        self.goniometer.motors["sample tray"]["motor"].move_steps(steps)
                        filename = self.encrypt("donemovingtray")
                    else:
                        status = self.goniometer.set_position("sample tray", params[0])
                        if status["complete"]:
                            filename = self.encrypt("donemovingtray")
                        else:
                            filename = self.encrypt("failuremovingtray" + str(int(status["position"])))
                    self.send(filename)

                elif cmd == "moveemission":
                    if "steps" in params:
                        steps = int(params[0])
                        self.goniometer.motors["emission"]["motor"].move_steps(steps)
                        filename = self.encrypt("donemovingemission")
                    else:
                        if self.goniometer.emission == None:
                            filename = self.encrypt("nopiconfig")
                        else:
                            status = self.goniometer.set_position("emission", int(params[0]))
                            if status["complete"]:
                                filename = self.encrypt("donemovingemission")
                            else:
                                filename = self.encrypt("failuremovingemission" + str(int(status["position"])))
                    self.send(filename)

                elif cmd == "moveincidence":
                    if "steps" in params:
                        steps = int(params[0])
                        self.goniometer.motors["incidence"]["motor"].move_steps(steps)
                        filename = self.encrypt("donemovingincidence")
                    else:
                        if self.goniometer.incidence == None:
                            filename = self.encrypt("nopiconfig")
                        else:
                            status = self.goniometer.set_position("incidence", int(params[0]))
                            if status["complete"]:
                                filename = self.encrypt("donemovingincidence")
                            else:
                                filename = self.encrypt("failuremovingincidence" + str(status["position"]))

                    self.send(filename)

                elif cmd == "moveazimuth":
                    if "steps" in params:
                        steps = int(params[0])
                        self.goniometer.motors["azimuth"]["motor"].move_steps(steps)
                        filename = self.encrypt("donemovingazimuth")
                    if self.goniometer.azimuth == None:
                        filename = self.encrypt("nopiconfig")
                    else:
                        status = self.goniometer.set_position("azimuth", int(params[0]))
                        filename = self.encrypt("donemovingazimuth" + str(int(status["position"])))

                    self.send(filename)

                elif cmd == "configure":
                    if params[2].upper() == "WR":
                        params[2] = -1
                    self.goniometer.configure(float(params[0]), float(params[1]), int(params[2]))
                    self.write_encoder_config(
                        self.goniometer.motors["incidence"]["motor"].encoder._zero_position,
                        self.goniometer.motors["emission"]["motor"].encoder._zero_position,
                        self.goniometer.motors["azimuth"]["motor"].encoder._zero_position,
                        self.goniometer.motors["sample tray"]["motor"].encoder._zero_position,
                    )
                    filename = self.encrypt(
                        "piconfigsuccess",
                        [
                            str(self.goniometer.incidence),
                            str(self.goniometer.emission),
                            str(self.goniometer.azimuth),
                            str(self.goniometer.tray_pos),
                        ],
                    )
                    self.send(filename)
                elif cmd == "getcurrentposition":
                    self.goniometer.move_tray_to_nearest()
                    self.goniometer.update_position()
                    filename = self.encrypt(
                        "currentposition",
                        [
                            str(self.goniometer.incidence),
                            str(self.goniometer.emission),
                            str(self.goniometer.azimuth),
                            str(self.goniometer.tray_pos),
                        ],
                    )
                    self.send(filename)

            t = t + INTERVAL
            time.sleep(INTERVAL)

    def write_encoder_config(self, i, e, az, tray):
        with open(ENCODER_CONFIG_PATH, "w+") as config_file:
            config_file.write(f"{i}\n")
            config_file.write(f"{e}\n")
            config_file.write(f"{az}\n")
            config_file.write(f"{tray}\n")

    def send(self, message):
        sent = self.client.send(message)
        while not sent:
            print("Failed to send message, retrying.")
            print(message)
            sent = self.client.send(message)

    def encrypt(self, cmd, parameters=None):
        filename = cmd
        if parameters:
            for param in parameters:
                param = param.replace("/", "+")
                param = param.replace("\\", "+")
                param = param.replace(":", "=")
                filename = filename + "&" + param
        return filename

    def decrypt(self, encrypted):
        cmd = encrypted.split("&")[0]
        params = encrypted.split("&")[1:]
        i = 0
        for param in params:
            params[i] = param.replace("+", "\\").replace("=", ":")
            params[i] = params[i].replace("++", "+")
            i = i + 1
        return cmd, params


if __name__ == "__main__":
    main()
