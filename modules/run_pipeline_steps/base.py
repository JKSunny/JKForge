from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from modules.run import Run
    from modules.run_pipeline import RunPipeline

class RunPipelineStep:
    def __init__(
        self,
        pipeline,
        env_id,
        run_id,
        step_data
    ):
        self.pipeline : 'RunPipeline' = pipeline
        self.run_context : 'Run' = pipeline.run_context

        self.env_id = env_id
        self.run_id = run_id

        self.step_data = step_data
        self.step_id = step_data["id"]

        self.active_processes = pipeline.active_processes
        self.monitor = self.run_context.monitor

    def step(self):
        return self.pipeline.pipeline_metadata["steps"][self.step_id]

    def set_step_status(self, status, error=None):

        step = self.step()

        step["status"] = status

        if status == "running":
            step["started"] = self.run_context.now()

        if status in {"finished", "failed"}:
            step["ended"] = self.run_context.now()

        if error is not None:
            step["error"] = str(error)

        self.sync()

    def ensure_step_details(self):
        step = self.step()

        if "details" not in step:
            step["details"] = {}

        return step["details"]

    def sync_metadata(self):
        self.pipeline.sync_metadata()

    def send_command(self, command):
        return self.run_context.command.send_command(
            self.env_id,
            self.run_id,
            command
        )

    def metadata(self):
        return self.run_context.read_run_metadata(
            self.env_id,
            self.run_id
        )

    def write_metadata(self, metadata):
        self.run_context.write_run_metadata(
            self.env_id,
            self.run_id,
            metadata
        )

    def run_dir(self):
        return self.run_context.run_dir(
            self.env_id,
            self.run_id
        )

    def start(self):
        pass

    def finish(self):
        self.pipeline.finish_step(self.step_id)

    def exit_run(self):
        self.run_context.finish_run(
            self.env_id,
            self.run_id,
            returncode=-0
        )
        
    def update(self):
        pass

    def handle_qconsole(self, line):
        pass