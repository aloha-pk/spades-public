# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import *
from commands import name, alias
import commands
 
@alias('tsnk')
@name('toggleselfnadekill')
def toggle_self_nade_kill(self):
    if self.protocol.babydontnademe == True:
        self.protocol.babydontnademe = False
        self.protocol.send_chat('You can hurt yourself with nades again.')
    else:
        self.protocol.babydontnademe = True
        self.protocol.send_chat('You canot hurt yourself with grenades anymore!')
commands.add(toggle_self_nade_kill)
 
 
def apply_script(protocol, connection, config):
 
    class nadydonthurtmeprotocol(protocol):
 
        babydontnademe = True
 
    class nadydonthurtmeconnection(connection):
 
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if hit_player == self and self.protocol.babydontnademe:
                return False
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)
 
    return nadydonthurtmeprotocol, nadydonthurtmeconnection
