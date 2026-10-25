from machine import Pin, I2C  # pyright: ignore[reportMissingImports]

from settings import config
from vl53l0x import VL53L0X
from mpu6050 import MPU6050


def setup_sensors():

    i2c = I2C(
        0,
        sda=Pin(config["pins"]["sda"]),
        scl=Pin(config["pins"]["scl"]),
        freq=config["parameters"]["i2c_frequency"]
    )

    print("Found:", [hex(address) for address in i2c.scan()])

    # With a timeout, a stuck sensor raises an error instead of freezing the loop.
    vl53 = VL53L0X(i2c, io_timeout_ms=100)
    vl53.start_continuous()

    #vl53.measurement_timing_budget = 100000

    mpu = MPU6050(i2c)
    mpu.set_calibration(config["mpu_calibration"])

    # Fresh gyro bias at every start: it drifts with temperature.
    print("Keep still: measuring gyro bias...")

    while not mpu.zero_gyro():
        print("Moved, measuring again...")

    return vl53, mpu
