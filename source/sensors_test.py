# Vibration test (handoff step 6): run once with MOTOR_POWER = 0, then with
# the heli held or tethered at MOTOR_POWER = 50, and compare the spreads.

import time

import motors
import sensors
from filters import Median3


MOTOR_POWER = 0     # %, both main motors
SECONDS = 5


class Stats:
    # Running mean and spread, without keeping every sample in memory.

    def __init__(self):
        self.count = 0
        self.mean = 0.0
        self._m2 = 0.0

    def add(self, value):
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self._m2 += delta * (value - self.mean)

    def spread(self):
        if self.count == 0:
            return 0.0

        return (self._m2 / self.count) ** 0.5


def show(name, stats, unit):
    print(
        "{:<16} mean={:+10.4f}  spread={:9.4f} {}".format(
            name, stats.mean, stats.spread(), unit
        )
    )


def main():
    motor_left, motor_right = motors.setup_motors()
    vl53, mpu = sensors.setup_sensors()

    names = ("accel X", "accel Y", "accel Z", "gyro X", "gyro Y", "gyro Z")
    channels = [Stats() for _ in names]

    distance_raw = Stats()
    distance_median = Stats()
    height_filter = Median3()

    read_time = Stats()
    slowest_read = 0

    try:
        if MOTOR_POWER > 0:
            print("Motors at", MOTOR_POWER, "%")
            motors.set_power(motor_left, MOTOR_POWER)
            motors.set_power(motor_right, MOTOR_POWER)
            time.sleep(2)  # let the speed settle

        print("Measuring for", SECONDS, "s...")
        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < SECONDS * 1000:
            before = time.ticks_us()
            reading = mpu.read()
            took = time.ticks_diff(time.ticks_us(), before)

            read_time.add(took)
            slowest_read = max(slowest_read, took)

            for i in range(6):
                channels[i].add(reading[i])

            distance = vl53.read_if_ready()

            if distance is not None:
                distance_raw.add(distance)
                distance_median.add(height_filter.update(distance))

            time.sleep_ms(5)

    finally:
        motors.set_power(motor_left, 0)
        motors.set_power(motor_right, 0)
        print("motors off")

    print("\nMotor power:", MOTOR_POWER, "%")

    for i in range(3):
        show(names[i], channels[i], "g")

    for i in range(3, 6):
        show(names[i], channels[i], "deg/s")

    show("distance", distance_raw, "mm")
    show("distance median", distance_median, "mm")

    print(
        "Distance readings: {} ({:.0f} per second)".format(
            distance_raw.count, distance_raw.count / SECONDS
        )
    )

    print(
        "MPU read: {:.0f} us average, {} us slowest".format(
            read_time.mean, slowest_read
        )
    )


if __name__ == "__main__":
    main()
