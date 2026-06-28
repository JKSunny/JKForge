from typing import TYPE_CHECKING

import subprocess
import shutil
from pathlib import Path

from modules.constants import *

if TYPE_CHECKING:
    from main import JKForge

class BuildError(Exception):
    def __init__(self, stage, error):
        self.stage = stage
        self.error = error

        super().__init__(error)

class Build:
    def __init__(self, context : 'JKForge'):
        self.context    : 'JKForge' = context
        self.environment = context.environment
        self.config = context.config

    def configure_cmd( self, env_id, metadata, _paths ):
        """Implemented by client class in modules/client/*.py"""
        return False

    def build_cmd( self, env_id, metadata, _paths ):
        """Implemented by client class in modules/client/*.py"""

        return False
    
    def install_cmd( self, env_id, metadata, _paths ):
        """Implemented by client class in modules/client/*.py"""
        return False


    # ---------------------------
    # Configure
    # ---------------------------
    def configure( self, env_id, metadata, _paths ):
        source_dir   = _paths["source_dir"]
        self.environment.step_update(env_id, "environment", "build", "cmake_configure", STEP_RUNNING)

        # cmd implemented in client class
        cmd = self.configure_cmd(env_id, metadata, _paths)

        if not cmd:
            self.environment.step_update(env_id, "environment", "build", "cmake_configure", STEP_FAILED)
            self.environment.write_log( env_id, "invalid cmd", "cmake_configure" )

            raise BuildError( "configure", "invalid cmd" )
            
        result = self.environment.run_proc_live( env_id, cmd, cwd=source_dir, log_file="cmake_configure")

        if result.returncode != 0:
            self.environment.step_update(env_id, "environment", "build", "cmake_configure", STEP_FAILED)

            raise BuildError( "configure", "" )

        self.environment.step_update(env_id, "environment", "build", "cmake_configure", STEP_DONE)

    # ---------------------------
    # Build
    # ---------------------------
    def build( self, env_id, metadata, _paths ):
        build_conf = metadata["build_configuration"]
        build_dir   = _paths["build_dir"]

        self.environment.step_update(env_id, "environment", "build", "cmake_build", STEP_RUNNING)

        # cmd implemented in client class
        cmd = self.build_cmd(env_id, metadata, _paths)

        if not cmd:
            self.environment.step_update(env_id, "environment", "build", "cmake_build", STEP_FAILED)
            self.environment.write_log( env_id, "invalid cmd", "cmake_build" )

            raise BuildError( "build", "invalid cmd" )

        result = self.environment.run_proc_live( env_id, cmd, cwd=build_dir, log_file="cmake_build")

        if result.returncode != 0:
            self.environment.step_update(env_id, "environment", "build", "cmake_build", STEP_FAILED)

            raise BuildError( "build", "" )

        self.environment.step_update(env_id, "environment", "build", "cmake_build", STEP_DONE)

    # ---------------------------
    # Install
    # ---------------------------
    def install( self, env_id, metadata, _paths ):
        build_conf = metadata["build_configuration"]
        build_dir   = _paths["build_dir"]

        self.environment.step_update(env_id, "environment", "build", "cmake_install", STEP_RUNNING)

        # cmd implemented in client class
        cmd = self.install_cmd(env_id, metadata, _paths)

        if not cmd:
            self.environment.step_update(env_id, "environment", "build", "cmake_install", STEP_FAILED)
            self.environment.write_log( env_id, "invalid cmd", "cmake_install" )

            raise BuildError( "install", "invalid cmd" )

        result = self.environment.run_proc_live( env_id, cmd, cwd=build_dir, log_file="cmake_install")

        if result.returncode != 0:
            self.environment.step_update(env_id, "environment", "build", "cmake_install", STEP_FAILED)

            raise BuildError( "install", "" )

        self.environment.step_update(env_id, "environment", "build", "cmake_install", STEP_DONE)

    # ---------------------------
    # Start
    # ---------------------------
    def start(self, env_id):
        metadata = self.environment.read_metadata(env_id)

        if self.environment.git_running(metadata):
            return {
                "success"   : False,
                "error"     : "Git job still running"
            }

        if self.environment.build_running(metadata):
            return {
                "success"   : False,
                "error"     : "Build already running"
            }

        _paths = self.environment.get_paths(env_id)
        build_dir   = _paths["build_dir"]
        output_dir  = _paths["output_dir"]

        build_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.configure( env_id, metadata, _paths )
            self.build( env_id, metadata, _paths )
            self.install( env_id, metadata, _paths )

        except BuildError as e:
            return {
                "success"   : False,
                "stage"     : e.stage,
                "error"     : e.error
            }

        return {
            "success"       : True,
            "environment"   : env_id,
            "build_dir"     : str(build_dir),
            "output_dir"    : str(output_dir)
        }

    # ---------------------------
    # Rebuild
    # ---------------------------
    def rebuild(self, env_id):
        metadata = self.environment.read_metadata(env_id)

        if self.environment.build_running(metadata):
            return {
                "success"   : False,
                "error"     : "Build already running"
            }

        _paths = self.environment.get_paths(env_id)
        build_dir = _paths["build_dir"]

        try:
            if build_dir.exists():
                shutil.rmtree(build_dir)

            self.environment.clear_build_logs(env_id)

        except Exception as e:
            return {
                "success"   : False,
                "error"     : str(e)
            }

        metadata["steps"]["environment"]["build"] = {
            "cmake_configure"   : self.environment.init_step(),
            "cmake_build"       : self.environment.init_step(),
            "cmake_install"     : self.environment.init_step()
        }

        self.environment.write_metadata(env_id, metadata)

        return self.start( env_id )
