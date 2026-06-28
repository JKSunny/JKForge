from typing import TYPE_CHECKING

import time
import psutil
import threading
from pathlib import Path

if TYPE_CHECKING:
    from modules.run import Run

from modules.constants import *

class RunMonitor:
    def __init__(self, run_context : 'Run'):
        self.run_context : 'Run' = run_context
        self.active_processes = run_context.active_processes
        self.environment = run_context.environment

    def update_running_runs(self):
        environments = self.environment.get_environments()

        for env in environments:
            env_id = env["id"]

            for run in self.run_context.get_runs(env_id):
                if run.get("status") not in {"running", "terminating"}:
                    continue

                run_id = run["id"]
                runtime = self.active_processes.get(run_id)
                proc = runtime["process"] if runtime else None

                # Try to resurrect Popen-like object from PID if not in memory
                if not runtime:
                    pid = run.get("process", {}).get("pid")
                    if pid and psutil.pid_exists(pid):
                        try:
                            class DummyPopen:
                                def __init__(self, pid):
                                    self._pid = pid
                                    self._proc = psutil.Process(pid)

                                def poll(self):
                                    try:
                                        # exited, cannot get correct returncode yet .. mark as failed maybe. or add: 
                                        # new lost return code?
                                        if not self._proc.is_running() or self._proc.status() == psutil.STATUS_ZOMBIE:
                                           # return self._proc.returncode if hasattr(self._proc, 'returncode') else -1
                                            return -1

                                        # keep alive
                                        return None 
                                    except psutil.NoSuchProcess:
                                        return -1
                                    except psutil.TimeoutExpired:
                                        return -1

                            proc = DummyPopen(pid)

                            self.active_processes[run_id] = {
                                "process"           : proc,
                                "qconsole_monitor"  : None # make this
                            }

                        except Exception as e:
                            print(f"[resurrect run] failed for {run_id}: {e}")
                            proc = None

                # proc not found
                if not proc:
                    self.run_context.finish_run(env_id, run_id, returncode=-1)
                    continue

                # Check if the process has exited
                returncode = proc.poll()
                if returncode is None:
                    continue

                # Process finished, mark run accordingly
                self.run_context.finish_run(env_id, run_id, returncode=returncode)
                del self.active_processes[run_id]

    def qconsole_monitor_loop(self, env_id, run_id, qconsole_path):
        qconsole_path = Path(qconsole_path)

        while not qconsole_path.exists():
            time.sleep(0.1)

        error_triggered = False

        with open(qconsole_path, "r", encoding="utf-8", errors="ignore") as f:
            print(f"{bcolors.WARNING}{run_id}] START qconsole monitor{bcolors.ENDC}")

            f.seek(0, 2) # tail mode

            while True:
                # auto quit thread
                runtime = self.run_context.active_processes.get(run_id)

                if not runtime:
                    print(f"{bcolors.WARNING}{run_id}] STOP qconsole monitor{bcolors.ENDC}")
                    break
                proc = runtime.get("process")
                if not proc or proc.poll() is not None:
                    print(f"{bcolors.WARNING}{run_id}] STOP qconsole monitor{bcolors.ENDC}")
                    break

                line = f.readline()

                if not line:
                    time.sleep(0.05)
                    continue

                line = line.rstrip()

                # emit socket update
                self.run_context.context.socket_append_qconsole(env_id, run_id, line)

                # debug..
                print(f"{bcolors.OKGREEN}[{run_id}] {line}{bcolors.ENDC}")

                # hadle messages like: DROPPED, ERROR
                # Z_Malloc(): Failed to alloc 134217728 bytes (TAG_TEMP_HUNKALLOC) !!!!!
                # ^1Z_Malloc(): Failed to alloc 134217728 bytes (TAG_TEMP_HUNKALLOC) !!!!!
                # then self.run_context.finish_run(env_id, run_id, returncode=-1)
                # Out of ghoul2 info slotsPortable install requested, skipping homepath support
                pipeline = runtime.get("pipeline")
                if pipeline and not error_triggered and "Z_MALLOC(): FAILED TO ALLOC" in line.upper():
                    error_triggered = True

                    print(
                        f"{bcolors.FAIL}[{run_id}] "
                        f"MEMORY ERROR DETECTED: "
                        f"{line}"
                        f"{bcolors.ENDC}"
                    )

                    #threading.Timer(
                    #    20.0,
                    #    lambda: self.run_context.finish_run(
                    #        pipeline.env_id,
                    #        run_id,
                    #        returncode=-1
                    #    )
                    #).start()

                # forward qconsole to pipeline step
                if pipeline:
                    pipeline.handle_qconsole(line)


    def monitor_loop(self, interval=2):
        while True:
            try:
                self.update_running_runs()

                # update pipelines
                for run_id, runtime in self.active_processes.items():

                    pipeline = runtime.get("pipeline")

                    if not pipeline:
                        continue

                    pipeline.update()

            except Exception as e:
                print(f"[monitor] {e}")

            time.sleep(interval)



    #def find_window_by_pid(self, pid):
    #    result = []
    #
    #    def callback(hwnd, _):
    #        if not win32gui.IsWindowVisible(hwnd):
    #            return
    #
    #        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
    #
    #        if window_pid == pid:
    #            result.append(hwnd)
    #
    #    win32gui.EnumWindows(callback, None)
    #
    #    return result[0] if result else None


    #def send_command(self, env_id, run_id, command):
        #metadata = self.read_run_metadata(env_id, run_id)
        #pid = metadata["process"]["pid"]
        #hwnd = self.find_window_by_pid(pid)
        #win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        #win32gui.SetForegroundWindow(hwnd)
        #
        #if not hwnd:
        #    return {
        #        "success": False,
        #        "error": "Game window not found"
        #    }