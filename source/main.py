import time

import motors
import sensors
from filters import LowPass, Median3


LOOP_HZ = 200
MAX_DT = 0.02           # s; one slow loop can't make an integral jump
MAX_HEIGHT_DT = 0.1     # s; the distance sensor gives ~30 readings per second
HEIGHT_TARGET = 500     # mm


def main():
    # Motors first, so they sit at 0% as early as possible.
    motor_left, motor_right = motors.setup_motors()
    vl53, mpu = sensors.setup_sensors()

    height_filter = Median3()
    speed_filter = LowPass(0.3)

    # Your part: create the PIDs (yaw rate, altitude).

    armed = False       # Set by the arm command, once the Wi-Fi link exists.
    throttle = 0.0      # %, both main motors
    yaw = 0.0           # %, difference between the main motors

    height = None       # mm, filtered
    speed = 0.0         # mm/s, + = going up
    height_time = time.ticks_us()

    period_us = 1000000 // LOOP_HZ
    last = time.ticks_us()
    next_loop = last

    loops = 0
    report_time = time.ticks_ms()

    try:
        while True:
            now = time.ticks_us()
            dt = min(time.ticks_diff(now, last) / 1000000, MAX_DT)
            last = now

            ax, ay, az, gx, gy, gz = mpu.read()

            # A new distance only comes ~30 times a second.
            distance = vl53.read_if_ready()

            if distance is not None:
                new_height = height_filter.update(distance)
                height_dt = min(time.ticks_diff(now, height_time) / 1000000, MAX_HEIGHT_DT)

                if height is not None:
                    speed = speed_filter.update((new_height - height) / height_dt)

                height = new_height
                height_time = now

                # Your part: altitude PID
                #   error = HEIGHT_TARGET - height, rate = speed, dt = height_dt
                #   -> throttle

            # Your part: yaw-rate PID
            #   error = 0 - gz, dt = dt
            #   -> yaw

            if armed:
                # Your part: mixer
                #   motors.set_power(motor_left, throttle + yaw)
                #   motors.set_power(motor_right, throttle - yaw)
                pass
            else:
                motors.set_power(motor_left, 0)
                motors.set_power(motor_right, 0)

                # Your part: reset the PIDs, so the integral can't wind up on the ground.

            loops += 1

            if time.ticks_diff(time.ticks_ms(), report_time) >= 1000:
                print(
                    "{} loops/s  height {} mm  speed {:+.0f} mm/s  yaw rate {:+.1f} deg/s".format(
                        loops, height, speed, gz
                    )
                )
                loops = 0
                report_time = time.ticks_ms()

            # Wait for the next loop, so dt stays steady.
            next_loop = time.ticks_add(next_loop, period_us)
            wait = time.ticks_diff(next_loop, time.ticks_us())

            if wait > 0:
                time.sleep_us(wait)
            else:
                next_loop = time.ticks_us()  # fell behind, count again from now

    finally:
        motors.set_power(motor_left, 0)
        motors.set_power(motor_right, 0)
        print("motors off")


if __name__ == "__main__":
    main()
