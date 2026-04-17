import time

class Chronometer:
    def __init__(self):
        self.start_time = None
        self.stop_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        if self.start_time is None:
            self.stop_time = 0
        else:
            self.stop_time = time.perf_counter()

    def format(self):
        elapsed = self.stop_time - self.start_time
        if elapsed < 1:
            return f"{elapsed * 1000:.2f}ms"  # Milisegundos para scripts rápidos
        return f"{elapsed:.3f}s"             # Segundos para procesos largos