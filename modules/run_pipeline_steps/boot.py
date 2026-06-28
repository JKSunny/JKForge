import subprocess
import threading

from .base import RunPipelineStep

class BootStep(RunPipelineStep):

    def start(self):
        metadata = self.metadata()

        run_dir = self.run_dir()

        launcher = metadata["launcher"]

        # get launcher info
        executable      = launcher["executable"]
        arguments       = launcher["arguments"]
        fs_basegame     = launcher["fs_basegame"]
        qconsole_path   = launcher["qconsole_path"]

        result = self.start_process(
            run_dir,
            executable,
            arguments,
            qconsole_path,
            fs_basegame
        )

        if not result["success"]:
            return result

        runtime = self.active_processes.get(self.run_id, {})

        runtime.update({
            "process"           : result["process"],
            "qconsole_monitor"  : result["qconsole_monitor"]
        })

        metadata["process"]["pid"] = result["pid"]

        self.write_metadata(metadata)

        return {
            "success": True
        }

    def handle_qconsole(self, line):
        if "--- Common Initialization Complete ---" not in line:
            return

        print(f"[{self.run_id}] boot complete")

        self.finish()

    def start_process(
        self,
        run_dir,
        executable,
        arguments,
        qconsole_path,
        fs_basegame
    ):

        exe = run_dir / executable

        if not exe.exists():
            return {
                "success": False,
                "error": f"Executable missing: {executable}"
            }

        try:
            arguments = list(arguments)
   
            arguments.extend([
                "+set", "fs_homepath", str(run_dir)
            ])

            arguments.extend([
                "+set", "logfile", "2"
            ])

            proc = subprocess.Popen(
                [str(exe), *arguments],
                cwd=run_dir,
            )

            qconsole_monitor = threading.Thread(
                target=self.monitor.qconsole_monitor_loop,
                args=(self.env_id, self.run_id, qconsole_path),
                daemon=True
            )

            qconsole_monitor.start()

            return {
                "success": True,
                "pid": proc.pid,
                "process": proc,
                "qconsole_monitor": qconsole_monitor,
                "pipeline"          : self.pipeline
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed starting process: {e}"
            }