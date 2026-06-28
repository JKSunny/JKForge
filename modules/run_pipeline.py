from typing import TYPE_CHECKING

import json
import yaml
from pathlib import Path

from modules.run_pipeline_steps.boot import BootStep
from modules.run_pipeline_steps.exit import ExitStep
from modules.run_pipeline_steps.command import CommandStep
from modules.run_pipeline_steps.sleep import SleepStep
from modules.run_pipeline_steps.demo_queue import DemoQueueStep

if TYPE_CHECKING:
    from modules.run import Run

class RunPipeline:

    def __init__(
        self,
        run_context : 'Run',
        env_id,
        run_id,
        preset
    ):
        self.run_context : 'Run' = run_context

        self.env_id = env_id
        self.run_id = run_id
        self.preset = preset

        self.active_processes = run_context.active_processes
        self.environment = run_context.environment

        self.current_step_instance = None

        self.step_types = {
            "boot"      : BootStep,
            "exit"      : ExitStep,
            "command"   : CommandStep,
            "sleep"     : SleepStep,
            "demo_queue": DemoQueueStep,
        }

        self.pipeline_definition = None
        self.pipeline_metadata = self.init_pipeline(preset)

    def sync_metadata(self):
        metadata = self.run_context.read_run_metadata(
            self.env_id,
            self.run_id
        )

        metadata["pipeline"] = self.pipeline_metadata

        self.run_context.write_run_metadata(
            self.env_id,
            self.run_id,
            metadata
        )

    def init_pipeline(self, preset):
        result = self.load_preset(preset)

        # fallback
        if not result["success"] and preset != "preset_default":
            print(f"[pipeline] failed loading preset '{preset}', using preset_default")

            preset = "preset_default"
            result = self.load_preset(preset)

        if not result["success"]:
            return None

        self.pipeline_definition = result
        runtime_steps = {}

        for step in result["steps"]:
            runtime_steps[step["id"]] = {
                "type": step["type"],
                "status": "pending",
                "started": None,
                "ended": None,
                "error": None
            }

        return {
            "status": "running", # not sure, should be in start_pipeline?
            "started": self.run_context.now(),
            "ended": None,
            "pipeline_preset": preset,
            "current_step": 0,
            "steps": runtime_steps
        }

    def load_preset(self, preset):
        path = self.run_context.pipeline_preset_dir / f"{preset}.yml"

        if not path.exists():
            return {
                "success": False,
                "error": f"Pipeline preset not found: {preset}"
            }

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return {
                "success": True,
                "steps": data.get("steps", []),

                "metadata": {
                    "name": data.get("name"),
                    "description": data.get("description")
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def start_pipeline(self):
        if not self.pipeline_definition:
            return {
                "success": False,
                "error": "Pipeline faield to load"
            }

        steps = self.pipeline_definition["steps"]

        if not steps:
            return {
                "success": False,
                "error": "No pipeline steps"
            }

        runtime = self.active_processes.get(self.run_id)

        if runtime:
            runtime["pipeline"] = self


        return self.start_step(
            steps[0]
        )

    def handle_qconsole(self, line):
        step = self.current_step_instance

        if not step:
            return

        handler = getattr(step, "handle_qconsole", None)

        if handler:
            handler(line)

    def update(self):
        step = self.current_step_instance

        if not step:
            return

        updater = getattr(step, "update", None)

        if updater:
            updater()

    def fail_step(self, step_id, error):
        step = self.pipeline_metadata["steps"].get(step_id)

        if not step:
            return {
                "success": False,
                "error": f"Unknown step: {step_id}"
            }

        # step
        step["status"] = "failed"
        step["ended"] = self.run_context.now()
        step["error"] = str(error)

        # pipeline
        self.pipeline_metadata["status"] = "failed"
        self.pipeline_metadata["ended"] = self.run_context.now()

        self.sync_metadata()

        print(f"[pipeline] step failed: {step_id}: {error}")

        self.run_context.finish_run(
            self.env_id,
            self.run_id,
            returncode=-1
        )

        return {
            "success": False,
            "error": str(error)
        }

    def start_step(self, step_data):
        step_type = step_data["type"]
        step_id = step_data["id"]

        step_class = self.step_types.get(step_type)

        if not step_class:
            self.fail_step(
                step_id,
                f"Unknown pipeline step: {step_type}"
            )
            return False

        # runtime metadata
        step = self.pipeline_metadata["steps"][step_id]
        step["status"] = "running"
        step["started"] = self.run_context.now()
        step["ended"] = None

        self.sync_metadata()

        try:
            step_instance = step_class(
                pipeline=self,
                env_id=self.env_id,
                run_id=self.run_id,
                step_data=step_data
            )

            self.current_step_instance = step_instance

            result = step_instance.start()

            if isinstance(result, dict):
                if not result.get("success", True):
                    return self.fail_step(
                        step_id,
                        result.get("error", "Unknown step failure")
                    )

            return result

        except Exception as e:
            return self.fail_step(step_id, e)

    def finish_step(self, step_id):
        step = self.pipeline_metadata["steps"].get(step_id)

        if not step:
            return

        step["status"] = "finished"
        step["ended"] = self.run_context.now()

        result = self.start_next_step()

        if result == "finished":
            self.pipeline_metadata["status"] = "finished"
            self.pipeline_metadata["ended"] = self.run_context.now()

            # auto stop run after last step finishes:
            # self.run_context.finish_run(
            #     self.env_id,
            #     self.run_id,
            #     returncode=-0
            # )

        self.sync_metadata()

    def start_next_step(self):
        current_index = self.pipeline_metadata["current_step"]

        if not self.pipeline_definition:
            self.fail_step(
                "pipeline",
                "Pipeline definition missing"
            )
            return "failed"

        steps = self.pipeline_definition["steps"]

        next_index = current_index + 1

        if next_index >= len(steps):
            print("[pipeline] finished")
            return "finished"

        self.pipeline_metadata["current_step"] = next_index

        next_step = steps[next_index]

        result = self.start_step(next_step)

        if result is False:
            return "failed"

        return "started"

