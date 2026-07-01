from typing import TYPE_CHECKING

from pathlib import Path
import os
import shutil
import subprocess
import uuid
from datetime import datetime
import json
import yaml

if TYPE_CHECKING:
    from main import JKForge

from modules.run_command import RunCommand
from modules.run_monitor import RunMonitor
from modules.run_pipeline import RunPipeline

import threading

class Run:
    def __init__(self, context : 'JKForge'):
        self.context    : 'JKForge' = context
        self.environment = context.environment
        self.config = context.config

        self.active_processes = {}

        self.preset_dir = Path( self.config.resource_path("static/run_presets"))
        self.pipeline_preset_dir = Path(self.config.resource_path("static/run_pipeline_presets"))

        # submodules
        self.command = RunCommand(self)
        self.monitor = RunMonitor(self)


    def now(self):
        return datetime.now().isoformat()

    def create_run_id(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        rand = str(uuid.uuid4())[:6]

        return f"{ts}_{rand}"

    def runs_dir(self, env_id):
        return self.environment.env_dir(env_id) / "runs"

    def run_dir(self, env_id, run_id):
        return self.runs_dir(env_id) / run_id

    def run_metadata_path(self, env_id, run_id):
        return self.run_dir(env_id, run_id) / "metadata.json"

    def write_run_metadata(self, env_id, run_id, metadata):
        with open(self.run_metadata_path(env_id, run_id), "w") as f:
            json.dump(metadata, f, indent=4)

    def read_run_metadata(self, env_id, run_id):
        with open(self.run_metadata_path(env_id, run_id), "r") as f:
            return json.load(f)

    def normalize_renderer_name(name: str) -> str:
        if name.lower().endswith(".dll"):
            return name[:-4]

        return name

    def update_run_alias( self, env_id, run_id, alias):
        metadata = self.read_run_metadata(env_id, run_id)
        metadata["alias"] = alias

        self.write_run_metadata(env_id, run_id,metadata)
        
        return {
            "success": True,
        }

    # fps snapshots
    def get_fps_snapshots(self, env_id, run_id):
        metadata = self.read_run_metadata(env_id, run_id)

        launcher = metadata.get("launcher", {})

        snapshots_path = Path(
            launcher.get("snapshots_path", "")
        )

        if not snapshots_path.exists():
            return {
                "success": False,
                "error": "FPS Snapshots path missing"
            }

        snapshots = {}

        for path in sorted( snapshots_path.glob("fps_*.json") ):
            try:
                with open(path, "r", encoding="utf8", errors="ignore") as f:
                    snapshots[path.stem] = json.load(f)

            except Exception as e:
                print(f"[fps snapshot load] {path.name}: {e}")

        return {
            "success": True,
            "snapshots": snapshots
        }

    # zone snapshots
    def get_zone_snapshots(self, env_id, run_id):
        metadata = self.read_run_metadata(env_id, run_id)

        launcher = metadata.get("launcher", {})

        snapshots_path = Path(launcher.get("snapshots_path", ""))

        if not snapshots_path.exists():
            return {
                "success": False,
                "error": "Snapshots path missing"
            }

        snapshots = {}

        for path in sorted( snapshots_path.glob("zone_*.json") ):
            try:
                with open(path, "r", encoding="utf8", errors="ignore") as f:
                    snapshots[path.stem] = json.load(f)

            except Exception as e:
                print(f"[zone snapshot load] {path.name}: {e}")

        return {
            "success": True,
            "snapshots": snapshots
        }

    # logs
    def get_qconsole( self, env_id, run_id):
        metadata = self.read_run_metadata(env_id, run_id)
        launcher = metadata.get("launcher", {})

        qconsole_path = launcher.get("qconsole_path", "")
        if os.path.exists(qconsole_path):
            with open(qconsole_path, "r", encoding="utf8", errors="ignore") as f:
                return f.read()

        return "empty"
    
    # actions
    def get_runs(self, env_id):
        runs = []

        runs_dir = self.runs_dir(env_id)

        if not runs_dir.exists():
            return runs

        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir():
                continue

            metadata_file = run_dir / "metadata.json"

            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                runs.append(metadata)

            except Exception as e:
                print(f"[run metadata error] {run_dir}: {e}")

        return sorted(
            runs,
            key=lambda x: x.get("id", ""),
            reverse=True
        )

    # run pipelines (load from modules/run_pipelines.py eventaully)
    def load_pipeline_presets(self):
        presets = {}

        if not self.pipeline_preset_dir.exists():
            return presets

        for path in self.pipeline_preset_dir.glob("*.yml"):

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                steps = data.get("steps", [])

                presets[path.stem] = {
                    "name": data.get("name", path.stem),
                    "description": data.get("description", ""),
                    "steps": [
                        {
                            "id": step.get("id", ""),
                            "type": step.get("type", ""),
                            "input": {
                                **step.get("input", {}),
                                "demos": step.get("input", {}).get("demos", "all")
                            }
                        }
                        for step in steps
                    ]
                }

            except Exception as e:
                print(f"[pipeline preset load] {path.name}: {e}")

        return presets

    # presets
    def save_run_preset(self, data):
        preset_id = data.get("preset_id", "").strip()
        preset = data.get("preset", {})

        if not preset_id:
            return {
                "success": False,
                "error": "Missing preset_id"
            }

        safe_name = "".join(
            x for x in preset_id
            if x.isalnum() or x in {"_", "-"}
        )

        if not safe_name:
            return {
                "success": False,
                "error": "Invalid preset name"
            }

        path = self.preset_dir / f"{safe_name}.json"

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    preset,
                    f,
                    indent=4
                )

            return {
                "success": True,
                "preset_id": safe_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def load_run_presets(self):
        presets = {}

        if not self.preset_dir.exists():
            return presets

        for path in self.preset_dir.glob("*.json"):

            try:
                with open(path, "r", encoding="utf-8") as f:
                    presets[path.stem] = json.load(f)

            except Exception as e:
                print(f"[run preset load] {path.name}: {e}")

        return presets

    def get_run_presets(self, env_id):
        env_metadata = self.environment.read_metadata(env_id)

        _paths = self.context.environment.get_paths(env_id)
        install_dir = _paths["install_dir"]

        if not install_dir.exists():
            return {
                "success": False,
                "error": "Build output missing",
                "details": str(install_dir)
            }

        executables = sorted(
            [
                x.name
                for x in install_dir.glob("*.exe")
                if ".ded" not in x.name.lower()
            ]
        )

        renderers = [
            x.stem.split("_", 1)[0]
            for x in install_dir.glob("rd-*.dll")
        ]


        presets = self.load_run_presets()
        pipeline_presets = self.load_pipeline_presets()

        #global_client = self.context.client.get_client(env_id)
        run_preset = (
            env_metadata.get("run_configuration", {}).get("default_preset")
            or self.config.var.default_run_preset
        )

        return {
            "success": True,
            "defaults" : {
                "run_preset": run_preset,
            },
            "executables"       : executables,
            "renderers"         : renderers,
            "pipeline_presets"  : pipeline_presets,

            "presets": presets,
        }

    def prepare_run_directory( self, env_id, run_id, run_dir, install_dir, base_dir, assets_dir ):
        def ignore_base(dirpath, names):
            if Path(dirpath).resolve() == Path(install_dir).resolve():
                return {"base"}
            return set()
       
        # copy build output
        shutil.copytree(
            install_dir, 
            run_dir,
            ignore=ignore_base
        )

        try:
            shutil.copytree(
                str(assets_dir),
                run_dir,
                dirs_exist_ok=True
            )

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed copying assets: {e}"
            }

        # base junction
        base_output = run_dir / "base"

        if not os.path.exists(base_dir):
            return {
                "success": False,
                "error": "Base directory missing"
            }

        try:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(base_output), base_dir],
                check=True,
                shell=False
            )

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed creating base junction: {e}"
            }

        return {
            "success": True
        }

    def extract_fs_basegame_from_args(self, arguments):
        mod = "base"

        if "+set" in arguments:
            for i in range(len(arguments) - 2):
                if arguments[i] == "+set" and arguments[i + 1] == "fs_game":
                    mod = arguments[i + 2]
                    break

        return mod

    def start(self, env_id, launcher=None):
        env_metadata = self.environment.read_metadata(env_id)
        launcher = launcher or {}

        # use centralized build path resolver
        _paths = self.context.environment.get_paths(env_id)

        build_dir   = _paths["build_dir"]
        install_dir = _paths["install_dir"]
        assets_dir  = _paths["assets_dir"]

        if not build_dir.exists():
            return {
                "success": False,
                "error": "Build dir missing",
                "details": str(build_dir)
            }

        if not install_dir.exists():
            return {
                "success": False,
                "error": "Build output missing",
                "details": str(install_dir)
            }

        if not assets_dir.exists():
            return {
                "success": False,
                "error": "Assets folder missing",
                "details": str(assets_dir)
            }

        run_id = self.create_run_id()
        run_dir = self.run_dir(env_id, run_id)

        # launcher info
        executable      = launcher.get("executable", "eternaljk.x86.exe")
        pipeline_preset = launcher.get("pipeline_preset", "preset_default")
        base_id         = launcher.get("base_id", None)

        arguments       = launcher.get("arguments", [])
        fs_basegame     = self.extract_fs_basegame_from_args( arguments )

        if not isinstance(base_id, int):
            return {
                "success": False,
                "error": f"Invalid base id",
            }
        base_location = self.config.get_base_location( base_id )    
        if not base_location:
            return {
                "success": False,
                "error": "Invalid base location"
            }
        base_dir = base_location.get("path", None)

        result = self.prepare_run_directory(
            env_id,
            run_id,
            run_dir,
            install_dir,
            base_dir,
            assets_dir
        )

        if not result["success"]:
            return result

        pipeline = RunPipeline(
            run_context=self,
            env_id=env_id,
            run_id=run_id,
            preset=pipeline_preset
        )

        metadata = {
            "id"        : run_id,
            "status"    : "running",
            "created"   : self.now(),
            "started"   : self.now(),
            "ended"     : None,
            "launcher": {
                "executable"            : executable,
                "base_id"               : base_id,
                "base_dir"              : base_dir, # resolved
                "arguments"             : arguments,
                "fs_basegame"           : fs_basegame,
                "qconsole_path"         : str((run_dir / fs_basegame / "qconsole.log")),
                "snapshots_path"   : str((run_dir / fs_basegame / "snapshots")),
            },
            "process": {
                "pid"           : None,
                "returncode"    : None
            },
            "pipeline"  : pipeline.pipeline_metadata,
            "results"   : {},
            "build"     : {
                "build_dir"     : str(build_dir),
                "install_dir"   : str(install_dir)
            }
        }

        self.write_run_metadata(env_id, run_id, metadata)

        # pipeline
        self.active_processes[run_id] = {
            "pipeline": pipeline
        }

        # start the pipeline
        print( pipeline.start_pipeline() )

        return {
            "success": True,
            "run_id": run_id
        }

    def cancel(self, env_id, run_id):
        metadata = self.read_run_metadata(env_id, run_id)

        runtime = self.active_processes.get(run_id)
        proc = runtime.get("process") if runtime else None

        if not runtime:
            return {
                "success": False,
                "error": "Runtime not found"
            }

        if not proc:
            return {
                "success": False,
                "error": "Run process not active"
            }

        try:
            self.shutdown_runtime(
                run_id,
                terminate=True
            )

            metadata["status"] = "terminating"

            self.write_run_metadata(
                env_id,
                run_id,
                metadata
            )

            return {
                "success": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def move_snapshots_final( self, env_id, run_id, metadata, source_key, target_dir, metadata_key=None ):
        run_dir = self.run_dir(env_id, run_id)
        launcher = metadata["launcher"]

        snapshots_path = Path(launcher.get(source_key, ""))

        if not snapshots_path.exists():
            return

        new_snapshots_path = run_dir / target_dir

        print(f"move snapshots from {snapshots_path} to {new_snapshots_path}")

        shutil.move(snapshots_path, new_snapshots_path)

        launcher[metadata_key or source_key] = str(new_snapshots_path)

        self.write_run_metadata(env_id, run_id, metadata)

    def move_qconsole_final(self, env_id, run_id, metadata):
        run_dir = self.run_dir(env_id, run_id)
        launcher = metadata["launcher"]

        if not Path(launcher["qconsole_path"]).exists():
            return

        # move qconsole log into the run dir
        new_qconsole_path = run_dir / "qconsole.log"
        shutil.copy(
            Path(launcher["qconsole_path"]), 
            new_qconsole_path
        )

        # update metadata with the new path
        metadata["launcher"]["qconsole_path"] = str(new_qconsole_path)

        self.write_run_metadata(env_id, run_id, metadata)

    def cleanup_run(self, env_id, run_id, metadata):
        run_dir = self.run_dir(env_id, run_id)

        if not run_dir.exists():
            return

        launcher = metadata["launcher"]

        # move logs
        self.move_qconsole_final(env_id, run_id, metadata)

        # move snapshots
        self.move_snapshots_final( env_id, run_id, metadata, source_key="snapshots_path", target_dir="snapshots" )

        # remove and keep files
        for item in run_dir.iterdir():
            # keep these
            KEEP_FILES = {
                "metadata.json",
                "qconsole.log",
                "snapshots",
            }
            if item.name in KEEP_FILES:
                continue

            # remove these
            try:
                if item.is_symlink() or os.path.islink(item):
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

            except Exception as e:
                print(f"[run cleanup] {item}: {e}")

    def finalize_pipeline(self, metadata):
        pipeline = metadata.get("pipeline")

        if not pipeline:
            return

        if pipeline.get("status") == "running":
            pipeline["status"] = "cancelled"
            pipeline["ended"] = self.now()

        for step in pipeline.get("steps", {}).values():

            if step["status"] not in {
                "pending",
                "running"
            }:
                continue

            step["status"] = "cancelled"

            if not step.get("ended"):
                step["ended"] = self.now()

    def finish_run(self, env_id, run_id, returncode=0):
        print(f"[{env_id}] Finish run: {run_id}")

        metadata = self.read_run_metadata(env_id, run_id)

        runtime = self.active_processes.get(run_id)

        if metadata["status"] == "terminating":
            metadata["status"] = "cancelled"

        elif returncode == 0:
            metadata["status"] = "finished"

        else:
            metadata["status"] = "failed"

        metadata["ended"] = self.now()
        metadata["process"]["returncode"] = returncode

        self.finalize_pipeline(metadata)

        self.write_run_metadata(
            env_id,
            run_id,
            metadata
        )

        self.shutdown_runtime(
            run_id,
            terminate=True
        )

        self.cleanup_run(env_id, run_id, metadata)

        self.active_processes.pop(run_id, None)

    def shutdown_runtime(self, run_id, terminate=False, join_timeout=2):
        runtime = self.active_processes.get(run_id)
        if not runtime:
            return None

        proc = runtime.get("process")
        qconsole_monitor = runtime.get("qconsole_monitor")

        if proc:
            try:
                if terminate:
                    proc.terminate()
            except Exception as e:
                print(f"[shutdown terminate] {e}")

            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass

            try:
                if proc.stdout:
                    proc.stdout.close()
            except Exception:
                pass

            try:
                if proc.stderr:
                    proc.stderr.close()
            except Exception:
                pass

            if terminate:
                try:
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass

        # close qconsole_monitor (failsafe, closes itself in qconsole_monitor_loop)
        try:
            if (
                qconsole_monitor
                and qconsole_monitor.is_alive()
                and qconsole_monitor != threading.current_thread()
            ):
                qconsole_monitor.join(timeout=join_timeout)

        except Exception as e:
            print(f"[shutdown qconsole_monitor join] {e}")

        self.active_processes.pop(run_id, None)
