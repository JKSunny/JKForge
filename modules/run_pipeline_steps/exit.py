import subprocess
import threading

from .base import RunPipelineStep

class ExitStep(RunPipelineStep):

    def start(self):
        self.finish()
        self.exit_run()

        return {
            "success": True
        }
