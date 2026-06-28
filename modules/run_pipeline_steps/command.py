import subprocess
import threading

from .base import RunPipelineStep

class CommandStep(RunPipelineStep):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.wait_for = None

    def start(self):
        input_data = self.step_data.get("input", {})
        command = input_data.get("command", "gfxinfo")

        metadata = self.metadata()

        try:
            result = self.run_context.command.send_command(
                self.env_id,
                self.run_id,
                command
            )

            if not self.wait_for:
                self.finish()

            return {
                "success": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def handle_qconsole(self, line):
        if not self.wait_for:
            return

        if self.wait_for not in line:
            return

        self.finish()