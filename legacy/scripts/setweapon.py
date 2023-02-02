# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import weapon_reload
from twisted.internet.reactor import callLater
from commands import name, get_player, add, admin
STRINGMATCH = ["Rifle","SMG","Shotgun","None"]
@admin
def setweapon(connection, value = None):
	if value is None:
		return "0 - Rifle only, 1 - SMG only, 2 - Shotgun only, 3 - No restrictions"
	value = int(value)
	connection.protocol.weapon_select = value
	if value < 3:
		strongk = STRINGMATCH[value]
		connection.protocol.send_chat("*** Weapon Prohibition: %s only ***" % strongk)
		for player in connection.protocol.players.values():
			if player.weapon_object.id != value:
				player.set_team(connection.protocol.spectator_team)
				player.spawn()
	elif value == 3:
		connection.protocol.send_chat("*** Weapon Prohibition disabled ***")
	else:
		return "Invalid #, use /setweapon 0-4"

add(setweapon)
"""
Modified version of GreaseMonkey's smgsucks.py

Public Domain
"""

from pyspades.constants import *

def apply_script(protocol, connection, config):
	class RifleOnlyConnection(connection):
		def on_weapon_set(self, wpnid):
			if wpnid != self.protocol.weapon_select and self.protocol.weapon_select != 3:
				self.send_chat("Weapon forbidden on this server - %s only!" % STRINGMATCH[self.protocol.weapon_select])
				return False
			return connection.on_weapon_set(self, wpnid)
		def set_weapon(self, weapon, local = False, no_kill = False, *args, **kwargs):
			if weapon != self.protocol.weapon_select and self.protocol.weapon_select != 3:
				self.send_chat("Weapon forbidden on this server - %s only!" % STRINGMATCH[self.protocol.weapon_select])
				weapon = self.protocol.weapon_select
				if local:
					no_kill = True
					local = False
			return connection.set_weapon(self, weapon, local, no_kill, *args, **kwargs)
	
	class RifleOnlyProtocol(protocol):
		weapon_select = 0 #0R1M2T,3-noweapons,4-norestr
	return RifleOnlyProtocol, RifleOnlyConnection




