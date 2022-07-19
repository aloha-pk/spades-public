# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

#no_top.py by izzy
#add to the map_name.txt of any map and remove # to auto kill players who walk on the very top of the map:
#extensions = {
#    'no_top': True
#}
from pyspades.constants import *
def apply_script(protocol, connection, config):
    class NoTopConnection(connection):
        def on_position_update(self):
            if self.protocol.no_top_enabled:
                if self.world_object.position.z <= 0:
                    self.kill()
            return connection.on_position_update(self)

    class NoTopProtocol(protocol):
        no_top_enabled = False
        def on_map_change(self, map):
            extensions = self.map_info.extensions
            if extensions.has_key('no_top'):
                self.no_top_enabled = extensions['no_top']
            else:
                self.no_top_enabled = False
            return protocol.on_map_change(self, map)

    return NoTopProtocol, NoTopConnection















