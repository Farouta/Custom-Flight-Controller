# Each signal gets its own filter object, created once at setup,
# so the filter keeps its own memory between loops.


class Median3:
    # Median of the last 3 readings. Throws away a single bad reading,
    # costs about one reading of delay.

    def __init__(self):
        self.values = []

    def update(self, value):
        self.values.append(value)

        if len(self.values) > 3:
            self.values.pop(0)

        return sorted(self.values)[len(self.values) // 2]


class LowPass:
    # Exponential average. alpha from 0 to 1: smaller = smoother but later.

    def __init__(self, alpha):
        self.alpha = alpha
        self.value = None

    def update(self, value):
        if self.value is None:
            self.value = value
        else:
            self.value += self.alpha * (value - self.value)

        return self.value
