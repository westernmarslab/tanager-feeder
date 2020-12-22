AZIMUTH_HOME = 0
INTERVAL=0.25


class ConnectionTracker:
    PI_PORT = 12345
    SPEC_PORT = 54321

    def __init__(self, spec_ip = '192.168.86.50', pi_ip = 'raspberrypi'):
        self.spec_offline = False
        self.pi_offline = False
        self.spec_ip = spec_ip
        self.pi_ip = pi_ip


class ConfigInfo:

    def __init__(self, local_config_loc, global_config_loc, icon_loc, opsys):
        self.local_config_loc = local_config_loc
        self.globabl_config_loc = global_config_loc
        self.icon_loc = icon_loc
        self.opsys = opsys

#Which spectrometer computer are you using? This should probably be desktop, but could be 'new' for the new lappy or 'old' for the ancient laptop.
computer='desktop'
computer='new'

def limit_len(input, max):
    return input[:max]


def validate_int_input(input, min, max):
    try:
        input = int(input)
    except:
        return False
    if input > max: return False
    if input < min: return False
    return True


def decrypt(encrypted):
    cmd = encrypted.split('&')[0]
    params = encrypted.split('&')[1:]
    i = 0
    for param in params:
        params[i] = param.replace('+', '\\').replace('=', ':')
        params[i] = params[i].replace('++', '+')
        i = i + 1
    return cmd, params

def rm_reserved_chars(input):
    output = input.replace('&', '').replace('+', '').replace('=', '').replace('$', '').replace('^', '').replace('*',
                                                                                                                '').replace(
        '(', '').replace(',', '').replace(')', '').replace('@', '').replace('!', '').replace('#', '').replace('{',
                                                                                                              '').replace(
        '}', '').replace('[', '').replace(']', '').replace('|', '').replace(',', '').replace('?', '').replace('~',
                                                                                                              '').replace(
        '"', '').replace("'", '').replace(';', '').replace('`', '')
    return output

def numbers_only(input):
    output = ''
    for digit in input:
        if digit == '1' or digit == '2' or digit == '3' or digit == '4' or digit == '5' or digit == '6' or digit == '7' or digit == '8' or digit == '9' or digit == '0':
            output += digit
    return output