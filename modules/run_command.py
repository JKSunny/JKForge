from typing import TYPE_CHECKING

from pathlib import Path
import json

if TYPE_CHECKING:
    from modules.run import Run

class RunCommand:
    def __init__(self, run_context : 'Run'):
        self.run_context : 'Run' = run_context
        self.environment = run_context.environment

    def run_command_path(self, env_id, run_id):
        return self.run_context.run_dir(env_id, run_id) / "jkforge_cmd.txt"

    def write_run_command(self, env_id, run_id, command: str):
        cmd_file = self.run_command_path(env_id, run_id)
        cmd_file.parent.mkdir(parents=True, exist_ok=True)  # ensure run_dir exists

        with open(cmd_file, "a", encoding="utf-8") as f:
            f.write(command.strip() + "\n")

    def send_command(self, env_id, run_id, command: str):
        try:
            self.write_run_command(env_id, run_id, command)
            return {
                "success": True
            }
        except Exception as e:
            print(f"[send_command] {e}")
            return {
                "success": False, 
                "error": str(e)
           }