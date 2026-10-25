from machine import Pin, I2C  # pyright: ignore[reportMissingImports]
from mpu6050 import MPU6050
from settings import config, save
import time


SAMPLES = 500


def collect(mpu):
    sums = [0.0] * 6
    squares = [0.0] * 6

    for _ in range(SAMPLES):
        values = mpu.read_raw()

        for i in range(6):
            sums[i] += values[i]
            squares[i] += values[i] ** 2

        time.sleep_ms(15)

    means = [value / SAMPLES for value in sums]

    spread = [
        max(0.0, squares[i] / SAMPLES - means[i] ** 2) ** 0.5
        for i in range(6)
    ]

    return means, spread


def calibrate():
    i2c = I2C(
        0,
        sda=Pin(config["pins"]["sda"]),
        scl=Pin(config["pins"]["scl"]),
        freq=config["parameters"]["i2c_frequency"]
    )

    mpu = MPU6050(i2c)

    print("Leave the assembly still while it settles.")
    print("Waiting 5 seconds...")
    time.sleep(5)

    # Gyroscope calibration: any stationary orientation.
    while True:
        print("Settling...")
        time.sleep(2)
        print("Measuring. Do not move it.")

        means, spread = collect(mpu)

        print("Gyro spread [deg/s]:", spread[3:])

        # Practical screening thresholds, not manufacturer limits.
        if max(spread[:3]) > 0.05 or max(spread[3:]) > 1.0:
            print("Too much movement or noise. Please retry.")
            continue

        gyro_bias = means[3:]
        print("Gyro offsets [deg/s]:", gyro_bias)
        break

    positions = (
        ("X+", 0, 1),
        ("X-", 0, -1),
        ("Y+", 1, 1),
        ("Y-", 1, -1),
        ("Z+", 2, 1),
        ("Z-", 2, -1)
    )

    measurements = {}

    for label, axis, sign in positions:
        while True:
            direction = "UP" if sign > 0 else "DOWN"

            print(
                "\n{}: point positive {} vertically {}.".format(
                    label, "XYZ"[axis], direction
                )
            )

            input("Position it securely, then press Enter.")

            preview = mpu.read_raw()[:3]
            print(
                "Preview [g]: X={:.3f}, Y={:.3f}, Z={:.3f}".format(
                    *preview
                )
            )

            answer = input(
                "Enter = measure; r + Enter = reposition: "
            )

            if answer.strip().lower() == "r":
                continue

            print("Settling...")
            time.sleep(2)
            print("Measuring. Do not move it.")

            means, spread = collect(mpu)
            accel = means[:3]

            print("Average acceleration [g]:", accel)

            if max(spread[:3]) > 0.05 or max(spread[3:]) > 1.0:
                print("Too much movement or noise. Retry.")
                continue

            # Broad orientation checks before calibration.
            correct_axis = 0.5 < sign * accel[axis] < 1.5
            other_axes_small = all(
                abs(accel[i]) < 0.4
                for i in range(3)
                if i != axis
            )

            if not correct_axis or not other_axes_small:
                print("Orientation looks incorrect. Retry.")
                continue

            measurements[label] = accel
            break

    accel_bias = []
    accel_scale = []

    for axis, name in enumerate("XYZ"):
        positive = measurements[name + "+"][axis]
        negative = measurements[name + "-"][axis]

        bias = (positive + negative) / 2.0
        scale = (positive - negative) / 2.0

        if not 0.5 < scale < 1.5:
            raise ValueError(
                "Unexpected {} scale; calibration not saved.".format(
                    name
                )
            )

        accel_bias.append(bias)
        accel_scale.append(scale)

    calibration = {
        "gyro_bias_dps": gyro_bias,
        "accel_bias_g": accel_bias,
        "accel_scale": accel_scale,
        "temperature_c": mpu.read_temperature()
    }

    # Only the calibration entry changes; Wi-Fi, pins and parameters stay.
    config["mpu_calibration"] = calibration
    save()

    print("\nCalibration saved to config.json.")
    print("Gyro offsets [deg/s]:", gyro_bias)
    print("Accel offsets [g]:", accel_bias)
    print("Accel scale factors:", accel_scale)


if __name__ == "__main__":
    calibrate()