import struct
import time


class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr

        # Made once, reused by every read.
        self._buffer = bytearray(14)

        # No correction until set_calibration() is called.
        self.accel_bias_g = (0.0, 0.0, 0.0)
        self.accel_scale = (1.0, 1.0, 1.0)
        self.gyro_bias_dps = (0.0, 0.0, 0.0)

        identity = self.i2c.readfrom_mem(
            self.addr, 0x75, 1
        )[0]

        if identity != 0x68:
            raise RuntimeError(
                "Unexpected MPU6050 identity: {}".format(
                    hex(identity)
                )
            )

        # Reset, then wake using the X-gyro PLL clock.
        self._write(0x6B, 0x80)
        time.sleep_ms(100)
        self._write(0x6B, 0x01)
        time.sleep_ms(100)

        self._write(0x1B, 0x00)  # Gyro: +/-250 deg/s
        self._write(0x1C, 0x00)  # Acceleration: +/-2 g
        self._write(0x1A, 0x04)  # About 20 Hz low-pass filter
        self._write(0x19, 4)     # 200 Hz output sample rate

        time.sleep_ms(100)

    def _write(self, register, value):
        self.i2c.writeto_mem(
            self.addr, register, bytes([value])
        )

    def set_calibration(self, calibration):
        # calibration: the "mpu_calibration" entry of config.json
        self.accel_bias_g = tuple(calibration["accel_bias_g"])
        self.accel_scale = tuple(calibration["accel_scale"])
        self.gyro_bias_dps = tuple(calibration["gyro_bias_dps"])

    def zero_gyro(self, samples=300, max_spread_dps=0.5):
        # Measures the gyro bias fresh. The sensor must sit still.
        # Returns False, and keeps the old bias, if it moved.
        sums = [0.0] * 3
        squares = [0.0] * 3

        for _ in range(samples):
            gyro = self.read_raw()[3:]

            for i in range(3):
                sums[i] += gyro[i]
                squares[i] += gyro[i] ** 2

            time.sleep_ms(5)

        means = [value / samples for value in sums]

        spread = max(
            max(0.0, squares[i] / samples - means[i] ** 2) ** 0.5
            for i in range(3)
        )

        if spread > max_spread_dps:
            return False

        self.gyro_bias_dps = tuple(means)
        return True

    def read_raw(self):
        # (ax, ay, az) in g and (gx, gy, gz) in deg/s, no calibration
        self.i2c.readfrom_mem_into(
            self.addr, 0x3B, self._buffer
        )

        ax, ay, az, _, gx, gy, gz = struct.unpack_from(
            ">7h", self._buffer
        )

        return (
            ax / 16384.0,
            ay / 16384.0,
            az / 16384.0,
            gx / 131.0,
            gy / 131.0,
            gz / 131.0
        )

    def read(self):
        # Same as read_raw(), with the calibration applied
        ax, ay, az, gx, gy, gz = self.read_raw()

        bias = self.accel_bias_g
        scale = self.accel_scale
        gyro_bias = self.gyro_bias_dps

        return (
            (ax - bias[0]) / scale[0],
            (ay - bias[1]) / scale[1],
            (az - bias[2]) / scale[2],
            gx - gyro_bias[0],
            gy - gyro_bias[1],
            gz - gyro_bias[2]
        )

    def read_temperature(self):
        data = self.i2c.readfrom_mem(
            self.addr, 0x41, 2
        )

        return struct.unpack(">h", data)[0] / 340.0 + 36.53
