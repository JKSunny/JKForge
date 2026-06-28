from typing import TYPE_CHECKING

from modules.constants import *

if TYPE_CHECKING:
    from main import JKForge

from modules.build import Build

from modules.global_client import GlobalClient

from dataclasses import asdict
from modules.clients.EternalJK import GlobalEternalJK
from modules.clients.OpenJK import GlobalOpenJK

class Client:
    def __init__(self, context : 'JKForge'):
        self.context    : 'JKForge' = context
        self.environment = context.environment
        self.config = context.config

        self.hc_client = "EternalJK"

        self.client_types = {
            "EternalJK" : GlobalEternalJK,
            "OpenJK"    : GlobalOpenJK,
        }

    def validate_client(self, client):
        return client in self.client_types

    def get_clients_list( self ):
        return list(self.client_types.keys())

    def get_clients_meta(self):
        return [
            {
                "name": name,
                "frontend": asdict(client_type.frontend),
            }
            for name, client_type in self.client_types.items()
        ]
    
    def get_client( self, env_id ) -> GlobalClient:
        metadata = self.environment.read_metadata(env_id)

        if not env_id:
            return GlobalClient()

        client = self.client_types.get(metadata.get("client"))

        if not client:
            return GlobalClient()

        print(client)
        return client

    def get_client_build_instance( self, global_client : GlobalClient ) -> Build: 
        client_build_class = global_client.build_class

        if not client_build_class:
            return False

        return client_build_class( self )