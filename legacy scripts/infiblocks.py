# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# -*- coding: utf-8 -*-

from commands import add, alias, admin, get_player
from twisted.internet import reactor
from pyspades.server import weapon_reload
from pyspades.constants import *
import sys

COMMAND_IS_LOUD = False
INFINITE_BLOCKS = True

@alias("iblox")
@admin
def infiniteblocks(connection):
    global INFINITE_BLOCKS
    INFINITE_BLOCKS = not INFINITE_BLOCKS
    on_off = ['OFF', 'ON'][int(INFINITE_BLOCKS)] 

    connection.protocol.irc_say("* %s has toggled infinite blocks %s" % (connection.name, on_off))

    ingame_msg = "Infinite blocks have been toggled %s!" % on_off
    
    if COMMAND_IS_LOUD:
        connection.protocol.send_chat(ingame_msg)
    else:
        return ingame_msg
add(infiniteblocks)

def apply_script(protocol, connection, config):
    class InfiblocksConnection(connection):

        def infiblocks_refill(self):
            health = self.hp
            weapon = self.weapon_object
            ammo = weapon.current_ammo
            reserve = weapon.current_stock
            self.refill()
            self.set_hp(health, type = FALL_KILL)	
            weapon.set_shoot(False)
            weapon.current_stock = reserve
            weapon.current_ammo = ammo		
            weapon_reload.player_id = self.player_id
            weapon_reload.clip_ammo = weapon.current_ammo
            weapon_reload.reserve_ammo = weapon.current_stock
            self.send_contained(weapon_reload)

        def on_block_build(self, x, y, z):
            if INFINITE_BLOCKS and self.blocks <= 5:
                self.infiblocks_refill()
            return connection.on_block_build(self, x, y, z)

        def on_line_build(self, points):
            if INFINITE_BLOCKS and self.blocks <= 25:
                self.infiblocks_refill()
            return connection.on_line_build(self, points)        

    return protocol, InfiblocksConnection