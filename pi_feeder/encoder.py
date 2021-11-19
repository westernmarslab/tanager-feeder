import serial
import time
import numpy as np

SERIAL_PORT_DEFAULT = "COM4"
SERIAL_TIMEOUT_SEC_DEFAULT = 0.1
SERIAL_BAUD = 2 * 1000 * 1000
SERIAL_BYTESIZE = 8
SERIAL_PARITY = "N"
SERIAL_STOPBITS = 1

ENCODER_BASE_DEFAULT = 0x54
ENCODER_READ_CMD_OFFSET = 0
ENCODER_READ_RESPONSE_LEN_BYTES = 2
ENCODER_READ_RESPONSE_MEASUREMENT_BITS = 12
ENCODER_EXTENDED_CMD_OFFSET = 2
ENCODER_RESET_CMD = 0x75
ENCODER_RESET_DELAY_SEC = 0.5
ENCODER_ZERO_CMD = 0x5E
ENCODER_ZERO_DELAY_SEC = 0.5


class AMT212ARotaryEncoder:
    def __init__(
        self,
        port=SERIAL_PORT_DEFAULT,
        timeout=SERIAL_TIMEOUT_SEC_DEFAULT,
        encoder_base=ENCODER_BASE_DEFAULT,
        zero_position=0,
    ):
        self._port = port
        self._timeout_sec = timeout
        self._encoder_base = encoder_base
        self._open_serial_port()
        self._zero_position = zero_position
        # JK added num rotations to encoder as this determines the total number of "full turns".
        # max rotations aren't important to the encoder, only number of rotations.
        self.num_rotations = 0

    def _open_serial_port(self):
        self._serial = serial.Serial(
            self._port,
            timeout=self._timeout_sec,
            baudrate=SERIAL_BAUD,
            bytesize=SERIAL_BYTESIZE,
            parity=SERIAL_PARITY,
            stopbits=SERIAL_STOPBITS,
        )
        self._reset_encoder()

    def _close_serial_port(self):
        self._serial.close()
        self._serial = None

    def _reset_encoder(self):
        cmd = [self._encoder_base + ENCODER_EXTENDED_CMD_OFFSET, ENCODER_RESET_CMD]
        self._serial.write(bytes(cmd))
        self._serial.read(len(cmd))  # Flush out the echoed command.
        time.sleep(ENCODER_RESET_DELAY_SEC)
        self.num_rotations = 0

    def _read_encoder_raw(self):
        self._serial.write(bytes([self._encoder_base + ENCODER_READ_CMD_OFFSET]))
        self._serial.read(1)  # Throw away the echoed command byte.
        response = self._serial.read(ENCODER_READ_RESPONSE_LEN_BYTES + 100)  # Read extra to be sure response is good.
        if len(response) != ENCODER_READ_RESPONSE_LEN_BYTES:
            raise ValueError(
                "Unexpected encoder response length {} -- expected {}".format(
                    len(response), ENCODER_READ_RESPONSE_LEN_BYTES
                )
            )
        raw_value = 0
        for i in range(ENCODER_READ_RESPONSE_LEN_BYTES):
            raw_value += response[i] << (i * 8)
        return raw_value

    def _check_encoder_response_parity(self, response):
        position = response & 0x3FFF
        parity_even = bool((response >> (8 + 6)) & 0x1)
        parity_odd = bool((response >> (8 + 7)) & 0x1)
        odds = position & 0xAAAA
        evens = position & 0x5555

        calc_parity_even = True
        while evens:
            calc_parity_even = not calc_parity_even
            evens = evens & (evens - 1)
        calc_parity_odd = True
        while odds:
            calc_parity_odd = not calc_parity_odd
            odds = odds & (odds - 1)

        if parity_odd != calc_parity_odd or parity_even != calc_parity_even:
            raise ValueError("Parity error in encoder response.")

    # JK added zero encoder command used for AZ, on limit switch.
    # use this to zero encoder and num_rotations when limit switch clicked.
    # sends message to encoder to set zero point as per documentation
    # https://www.cuidevices.com/product/resource/amt21.pdf
    # page 4.
    def zeroize_encoder(self):
        # cmd = [self._encoder_base + ENCODER_EXTENDED_CMD_OFFSET, ENCODER_ZERO_CMD]
        # self._serial.write(bytes(cmd))
        # self._serial.read(len(cmd))  # Flush out the echoed command.
        # time.sleep(ENCODER_ZERO_DELAY_SEC)
        self.configure(0)
        self.num_rotations = 0

    def get_position_degrees(self, num_measurements=1):
        adjusted_position_degrees = []
        for _ in range(num_measurements):
            response = None
            while response is None:
                try:
                    response = self._read_encoder_raw()
                except ValueError:
                    logging.info("Error. Failed to read encoder. Retrying.")
            self._check_encoder_response_parity(response)
            position = (response >> 2) & 0x0FFF  # Throw away the lowest 2 bits for 12-bit encoder.
            position_degrees = 360 * position / 0x0FFF
            adjusted_position_degrees.append((360 + position_degrees - self._zero_position) % 360)
        large_count = 0
        small_count = 0
        for val in adjusted_position_degrees:
            if val > 358:
                large_count += 1
            elif val < 2:
                small_count += 1
        # This looks like the place where % 360 transitions happen on the encoder
        # best place to set rotation rollovers.
        if large_count > 0 and small_count > 0:
            if large_count > small_count:
                for i, val in enumerate(adjusted_position_degrees):
                    if val < 2:
                        adjusted_position_degrees[i] = adjusted_position_degrees[i] + 360
                        self.num_rotations -= 1
            else:
                for i, val in enumerate(adjusted_position_degrees):
                    if val > 358:
                        adjusted_position_degrees[i] = adjusted_position_degrees[i] - 360
                        self.num_rotations += 1

        mean_position = np.mean(adjusted_position_degrees) % 360

        return mean_position

    def configure(self, config_position: int = 0):
        self._zero_position = (self._zero_position + (self.get_position_degrees() - config_position)) % 360
