import os
import threading
import socket
import time
import json
from flask import Flask, jsonify, request, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from dataclasses import asdict

from modules.configuration import Configuration
from modules.tray import Tray

from modules.environment import Environment
from modules.client import Client
from modules.clone import Clone
from modules.build import Build

from modules.run import Run

class JKForge:
    def __init__( self ) -> None:
        # configurationn
        self.config : Configuration = Configuration( self )

        # flask instance
        self.app = Flask(__name__)

        # flask socketio instance
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading",)
        self.socketio_interval_sec = 4 
        self.socketio_data = []

        # routes
        self.register_routes()

        # modules
        self.tray : Tray = Tray( self )

        self.environment    = Environment( self )
        self.clone          = Clone( self )
        self.run            = Run( self )
        self.client         = Client( self )

        print("Initialized sucessfully")

    # routes
    def register_routes( self ):

        @self.socketio.on("connect")
        def handle_connect():
            """Send initial application state to a newly connected client."""
            print("Client connected")

            # TODO: unify this with emitter!
            emit("fetch_state", {
                "environments": self.environment.get_environments()
            })

        @self.app.route("/")
        def index():
            return render_template(
                "index.html",
                config=self.config.get()
                #config=self.config.var
            )

        # -------------------------------------------------------------------------
        # Configuration API
        #
        # Frontend configuration management.
        #
        # GET  /get_config
        # POST /update_config
        # -------------------------------------------------------------------------
        @self.app.route("/get_config", methods=["GET"])
        def get_config():
            """Return current application configuration."""
            result = {
                "success": True,
                "config": self.config.get()
            }

            return jsonify(result)


        @self.app.route("/fetch_config", methods=["POST"])
        def fetch_config():
            return jsonify(self.config.fetch())
         
        @self.app.route("/update_config", methods=["POST"])
        def update_config():
            """Update a configuration value."""
            data = request.json

            key = data.get("key")
            value = data.get("value")

            result = self.config.update(key, value)

            return jsonify(result)

        @self.app.route("/confg_base_add", methods=["POST"])
        def confg_base_add():
            result = self.config.add_base_location()

            return jsonify(result)


        @self.app.route("/confg_base_remove", methods=["POST"])
        def confg_base_remove():
            data = request.json

            result = self.config.remove_base_location(
                data.get("index", -1)
            )

            return jsonify(result)


        @self.app.route("/confg_base_update", methods=["POST"])
        def confg_base_update():
            data = request.json

            result = self.config.update_base_location(
                data.get("index", -1),
                data.get("key"),
                data.get("value")
            )

            return jsonify(result)

        # -------------------------------------------------------------------------
        # Environment API
        #
        # Environment lifecycle management.
        #
        # POST /environment_add
        # POST /update_environment_alias
        # POST /set_default_run_preset
        # POST /delete
        #
        # Git:
        # POST /git
        # POST /git_repatch
        #
        # Build:
        # POST /build
        # POST /rebuild
        # -------------------------------------------------------------------------
        @self.app.route("/update_environment_alias", methods=["POST"])
        def update_environment_alias():
            data = request.json or {}
            env_id = data["environment"]
            alias = data["alias"]
            result = self.environment.update_environment_alias( env_id, alias )

            return jsonify(result)
        
        @self.app.route("/environment_add", methods=["POST"])
        def environment_add():
            """Create a new build environment."""
            data = request.json or {}

            # validate client first
            client = data.get("client", None)
            if not client or not self.client.validate_client(client):
                return jsonify({
                    "error"     : f"Invalid client",
                    "success"   : False
                })

            conf = {
                "client"    : client,
                "git"       : data.get("git", "JKSunny/EternalJK"),
                "branch"    : data.get("branch", "master"),
                "commit"    : data.get("commit"),

                "build_configuration": {
                    "type"          : data.get("type", "Release"),
                    "arch"          : data.get("arch", "x86"),
                    "generator"     : data.get("generator", self.config.get_fallback_generator()),
                    "cmake_options" : data.get("cmake_options", "")
                }
            }

            result = self.environment.create(conf)

            return jsonify(result)

        @self.app.route("/set_default_run_preset", methods=["POST"])
        def set_default_run_preset():
            """Set default preset for an environment."""
            data = request.json
            env_id = data["environment"]
            preset_id = data["preset_id"]
            result = self.environment.set_default_run_preset( env_id, preset_id )

            return jsonify(result)

        @self.app.route("/delete", methods=["POST"])
        def delete():
            """Delete an environment and all associated data."""
            data = request.json
            env_id = data["environment"]
            result = self.environment.delete(env_id)

            return jsonify(result)


        @self.app.route("/git", methods=["POST"])
        def git():
            """Clone and prepare an environment repository."""
            data = request.json
            env_id = data["environment"]
            result = self.clone.start( env_id )

            return jsonify(result)

        @self.app.route("/git_repatch", methods=["POST"])
        def git_repatch():
            """Reset repository changes and reapply local patches."""
            data = request.json
            env_id = data["environment"]
            result = self.clone.repatch( env_id )

            return jsonify(result)

        @self.app.route("/build", methods=["POST"])
        def build():
            """Configure, build, and install the selected environment."""
            env_id = request.json["environment"]

            client = self.client.get_client(env_id)
            if not client:
                return jsonify({
                    "error": f"invalid client",
                    "success": False
                })

            build_instance = self.client.get_client_build_instance(client)
            if not build_instance:
                return jsonify({
                    "error": f"invalid build instance",
                    "success": False
                })
            result = build_instance.start( env_id )

            return jsonify(result)

        @self.app.route("/rebuild", methods=["POST"])
        def rebuild():
            """Clean build artifacts and perform a full rebuild."""
            env_id = request.json["environment"]

            client = self.client.get_client(env_id)
            if not client:
                return jsonify({
                    "error": f"invalid client",
                    "success": False
                })

            build_instance = self.client.get_client_build_instance(client)
            if not build_instance:
                return jsonify({
                    "error": f"invalid build instance",
                    "success": False
                })
            result = build_instance.rebuild(env_id)

            return jsonify(result)

        @self.app.post("/get_env_console")
        def get_env_console():
            """Fetch complete get_env_console output for a environment."""
            data = request.json

            env_id = data.get("environment")

            return jsonify({
                "content": self.environment.get_env_console( env_id ),
                "success": True
            })

        # -------------------------------------------------------------------------
        # Run API
        #
        # POST /update_run_alias
        #
        # Presets:
        # POST /get_run_presets
        # POST /save_run_preset
        #
        # Execution:
        # POST /run
        # POST /run_stop
        #
        # Console:
        # POST /run_command
        # POST /get_qconsole
        #
        # Telemetry:
        # POST /get_zone_snapshots
        # POST /get_fps_snapshots
        # -------------------------------------------------------------------------
        @self.app.route("/update_run_alias", methods=["POST"])
        def update_run_alias():
            data = request.json or {}
            env_id = data.get("environment")
            run_id = data.get("run_id")
            alias = data["alias"]
            result = self.run.update_run_alias( env_id, run_id, alias )

            return jsonify(result)
        
        @self.app.route("/get_run_presets", methods=["POST"])
        def get_run_presets():
            """Return available run launcher presets."""
            env_id = request.json["environment"]
            result = self.run.get_run_presets(env_id)
            print(result)
            return jsonify(result)

        @self.app.route("/save_run_preset", methods=["POST"])
        def run_config():
            """Save or update a run launcher preset."""
            data = request.get_json(force=True)
            result = self.run.save_run_preset(data)

            return jsonify(result)

        @self.app.route("/run", methods=["POST"])
        def run():
            """Start a new run instance."""
            env_id = request.json["environment"]
            launcher = request.json.get("launcher", {})

            result = self.run.start(
                env_id,
                launcher=launcher
            )

            return jsonify(result)

        @self.app.route("/run_stop", methods=["POST"])
        def stop_run():
            """Terminate a running instance."""
            env_id = request.json["environment"]
            run_id = request.json["run"]
            result = self.run.cancel( env_id, run_id )

            return jsonify(result)

        # send command
        @self.app.post("/run_command")
        def run_command():
            """Send a console command to a running instance."""
            data = request.json

            env_id = data.get("environment")
            run_id = data.get("run")
            command = data.get("command", "").strip()

            result = self.run.command.send_command( env_id, run_id, command )

            return jsonify(result)
        
        @self.app.post("/get_qconsole")
        def get_qconsole():
            """Fetch complete qconsole output for a run."""
            data = request.json

            env_id = data.get("environment")
            run_id = data.get("run")

            return jsonify({
                "content": self.run.get_qconsole( env_id, run_id ),
                "success": True
            })

        @self.app.post("/get_zone_snapshots")
        def get_zone_snapshots():
            """Fetch zone memory snapshot telemetry."""
            data = request.json

            env_id = data.get("environment")
            run_id = data.get("run")

            return jsonify({
                "snapshots": self.run.get_zone_snapshots( env_id, run_id ),
                "success": True
            })

        @self.app.post("/get_fps_snapshots")
        def get_fps_snapshots():
            """Fetch FPS telemetry."""
            data = request.json

            env_id = data.get("environment")
            run_id = data.get("run")

            return jsonify({
                "snapshots": self.run.get_fps_snapshots( env_id, run_id ),
                "success": True
            })

    # socket
    def socket_update_config( self ):
        """Update config in frontend"""
        self.socketio.emit(
            "config_updated",
            self.config.get()
        )

    def socket_redraw_envconsole( self, env_id):
        self.socketio.emit(
            "env_console_redraw",
            {
                "environment": env_id
            },
            room=f"env:{env_id}"
        )
    def socket_append_envconsole( self, env_id, line ):
        self.socketio.emit(
            "env_console_append",
            {
                "environment": env_id,
                "append": line
            },
            room=f"env:{env_id}"
        )

    def socket_append_qconsole( self, env_id, run_id, line ):
        """Append a console line to connected run viewers."""
        self.socketio.emit(
            "qconsole_append",
            {
                "environment": env_id,
                "run": run_id,
                "append": line + "\n"
            },
            room=f"run:{run_id}"
        )

    def socket_update_loop(self):
        if not self.config.var.http_use_socketio:
            return

        while True:
            try:
                data = {
                    "environments": self.environment.get_environments()
                }
                encoded = json.dumps(data, sort_keys=True)

                if encoded != self.socketio_data:
                    self.socketio.emit("fetch_state", data)
                    self.socketio_data = encoded

            except Exception as e:

                print(f"[socket loop error] {e}")

            time.sleep(self.socketio_interval_sec)

    # server
    def is_flask_running( self ):
        try:
            with socket.create_connection(("127.0.0.1", self.config.var.http_port), timeout=2):
                return True
        except OSError:
            return False

    def open_browser( self ):
        import webbrowser

        webbrowser.open(f"http://localhost:{self.config.var.http_port}")

    def open_browser_when_flask_active( self ):
        while not self.is_flask_running():
            time.sleep(0.1)

        self.open_browser()

    def _run( self ) -> None: 
        """Start flask and open in a browser, if flask is already running, only open the browser"""
        if self.is_flask_running():
            print(f"Already listening on port {self.config.var.http_port}, open browser only")
            self.open_browser()
            return

        # run monitoring
        threading.Thread(target=self.run.monitor.monitor_loop,daemon=True).start()

        # socket
        threading.Thread(target=self.socket_update_loop, daemon=True).start()
 
        # open browser as soon as flask webserver is active
        # threading.Thread(target=self.open_browser_when_flask_active).start()
        
        # add tray icon
        threading.Thread(target=self.tray.run, daemon=False).start()

        print( f"Webserver starting on port {self.config.var.http_port}" )

        if self.config.var.http_use_socketio:
            #
            # env
            #
            @self.socketio.on("join_env_detail")
            def on_join_run(data):
                env_id = data.get("env")

                join_room(f"env:{env_id}")

                print(f"JOIN env:{env_id}")

            @self.socketio.on("laeve_env_detail")
            def on_leave_run(data):
                env_id = data.get("env")

                leave_room(f"env:{env_id}")

                print(f"LEAVE env:{env_id}")

            #
            # run
            #
            @self.socketio.on("join_run")
            def on_join_run(data):
                run_id = data.get("run")

                join_room(f"run:{run_id}")

                print(f"JOIN run:{run_id}")

            @self.socketio.on("leave_run")
            def on_leave_run(data):
                run_id = data.get("run")

                leave_room(f"run:{run_id}")

                print(f"LEAVE run:{run_id}")

            self.socketio.run(
                self.app, 
                port=self.config.var.http_port, 
                host="127.0.0.1",           # allow 'unsafe' for local tray app
                allow_unsafe_werkzeug=True
            )

        else: 
            self.app.run(
                port=self.config.var.http_port,
                host="127.0.0.1"
            )

if __name__ == "__main__":
    app = JKForge()
    app._run()
    