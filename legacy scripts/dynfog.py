# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

import commands

def apply_script(protocol, connection, config):
    class FogProtocol(protocol):
        default_fog = (128, 232, 255)
        def on_map_change(self, name):
            self.set_fog_color(getattr(self.map_info.info, 'fog', self.default_fog))
            protocol.on_map_change(self, name) 
    return FogProtocol, connection