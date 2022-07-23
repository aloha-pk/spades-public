# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.constants import *

BLUE_COORD = (96, 256)
GREEN_COORD = (416, 256)

def apply_script(protocol, connection, config):

    class TentProtocol(protocol):

        def on_base_spawn(self, x, y, z, base, entity_id):
            if entity_id is BLUE_BASE:
                map = self.map
                x = BLUE_COORD[0]
                y = BLUE_COORD[1]
                z = map.get_z(BLUE_COORD[0], BLUE_COORD[1])
            if entity_id is GREEN_BASE:
                map = self.map
                x = GREEN_COORD[0]
                y = GREEN_COORD[1]
                z = map.get_z(GREEN_COORD[0], GREEN_COORD[1])
            return (x, y, z)

    return TentProtocol, connection