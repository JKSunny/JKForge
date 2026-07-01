from typing import TYPE_CHECKING

from pathlib import Path
from datetime import datetime
import subprocess
import uuid
import json
import shutil
import os
from datetime import datetime

from modules.configuration import Generator
from modules.constants import *

if TYPE_CHECKING:
    from main import JKForge

class Environment:
    def __init__(self, context : 'JKForge'):
        self.context : 'JKForge'  = context
        self.config                 = context.config

        self.builds_dir = Path( self.config.resource_path("builds") )

    def now(self):
        return datetime.now().isoformat()

    def env_dir(self, env_id):
        return self.builds_dir / env_id

    def metadata_path(self, env_id):
        return self.env_dir(env_id) / "metadata.json"

    def write_metadata(self, env_id, metadata):
        with open(self.metadata_path(env_id), "w") as f:
            json.dump(metadata, f, indent=4)

    def read_metadata(self, env_id):
        with open(self.metadata_path(env_id), "r") as f:
            return json.load(f)

    def get_logs_path(self, env_id):
        return self.env_dir(env_id) / "logs"

    def get_paths(self, env_id):
        metadata            = self.read_metadata(env_id)

        build_conf          = metadata["build_configuration"]
        client              = self.context.client.get_client(env_id)

        build_type          = build_conf["type"]
        arch                = build_conf["arch"]
        
        generator : Generator = Generator(**build_conf["generator"])

        env_dir             = self.env_dir(env_id)
        env_logs_dir        = self.get_logs_path(env_id)
        source_dir          = env_dir / "source"

        # source/build/vs2022_x86
        # source/build/vs2019_x86_64
        build_folder_name   = f"{generator.id}_{arch}"
        build_dir           = source_dir / "build" / build_folder_name

        # source/build/vs2022_x86/Release
        output_dir = build_dir / build_type

        # source/build/vs2022_x86/Release/JediAcademy
        install_dir = output_dir / client.install_dir

        # client assets/patches dir
        assets_dir = Path( self.config.resource_path(f"client/{metadata["client"]}/assets") )
        patches_dir = Path( self.config.resource_path(f"client/{metadata["client"]}/patches") )

        return {
            "env_dir"       : env_dir,
            "env_logs_dir"  : env_logs_dir,
            "source_dir"    : source_dir,
            "build_dir"     : build_dir,
            "output_dir"    : output_dir,
            "install_dir"   : install_dir,
            "build_type"    : build_type,
            "arch"          : arch,
            "generator"     : generator,
            "assets_dir"    : assets_dir,
            "patches_dir"   : patches_dir
        }

    #
    # sub processing
    #
    def run_proc_live(self, env_id, cmd, cwd=None, log_file=None):
        logs_dir = self.get_logs_path(env_id)
        log_path = logs_dir / f"{log_file}.log"

        print(">", " ".join(map(str, cmd)))

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        with open(log_path, "a", encoding="utf-8") as f:
            for line in proc.stdout:
                self.context.socket_append_envconsole(env_id, line)
                f.write(line)
                f.flush()

        proc.wait()

        return proc

    def run_proc(self, cmd, cwd=None):
        print(">", " ".join(map(str, cmd)))

        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True
        )

    #
    # logging
    #
    def write_log(self, env_id, log, log_file):
        logs_dir = self.get_logs_path(env_id)
        log_path = logs_dir / f"{log_file}.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write( log )

        return log

    def write_proc_log(self, env_id, proc, log_file):
        log = "\n".join(
            x for x in [proc.stdout, proc.stderr] if x
        )

        return self.write_log( env_id, log, log_file )

    def clear_build_logs( self, env_id ):
        logs_dir = self.get_logs_path(env_id)
        logs = [
            "cmake_configure.log",
            "cmake_build.log",
            "cmake_install.log",
        ]

        for name in logs:
            log_file = logs_dir / name
            if log_file.exists():
                log_file.unlink()

        self.context.socket_redraw_envconsole
        return True

    def get_env_console( self, env_id ):
        logs_dir = self.get_logs_path(env_id)

        if not logs_dir.exists():
            return ""

        output = []

        log_order = [
            "git_clone.log",
            "checkout_commit.log",
            "git_patch.log",
            "cmake_configure.log",
            "cmake_build.log",
            "cmake_install.log",
        ]

        for name in log_order:
            log_file = logs_dir / name
            if log_file.exists():
                output.append(f"\n===== {log_file.name} =====\n")

                with open(log_file, "r", encoding="utf8", errors="ignore") as f:
                    output.append(f.read())

        return "".join(output)
    
    #
    # steps
    #
    def init_step(self):
        return {
            "status": STEP_WAITING,
            "started": None,
            "ended": None,
            "duration": 0.0,
            #"log": None,
            #"retries": 0
        }

    def step_update(self, env_id, group, section, step, status):
        metadata = self.read_metadata(env_id)

        entry = metadata["steps"][group][section][step]
        entry["status"] = status

        if status == STEP_RUNNING:
            entry["started"] = self.now()
            entry["ended"] = None
            entry["duration"] = 0.0

        if status in [STEP_DONE, STEP_FAILED, STEP_SKIPPED]:
            entry["ended"] = self.now()

            if entry.get("started"):
                started = datetime.fromisoformat(entry["started"])
                ended = datetime.fromisoformat(entry["ended"])

                entry["duration"] = round(
                    (ended - started).total_seconds(),
                    3
                )

        self.write_metadata(env_id, metadata)

    def step_running( self, step ):
        return step.get("status") == STEP_RUNNING

    def git_running( self, metadata ):
        setup = metadata["steps"]["environment"]["setup"]

        return (
            self.step_running(setup["git_fetch"]) or
            self.step_running(setup["git_patch"]) or
            self.step_running(setup["checkout_commit"])
        )

    def build_running( self, metadata ):
        build = metadata["steps"]["environment"]["build"]

        return (
            self.step_running(build["cmake_configure"]) or
            self.step_running(build["cmake_build"]) or
            self.step_running(build["cmake_install"])
        )

    #
    # general
    #
    def get_environments( self ):
        environments = []

        if not self.builds_dir.exists():
            return environments

        for env_dir in self.builds_dir.iterdir():
            if not env_dir.is_dir():
                continue

            metadata_file = env_dir / "metadata.json"

            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                metadata["id"] = env_dir.name
                metadata["runs"] = self.context.run.get_runs(env_dir.name)

                environments.append(metadata)

            except Exception as e:
                print(f"[metadata error] {env_dir}: {e}")

        return sorted(
            environments,
            key=lambda x: x.get("id", ""),
            reverse=True
        )

    def create_instance( self, conf ):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch = conf["branch"].replace("/", "_")
        rand = str(uuid.uuid4())[:6]

        env_id = f"{ts}_{branch}_{rand}"
        env_dir = self.builds_dir / env_id
        env_dir.mkdir(parents=True)

        return {
            "id": env_id,
            "dir": env_dir
        }

    def update_environment_alias( self, env_id, alias):
        metadata = self.read_metadata(env_id)
        metadata["alias"] = alias

        self.write_metadata(env_id, metadata)

        return {
            "success": True,
        }

    def set_default_run_preset( self, env_id, preset_id ):
        metadata = self.read_metadata(env_id)

        metadata["run_configuration"] = metadata.get("run_configuration", {})
        metadata["run_configuration"]["default_preset"] = str(preset_id)

        self.write_metadata(env_id, metadata)

        return {
            "success": True,
        }

    def create( self, conf) :
        env = self.create_instance(conf)

        for name in ("logs", "runs"):
            (env["dir"] / name).mkdir(exist_ok=True)

        build_conf = conf["build_configuration"]

        # probably need to be a dataclass eventually.
        metadata = {
            "id"    : env["id"],
            "alias" : env["id"],

            "client"    : conf["client"],
            "git"       : conf["git"],
            "branch"    : conf["branch"],
            "commit"    : conf.get("commit"),

            "build_configuration": {
                "type"          : build_conf["type"],
                "arch"          : build_conf["arch"],
                "generator"     : build_conf["generator"],
                "cmake_options" : build_conf["cmake_options"]
            },  
            "run_configuration": {
                "default_preset" : "default",
            },  
            "status": 0,

            "steps": {
                "environment": {
                    "setup": {
                        "create_folders"    : self.init_step(),
                        "git_fetch"         : self.init_step(),
                        "checkout_commit"   : self.init_step(),
                        "git_patch"         : self.init_step()
                    },

                    "build": {
                        "cmake_configure"   : self.init_step(),
                        "cmake_build"       : self.init_step(),
                        "cmake_install"     : self.init_step()
                    }
                },
                "runs": {}
            }
        }

        self.write_metadata(env["id"], metadata)
        self.step_update( env["id"], "environment", "setup", "create_folders", STEP_DONE )

        return {
            "success": True,
        }

    def delete(self, env_id):
        env_dir = self.env_dir(env_id)

        if not env_dir.exists():

            return {
                "success": False,
                "error": "Environment does not exist"
            }
        try:
            shutil.rmtree(env_dir)

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

        return {
            "success": True,
            "environment": env_id
        }