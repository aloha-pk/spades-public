# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.constants import *
from commands import add, admin

INVULNERABLE_COLORS = ((0,0,255),(0,255,0))

def apply_script(protocol, connection, config):
    class InvulnerableColorsConnection(connection):

        def on_block_destroy(self, x, y, z, value):
            if value == DESTROY_BLOCK:
                blocks = ((x, y, z),)
            elif value == SPADE_DESTROY:
                blocks = ((x, y, z), (x, y, z + 1), (x, y, z - 1))
            elif value == GRENADE_DESTROY:
                blocks = []
                for nade_x in xrange(x - 1, x + 2):
                    for nade_y in xrange(y - 1, y + 2):
                        for nade_z in xrange(z - 1, z + 2):
                            blocks.append((nade_x, nade_y, nade_z))
            for block in blocks:
                block_info = self.protocol.map.get_point(block[0], block[1], block[2])
                if block_info[0] == True:
                    for color in INVULNERABLE_COLORS:
                        if block_info[1][0] == color[0] and block_info[1][1] == color[1] and block_info[1][2] == color[2]:
                            return False
            return connection.on_block_destroy(self, x, y, z, value)

    return protocol, InvulnerableColorsConnection









