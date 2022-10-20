from pi_feeder import limit_switch

switch_1 = limit_switch.LimitSwitch("Switch 1", 2)
switch_2 = limit_switch.LimitSwitch("Switch 2", 3)

switch_1_tripping = False
switch_2_tripping = False

while True:
    if switch_1.get_tripped() and not switch_1_tripping:
        print("Switch 1 tripped")
        switch_1_tripping = True
    if not switch_1.get_tripped():
        switch_1_tripping = False

    if switch_2.get_tripped() and not switch_2_tripping:
        print("Switch 2 tripped")
        switch_2_tripping = True
    if not switch_2.get_tripped():
        switch_2_tripping = False
