from typing import TYPE_CHECKING

import json
import os
import re
import sys
from modules.constants import REQUIRED_BASE_FILES
from dataclasses import asdict, dataclass, field

import tempfile
import subprocess
from pathlib import Path
import shutil

if TYPE_CHECKING:
    from main import JKForge

@dataclass(slots=True)
class Generator:
    id      : str
    type    : str
    name    : str
    valid   : bool

@dataclass(slots=True)
class Toolchain:
    cmake: bool = False
    git: bool = False
    generators: list[Generator] = field(default_factory=list)

@dataclass(slots=True)
class BaseLocation:
    id      : str
    path    : str

@dataclass(slots=True)
class Config:
    http_port               : int       = field( default=5000 )
    http_use_socketio       : bool      = field( default=True )

    base_locations          : list[BaseLocation]    = field(default_factory=list)
    toolchain               : Toolchain = field(default_factory=Toolchain)
    default_generator       : str      = field( default="vs2022") 

    default_run_preset      : str       = field( default="default")

    qconsole_colors         : bool      = field( default=False) 
    qconsole_strip_colors   : bool      = field( default=True) 

class Configuration:
    def __init__( self, context ) -> None:
        self.context    : 'JKForge' = context

        self.CONFIG_FILE = self.resource_path("config.json")

        self.var : Config = Config()
        self.data = asdict( self.var )

        # debug default config
        #self.print_config()

        print("Starting up, please wait")
        self.load_config()
        self.test_toolchain()

    def has_cmake( self ):
        return shutil.which("cmake") is not None

    def has_git( self ):
        return shutil.which("git") is not None

    def test_generator( self, generator ):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            (tmp / "main.cpp").write_text("int main() { return 0; }")
            (tmp / "CMakeLists.txt").write_text("""
                cmake_minimum_required(VERSION 3.10)
                project(test)
                add_executable(test main.cpp)
            """)

            result = subprocess.run(
                ["cmake", "-G", generator, "-B", "build"],
                cwd=tmp,
                capture_output=True,
                text=True
            )

            return result.returncode == 0

    def get_fallback_generator( self ) -> Generator:
        for generator in self.var.toolchain.generators:
            if not generator.valid:
                continue

            return generator
        
        # should probaly abort and notify use at this point ..
        return Generator(
            id      = "vs2022",
            type    = "vs",
            name    = "Visual Studio 17 2022",
            valid   = True
        )

    def test_toolchain( self ):
        print("Loading toolchain")

        self.var.toolchain.cmake      = self.has_cmake()
        self.var.toolchain.git        = self.has_git()
        self.var.toolchain.generators  = [
            Generator( type="vs", id="vs2015",     name="Visual Studio 14 2015", valid=False),
            Generator( type="vs", id="vs2017",     name="Visual Studio 15 2017", valid=False),
            Generator( type="vs", id="vs2019",     name="Visual Studio 16 2019", valid=False),
            Generator( type="vs", id="vs2022",     name="Visual Studio 17 2022", valid=False)
        ]

        for generator in self.var.toolchain.generators:
            print(f"Testing toolchain: {generator.name}...", end="", flush=True)
            generator.valid = self.test_generator(generator.name)
            print(f"\rTesting toolchain: {generator.name}... {'OK' if generator.valid else 'FAILED'}")

    def get( self ):
        run_presets = self.context.run.load_run_presets()

        return {
            "http_port"             : self.var.http_port,
            "http_use_socketio"     : self.var.http_use_socketio,
            "qconsole_colors"       : self.var.qconsole_colors,
            "qconsole_strip_colors" : self.var.qconsole_strip_colors,
            "clients"               : self.context.client.get_clients_list(),
            "clients_meta"          : self.context.client.get_clients_meta(),
            "toolchain"             : {
                "cmake"         : self.var.toolchain.cmake,
                "git"           : self.var.toolchain.git,
                "generators"    : [asdict(generator) for generator in self.var.toolchain.generators],
            },
            "default_generator" : self.var.default_generator,
            "base_locations"        : [
                {
                    "id"    : location.id,
                    "path"  : self.data["base_locations"][i]["path"],
                    "valid" : self.validate_base_location( self.data["base_locations"][i]["path"] ),
                    "use"   : location.path
                }
                for i, location in enumerate(self.var.base_locations)
            ],
            "default_run_preset"    : self.var.default_run_preset,
            "run_presets"           : list(run_presets.keys())
        }

    def print_config( self ):
        json_config = json.dumps( self.data, indent=4 )
        print(json_config)
        
    def resource_path( self, filename ):
        """Get path to resource, works for dev and PyInstaller exe"""
        if getattr(sys, 'frozen', False):  # running as compiled exe
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, filename)

    def validate_path( self, path_value) -> Path | None:
        if isinstance(path_value, str) and path_value.strip():
            normalized = os.path.abspath(os.path.normpath(path_value))

            if os.path.isabs(normalized) and os.path.exists(normalized):
                return Path(normalized)

        return False

    def resolve_path(self, path_value: str, fallback: str) -> str:
        """
        Resolve and validate a configured path.

        Rules:
        - Must be a non-empty absolute path
        - Must exist
        - Otherwise fallback to resource_path(fallback)
        """

        if isinstance(path_value, str) and path_value.strip():
            normalized = os.path.abspath(os.path.normpath(path_value))

            if os.path.isabs(normalized) and os.path.exists(normalized):
                return normalized

        return self.resource_path(fallback)

    def parse_config( self ):
        """Map this manually for now. use hasattr and setattr later"""
        self.var.http_port              = self.data.get("http_port",            self.var.http_port)
        self.var.http_use_socketio      = self.data.get("http_use_socketio",    self.var.http_use_socketio)

        self.var.base_locations = [
            BaseLocation(
                id      = x.get("id", "Unnamed"),
                path    = self.resolve_path(x.get("path", ""), "base")
            )
            for x in self.data.get("base_locations", [])
        ]

        self.var.default_generator     = self.data.get("default_generator",   self.var.default_generator)
        
        self.var.default_run_preset     = self.data.get("default_run_preset",   self.var.default_run_preset)
       
        self.var.qconsole_colors        = self.data.get("qconsole_colors",      self.var.qconsole_colors)
        self.var.qconsole_strip_colors  = self.data.get("qconsole_strip_colors",self.var.qconsole_strip_colors)

    def load_config( self ):
        print("Loading config")
        if os.path.exists( self.CONFIG_FILE ):
            with open( self.CONFIG_FILE, "r" ) as f:
                self.data = json.load(f)

        else:
            print(f"{self.CONFIG_FILE} is not found, use defaults!")
            self.print_config()
        
        self.parse_config()

    def save_config(self):
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    def fetch(self):
        self.parse_config()
        self.save_config()

        self.context.socket_update_config()

        return {
            "success": True,
            "config": self.get()
        }

    def update(self, key, value):
        self.data[key] = value
        
        return self.fetch()

    def validate_base_location( self, path ) -> dict:
        base : Path  = self.validate_path( path )
        if not base:
            return {
                "state": False,
                "missing": [],
            }

        missing = [f for f in REQUIRED_BASE_FILES if not (base / f).is_file()]

        return {
            "state": len(missing) == 0,
            "missing": missing,
        }
    
    def get_base_location( self, index ):
        locations = self.data.get("base_locations", [])

        if not (0 <= index < len(locations)):
            return False

        return locations[index]

    def add_base_location(self):
        self.data.setdefault("base_locations", []).append({
            "id": f"Base {len(self.data['base_locations']) + 1:03d}",
            "path": ""
        })

        return self.fetch()

    def remove_base_location(self, index):
        locations = self.data.get("base_locations", [])

        if not self.get_base_location( index ):
            return {
                "success": False,
                "error": "Invalid base location index"
            }

        locations.pop(index)

        return self.fetch()

    def update_base_location(self, index, key, value):
        locations = self.data.get("base_locations", [])

        if not self.get_base_location( index ):
            return {
                "success": False,
                "error": "Invalid base location index"
            }

        if key not in ("id", "path"):
            return {
                "success": False,
                "error": f"Invalid key: {key}"
            }

        locations[index][key] = value

        return self.fetch()