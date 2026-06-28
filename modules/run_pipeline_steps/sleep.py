import time

from .base import RunPipelineStep


class SleepStep(RunPipelineStep):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.duration = 0
        self.started_at = 0

    def start(self):
        input_data = self.step_data.get("input", {})

        self.duration = float(input_data.get("duration", 1))

        self.started_at = time.time()

        return {
            "success": True
        }

    def update(self):
        elapsed = time.time() - self.started_at

        print(f"time elapsted: {elapsed}")

        if elapsed < self.duration:
            return

        self.finish()