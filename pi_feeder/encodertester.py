from pi_feeder import encoder
from time import sleep

enc1 = encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x54)
enc1.configure()

enc2 = encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x4C)
enc2.configure()

enc3 = encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x48)
enc3.configure()

enc4 = encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x50)
enc4.configure()

while True:

    posn1 = enc1.get_position_degrees(1)
    print("ang1 ", posn1)

    posn2 = enc2.get_position_degrees(1)
    print("ang2 ", posn2)

    posn3 = enc3.get_position_degrees(1)
    print("ang3 ", posn3)

    posn4 = enc4.get_position_degrees(1)
    print("ang4 ", posn4)

    sleep(0.01)
