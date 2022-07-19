# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# disable_intel.py last modified 2013-02-22 16:21:27

from pyspades.constants import *

def apply_script(protocol, connection, config):
    class DisableIntelConnection(connection):
        def on_flag_take(self):
            self.send_chat("Intel disabled.")
            return False
            return connection.on_flag_take(self)

    class DisableIntelProtocol(protocol):
        def on_flag_spawn(self, x, y, z, flag, entity_id):
            if entity_id == GREEN_FLAG:
                return (0, 0, 63)
            if entity_id == BLUE_FLAG:
                return (0, 0, 63)
            return protocol.on_flag_spawn(self, x, y, z, flag, entity_id)

    return DisableIntelProtocol, DisableIntelConnection

