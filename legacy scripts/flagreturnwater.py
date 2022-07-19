# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.constants import *
from commands import name, reset_game

def apply_script(protocol, connection, config):
    class FlagWaterConnection(connection):
        def on_flag_drop(self):
            flag = self.team.other.flag
            if flag.z == 63:
                    reset_game(self)
            return connection.on_flag_drop(self)
    return protocol, FlagWaterConnection
