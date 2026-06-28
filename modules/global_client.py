from dataclasses import dataclass, field
from typing import ClassVar

from modules.build import Build

@dataclass
class GlobalClientFrontend:
    badge_class : str                           = ""
    badge_icon : str                            = ""

@dataclass
class GlobalClient:
    install_dir : str                           = "Unknown"
    build_class : ClassVar[type[Build]]         = None
    frontend: GlobalClientFrontend              = field( default_factory=GlobalClientFrontend )
