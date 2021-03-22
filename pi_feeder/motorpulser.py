from gpiozero import LED, Button
from time import sleep


azimuth_stepdir = LED(17)
azimuth_steppulse = LED(27)
emission_stepdir = LED(22)
emission_steppulse = LED(23)
incidence_stepdir = LED(5)
incidence_steppulse = LED(6)
sample_stepdir = LED(24)
sample_steppulse = LED(25)
runbutton = Button(2)
dirbutton = Button(3)
while True:
    if dirbutton.is_pressed:
        azimuth_stepdir.on()
        emission_stepdir.on()
        incidence_stepdir.on()
        sample_stepdir.on()
    else:
        azimuth_stepdir.off()
        emission_stepdir.off()
        incidence_stepdir.off()
        sample_stepdir.off()

    if runbutton.is_pressed:
        azimuth_steppulse.on()
        emission_steppulse.on()
        incidence_steppulse.on()
        sample_steppulse.on()

        sleep(0.00002)
        azimuth_steppulse.off()
        emission_steppulse.off()
        incidence_steppulse.off()
        sample_steppulse.off()
        sleep(0.00002)
    else:
        azimuth_steppulse.off()
        emission_steppulse.off()
        incidence_steppulse.off()
        sample_steppulse.off()
