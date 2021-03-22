from gpiozero import Button
from time import sleep

button = Button(2)
button2 = Button(3)
while True:
    if button.is_pressed:
        print("Pressed")
    else:
        print("Released")
    if button2.is_pressed:
        print("Pressed2")
    else:
        print("Released2")
    sleep(0.1)
