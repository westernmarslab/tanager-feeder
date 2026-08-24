import time
from pywinauto import Application, keyboard, findwindows, Desktop

def main():
    helper = PywinautoFrameHelper(
        r"C:\Program Files (x86)\ASD\RS3\RS3.exe"
    )
    helper.start_RS3()
    time.sleep(10)
    helper.draw_outlines()


class PywinautoFrameHelper:
    def __init__(self, RS3_loc):
        self.RS3_loc = RS3_loc

    def start_RS3(self):
        self.app = Application().start(self.RS3_loc)
        self.spec = None
        self.spec_connected = False
        while True:
            print("Waiting for RS3 to come back...")
            try:
                self.spec = self.app.ThunderRT6Form
                break
            except:
                time.sleep(1)
        print("Started RS3.")

    def draw_outlines(self):
        frames = self.spec.descendants(class_name="ThunderRT6Frame")
        self.spec.print_control_identifiers()


        colors = [
            "red",
            "green",
            "blue",
        ]

        frames_of_interest = []
        frame_numbers = []
        for i, frame in enumerate(frames):
            if frame.rectangle().left == 14 and frame.rectangle().top in [378]: #[378, 484, 608]:
                frames_of_interest.append(frame)
                frame_numbers.append(i)

        for i, frame in enumerate(frames_of_interest):
            print(
                f"Frame {frame_numbers[i]}: ({colors[i % len(colors)]}",
                frame.rectangle(),
                repr(frame.window_text()),
                "handle=", frame.handle
            )
        while True:
            for i, frame in enumerate(frames_of_interest):
                frame.draw_outline(
                    colour=colors[i % len(colors)],
                    thickness=i
                )


if __name__ == "__main__":
    main()