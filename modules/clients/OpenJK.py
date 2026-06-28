from dataclasses import dataclass
from typing import ClassVar

from modules.configuration import Generator
from modules.build import Build
from modules.global_client import GlobalClient, GlobalClientFrontend

class BuildOpenJK(Build):
    def configure_cmd( self, env_id, metadata, _paths ):
        build_conf = metadata["build_configuration"]
        build_dir   = _paths["build_dir"]
        output_dir  = _paths["output_dir"]
        generator : Generator = _paths["generator"]

        cmake_cmd = [
            "cmake",
            "-G", generator.name,
            f"-DCMAKE_INSTALL_PREFIX={output_dir}"
        ]
        
        if generator.type != "vs":
            cmake_cmd += [f"-DCMAKE_BUILD_TYPE={_paths["build_type"]}"]
        
        if generator.type == "vs":
            cmake_cmd += ["-A", "Win32" if _paths["arch"] == "x86" else "x64"]
        
        if build_conf.get("cmake_options"):
            cmake_cmd += build_conf["cmake_options"].split()

        # Use -B <build_dir> -S .. (source is parent of build folder)
        cmake_cmd += ["-B", str(build_dir), "-S", "."]

        return cmake_cmd

    def build_cmd( self, env_id, metadata, _paths ):
        build_cmd = ["cmake", "--build", ".", "-j"]
        generator : Generator = _paths["generator"]

        if generator.type == "vs":
            build_cmd += ["--config", _paths["build_type"]]

        return build_cmd

    def install_cmd( self, env_id, metadata, _paths ):
        install_cmd = ["cmake", "--install", "."]
        generator : Generator = _paths["generator"]

        if generator.type == "vs":
            install_cmd += ["--config", _paths["build_type"]]

        return install_cmd

@dataclass
class GlobalOpenJK(GlobalClient):
    install_dir     : str                       = "JediAcademy"
    build_class     : ClassVar[type[Build]]     = BuildOpenJK
    frontend: ClassVar[GlobalClientFrontend]    = GlobalClientFrontend(
        badge_class = "badge-openjk",
        badge_icon  = "fa-brands fa-old-republic"
    )