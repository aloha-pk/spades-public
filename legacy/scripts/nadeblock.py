# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
nadeblock.py, it disables nade damage. what's more to know?

originally some HORRIBLE gutted version of trollscript, lostmotel's fault. now 100% better!

maintainer: MuffinTastic
"""

from pyspades.constants import *
 
def apply_script(protocol, connection, config):
 
    class NadeBlockConnection(connection):
        def on_block_destroy(self, x, y, z, mode):
            if mode == GRENADE_DESTROY:
                return False
            return connection.on_block_destroy(self, x, y, z, mode)
 
    return protocol, NadeBlockConnection
    