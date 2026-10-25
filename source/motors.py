from machine import Pin, PWM  # pyright: ignore[reportMissingImports]

from settings import config


def setup_motors():
    motor_pwm_frequency = config["parameters"]["motor_pwm_frequency"]

    # Motor off at every boot. The pull-down keeps it off until this line runs.
    motor_left = PWM(Pin(config["pins"]["motor_left"]), freq=motor_pwm_frequency, duty_u16=0)
    motor_right = PWM(Pin(config["pins"]["motor_right"]), freq=motor_pwm_frequency, duty_u16=0)

    return motor_left, motor_right


def set_power(motor, percent):
    # A PID can ask for less than 0% or more than 100%.
    percent = min(max(percent, 0), 100)

    # duty_u16 goes from 0 (off) to 65535 (full on)
    motor.duty_u16(int(percent * 65535 / 100))
