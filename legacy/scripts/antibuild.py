# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.constants import *

def apply_script(protocol, connection, config):
    class AntiBuildConnection(connection):
        def on_block_build_attempt(self, x, y, z):
            return False

        def on_block_destroy(self, x, y, z, value):
            return False
    return protocol, AntiBuildConnection
