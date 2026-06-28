from typing import TYPE_CHECKING

import subprocess
import shutil
from pathlib import Path

from modules.constants import *

if TYPE_CHECKING:
    from main import JKForge

class CloneError(Exception):
    def __init__(self, stage, error):
        self.stage = stage
        self.error = error

        super().__init__(error)

class Clone:
    def __init__(self, context : 'JKForge'):
        self.context    : 'JKForge' = context
        self.environment = context.environment
        self.config = context.config

    # ---------------------------
    # Apply patches
    # ---------------------------
    def repatch(self, env_id):
        metadata = self.environment.read_metadata(env_id)
        _paths = self.environment.get_paths(env_id)

        source_dir = _paths["source_dir"]

        try:
            cmd = ["git", "reset", "--hard", "HEAD"]
            result = self.environment.run_proc(cmd,cwd=source_dir)
            log = self.environment.write_proc_log( env_id, result, "git_repatch_reset" )

            if result.returncode != 0:
                raise CloneError("git_patch", log)

            # remove *.rej files from previous failed patch attempts
            for rej in source_dir.rglob("*.rej"):
                rej.unlink(missing_ok=True)

            # remove *.orig files git apply may create
            for orig in source_dir.rglob("*.orig"):
                orig.unlink(missing_ok=True)

            self.apply_patches(
                env_id,
                metadata,
                _paths
            )

            return {"success": True}

        except CloneError as e:
            error =  {
                "success": False,
                "stage": e.stage,
                "error": e.error
            }
            print(error)

            return error

    def apply_patches( self, env_id, metadata, _paths ):
        source_dir  = _paths["source_dir"]
        patches_dir = _paths["patches_dir"]

        if not patches_dir.exists():
            self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_FAILED)
            
            raise CloneError( "git_patch", "Patches directory missing" )

        patch_files = sorted(
            patches_dir.glob("*.patch")
        )

        if not patch_files:
            self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_SKIPPED)

            return {
                "success": True
            }

        self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_RUNNING)

        for patch_file in patch_files:
            print(str(patch_file.resolve()))
            try:
                cmd = ["git", "apply", "--reject", "--verbose", str(patch_file.resolve())]
                print(">", " ".join(map(str, cmd)))

                result = self.environment.run_proc_live( env_id, cmd, str(source_dir), "git_patch")

                if result.returncode != 0:
                    self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_FAILED)
   
                    raise CloneError( "git_patch", "" )

                print(f"[patch] applied {patch_file.name}")

            except CloneError:
                raise

            except subprocess.CalledProcessError as e:
                error = f"Failed applying patch "
                self.context.socket_append_envconsole(env_id, error)
                self.environment.write_log( env_id, error, "git_patch" )
                self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_FAILED)

                raise CloneError( "git_patch", error )

            except Exception as e:
                error = f"Failed applying patch {patch_file.name}:\n{e}"
                self.context.socket_append_envconsole(env_id, error)
                self.environment.write_log( env_id, error, "git_patch" )
                self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_FAILED)

                raise CloneError( "git_patch", error )


        self.environment.step_update(env_id, "environment", "setup", "git_patch", STEP_DONE)

        return {
            "success": True
        }
   
    # ---------------------------
    # Clone repo
    # ---------------------------
    def clone( self, env_id, metadata, _paths ):
        source_dir  = _paths["source_dir"]
        repo_url = f"https://github.com/{metadata['git']}.git"

        self.environment.step_update(env_id, "environment", "setup", "git_fetch", STEP_RUNNING)

        cmd = [
            "git", "clone", "--branch", metadata["branch"],
            repo_url,
            str(source_dir)
        ]
        result = self.environment.run_proc_live( env_id, cmd, cwd=None, log_file="git_fetch")

        if result.returncode != 0:
            self.environment.step_update(env_id, "environment", "setup", "git_fetch", STEP_FAILED)
            
            raise CloneError( "git_fetch", "" )

        self.environment.step_update(env_id, "environment", "setup", "git_fetch", STEP_DONE)
    
    # ---------------------------
    # Checkout commit *optional
    # ---------------------------
    def checkout( self, env_id, metadata, _paths ):
        source_dir  = _paths["source_dir"]

        if not metadata.get("commit"):
            self.environment.step_update(env_id, "environment", "setup", "checkout_commit", STEP_SKIPPED)
            return

        self.environment.step_update(env_id, "environment", "setup", "checkout_commit", STEP_RUNNING)
        cmd = [
            "git", "checkout",
            metadata["commit"]
        ]
        result = self.environment.run_proc_live( env_id, cmd, source_dir, "checkout_commit")

        if result.returncode != 0:
            self.environment.step_update(env_id, "environment", "setup", "checkout_commit", STEP_FAILED)
            
            raise CloneError( "checkout_commit", "" )

        self.environment.step_update(env_id, "environment", "setup", "checkout_commit", STEP_DONE)
   
    # ---------------------------
    # Set current commit sha in metadata
    # ---------------------------
    def set_commit_sha( self, env_id, metadata, _paths ):
        source_dir  = _paths["source_dir"]

        result = self.environment.run_proc([
            "git", "rev-parse", "HEAD"
        ], cwd=source_dir)

        # update git commit sha
        metadata = self.environment.read_metadata(env_id)
        metadata["commit"] = result.stdout.strip()
        self.environment.write_metadata(env_id, metadata)

    # ---------------------------
    # Start
    # ---------------------------
    def start( self, env_id ):
        metadata = self.environment.read_metadata(env_id)

        if self.environment.git_running(metadata):
            return {
                "success": False,
                "error": "Git job already running"
            }

        if self.environment.build_running(metadata):
            return {
                "success": False,
                "error": "Build already running"
            }

        _paths = self.environment.get_paths(env_id)

        try:
            self.clone( env_id, metadata, _paths )
            self.checkout( env_id, metadata, _paths )
            self.set_commit_sha( env_id, metadata, _paths )
            self.apply_patches( env_id, metadata, _paths)

        except CloneError as e:
            error =  {
                "success": False,
                "stage": e.stage,
                "error": e.error
            }
            print(error)

            return error

        return {
            "success": True,
            "environment": env_id,
            "commit": metadata["commit"]
        }