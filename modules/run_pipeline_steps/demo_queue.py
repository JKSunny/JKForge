from pathlib import Path
import threading
import re

from .base import RunPipelineStep

class DemoQueueStep(RunPipelineStep):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.demo_active = False
        self.demo_files = []
        self.current_demo_index = 0

        self.repeat = 1
        self.current_repeat = 0

    def start(self):
        input_data = self.step_data.get("input", {})
        self.repeat = int( input_data.get("repeat", 0) )
        requested_demos = input_data.get("demos")

        metadata = self.metadata()

        launcher = metadata["launcher"]
   
        # get launcher info
        #fs_basegame = launcher["fs_basegame"]
        # look for demos in base folder, not in mod folder.
        fs_basegame = "base"

        run_dir = self.run_dir()
        demos_dir = ( run_dir / fs_basegame / "demos" )

        # create list of demos
        if requested_demos:
            self.demo_files = []

            for demo in requested_demos:
                demo = demo if demo.endswith(".dm_26") else f"{demo}.dm_26"
                demo_path = demos_dir / demo

                if not demo_path.is_file():
                    return {
                        "success": False,
                        "error": f"Demo not found: {demo}"
                    }

                self.demo_files.append(demo_path)
        else:
            self.demo_files = sorted(demos_dir.glob("*.dm_26"))

        if not self.demo_files:
            return {
                "success": False,
                "error": f"No demos found in: {demos_dir}"
            }

        print(
            f"[{self.run_id}] loaded "
            f"{len(self.demo_files)} demos"
        )

        # metadata
        step = self.step()
        self.ensure_step_details()

        step["details"] = {
            "total_demos": len(self.demo_files),
            "current_demo": None,
            "completed_demos": 0,
            "repeat": self.repeat,
            "current_repeat": 0,
            "demos": {}
        }

        for demo_path in self.demo_files:
            demo_name = demo_path.stem

            step["details"]["demos"][demo_name] = {
                "plays": 0,
                "started": None,
                "loaded": None,
                "ended": None,
                "load_time": None,
                "status": "pending"
            }

        self.sync_metadata()

        # start first demo
        return self.play_next_demo()

    def handle_nextdemo_repeat_or_finish(self):
        if self.current_demo_index < len(self.demo_files):
            return {
                "success": True,
                "action": "next_demo"
            }

        self.current_repeat += 1
        step = self.step()

        if self.repeat > 0 and self.current_repeat >= self.repeat:
            print(f"[{self.run_id}] demo queue finished")

            self.sync_metadata()
            self.finish()

            return {
                "success": True,
                "action": "finished"
            }

        print(f"[{self.run_id}] restart demo queue (loop {self.current_repeat})")

        self.current_demo_index = 0

        step["details"]["completed_demos"] = 0
        step["details"]["current_demo"] = None
        step["details"]["current_repeat"] = self.current_repeat

        for demo_info in step["details"]["demos"].values():
            demo_info["started"] = None
            demo_info["loaded"] = None
            demo_info["ended"] = None
            demo_info["load_time"] = None
            demo_info["status"] = "pending"

        self.sync_metadata()

        return {
            "success": True,
            "action": "repeat"
        }

    def play_next_demo(self):
        result = self.handle_nextdemo_repeat_or_finish()

        if not result["success"]:
            return result

        if result["action"] == "finished":
            return {
                "success": True
            }

        demo_path = self.demo_files[self.current_demo_index]
        demo_name = demo_path.stem

        print(f"[{self.run_id}] play demo: {demo_name}")

        result = self.send_command(f"demo \"{demo_name}\"")

        if not result.get("success"):
            return result

        self.demo_active = True
        self.current_demo_index += 1

        step = self.step()
        demo_info = step["details"]["demos"][demo_name]

        step["details"]["current_demo"] = demo_name

        demo_info["plays"] += 1
        demo_info["started"] = self.run_context.now()
        demo_info["loaded"] = None,
        demo_info["ended"] = None
        demo_info["status"] = "loading"
        demo_info["load_time"] = None

        self.sync_metadata()

        return {
            "success": True
        }

    def finish_demo(self):
        step = self.step()

        current_demo = step["details"]["current_demo"]

        if current_demo:
            demo_info = step["details"]["demos"][current_demo]

            demo_info["ended"] = self.run_context.now()
            demo_info["status"] = "finished"

            step["details"]["completed_demos"] += 1
            self.sync_metadata()

        threading.Timer(
            5.00,
            self.play_next_demo
        ).start()

    def handle_qconsole(self, line):
        line_upper = line.upper()

        finished_markers = [
            "DISCONNECTED",
            "TIMELIMIT HIT",
            "SERVER DISCONNECTED",
        ]

        #
        # map finished loading
        #

        match = re.search(
            r"CL_InitCGame:\s+([\d.]+)\s+seconds",
            line,
            re.IGNORECASE
        )

        if match and self.demo_active:
            load_time = float(match.group(1))

            step = self.step()

            current_demo = step["details"]["current_demo"]

            if current_demo:
                demo_info = step["details"]["demos"][current_demo]

                # prevent duplicate triggers
                if demo_info["status"] == "loading":

                    demo_info["status"] = "running"
                    demo_info["load_time"] = load_time
                    demo_info["loaded"] = self.run_context.now()

                    print(
                        f"[{self.run_id}] "
                        f"demo loaded in {load_time:.2f}s"
                    )

                    self.sync_metadata()

        #
        # demo finished
        #
        for marker in finished_markers:
            if marker not in line_upper:
                continue

            print(f"[{self.run_id}] demo finished")

            self.demo_active = False
            self.finish_demo()
            break