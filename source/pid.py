class PID:
    kp=1
    ki=1
    kd=1 

    def __init__(self, name):
        self.name = name 

    def forward_pass(self, error, rate):

        integral += error * dt

        p = self.kp * error
        i = self.ki * integral
        d = -self.kd * rate

        correction = p + i + d
        return correction
    