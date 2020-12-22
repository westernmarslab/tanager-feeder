class PiCommander(Commander):
    def __init__(self, pi_server_ip, listener):
        super().__init__(pi_server_ip, listener)

    def configure(self, i, e, az, pos):
        self.remove_from_listener_queue(['piconfigsuccess'])
        filename = self.encrypt('configure', [i, e, az, pos])
        self.send(filename)
        return filename

    # We may specify either an incidence angle to move to, or a number of steps to move
    def set_incidence(self, num, type='angle'):
        self.remove_from_listener_queue(['donemoving', 'nopiconfig'])
        if type == 'angle':
            incidence = num
            filename = self.encrypt('moveincidence', [incidence])
        else:
            steps = num
            filename = self.encrypt('moveincidence', [steps, 'steps'])
        self.send(filename)
        return filename

    # We may specify either an azimuth angle to move to, or a number of steps to move
    def set_azimuth(self, num, type='angle'):
        self.remove_from_listener_queue(['donemoving', 'nopiconfig'])
        if type == 'angle':
            azimuth = num
            filename = self.encrypt('moveazimuth', [azimuth])
        else:
            steps = num
            filename = self.encrypt('moveazimuth', [steps, 'steps'])
        self.send(filename)
        return filename

    # We may specify either an emission angle to move to, or a number of steps to move
    def set_emission(self, num, type='angle'):
        self.remove_from_listener_queue(['donemoving', 'nopiconfig'])
        if type == 'angle':
            emission = num
            filename = self.encrypt('moveemission', [emission])
        else:
            steps = num
            filename = self.encrypt('moveemission', [steps, 'steps'])
        self.send(filename)
        return filename

    # pos can be either a sample position, or a number of motor steps.

    def move_tray(self, pos, type):
        self.remove_from_listener_queue(['donemoving'])
        if type == 'position':
            positions = {'wr': 'wr', 'Sample 1': 'one', 'Sample 2': 'two', 'Sample 3': 'three', 'Sample 4': 'four',
                         'Sample 5': 'five'}
            if pos in positions:
                filename = self.encrypt('movetray', [positions[pos]])
        else:
            filename = self.encrypt('movetray', [pos, 'steps'])
        self.send(filename)

    def send(self, filename):
        super().send(filename, PI_PORT)