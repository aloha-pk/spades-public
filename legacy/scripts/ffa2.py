# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# Free for all script written by Yourself

from random import randint

# If ALWAYS_ENABLED is False, free for all can still be enabled in the map
# metadata by setting the key 'free_for_all' to True in the extensions dictionary
ALWAYS_ENABLED = True

# If WATER_SPANS is True, then players can spawn in water
WATER_SPAWNS = False

HIDE_POS = (0, 0, 63)
from pyspades.constants import *
from pyspades.common import *
from pyspades import world
from pyspades.server import create_player
from pyspades.contained import ChangeTeam as change_team
def apply_script(protocol, connection, config):
	class FreeForAllProtocol(protocol):
		free_for_all = False
		old_friendly_fire = None
		def on_map_change(self, map):
			extensions = self.map_info.extensions
			if ALWAYS_ENABLED:
				self.free_for_all = True
			else:
				if extensions.has_key('free_for_all'):
					self.free_for_all = extensions['free_for_all']
				else:
					self.free_for_all = False
			if self.free_for_all:
				self.old_friendly_fire = self.friendly_fire
				self.friendly_fire = True
			else:
				if self.old_friendly_fire is not None:
					self.friendly_fire = self.old_friendly_fire
					self.old_friendly_fire = None
			return protocol.on_map_change(self, map)

		def on_base_spawn(self, x, y, z, base, entity_id):
			if self.free_for_all:
				return HIDE_POS
			return protocol.on_base_spawn(self, x, y, z, base, entity_id)

		def on_flag_spawn(self, x, y, z, flag, entity_id):
			if self.free_for_all:
				return HIDE_POS
			return protocol.on_flag_spawn(self, x, y, z, flag, entity_id)

	class FreeForAllConnection(connection):
	
		
		def spawn(self, pos = None):
			self.spawn_call = None
			if self.team is None:
				return
			spectator = self.team.spectator
			if not spectator:
				if pos is None:
					x, y, z = self.get_spawn_location()
					x += 0.5
					y += 0.5
					z -= 2.4
				else:
					x, y, z = pos
				returned = self.on_spawn_location((x, y, z))
				if returned is not None:
					x, y, z = returned
				if self.world_object is not None:
					self.world_object.set_position(x, y, z, True)
				else:
					position = Vertex3(x, y, z)
					self.world_object = self.protocol.world.create_object(
						world.Character, position, None, self._on_fall)
				self.world_object.dead = False
				self.tool = WEAPON_TOOL
				self.refill(True)
				create_player.x = x
				create_player.y = y
				create_player.z = z
				create_player.weapon = self.weapon
			create_player.player_id = self.player_id
			create_player.name = self.name
			create_player.team = self.team.id
			if self.filter_visibility_data and not spectator:
				self.send_contained(create_player)
			else:
				if create_player.team == 1:
					create_player.team = 0
				self.send_contained(create_player)
				if create_player.team == 0:
					create_player.team = 1
				for player in self.protocol.connections.values():
					if player != self:
						player.send_contained(create_player)
			if not spectator:
				self.on_spawn((x, y, z))

		def on_spawn_location(self, pos):
			if self.protocol.free_for_all:
				while True:
					x = randint(0, 511)
					y = randint(0, 511)
					z = self.protocol.map.get_z(x, y)
					if z != 63 or WATER_SPAWNS:
						break
				# Magic numbers taken from server.py spawn function
				z -= 2.4
				x += 0.5
				y += 0.5
				return (x, y, z)
			return connection.on_spawn_location(self, pos)

		def on_refill(self):
			if self.protocol.free_for_all:
				return False
			return connection.on_refill(self)

		def on_flag_take(self):
			if self.protocol.free_for_all:
				return False
			return connection.on_flag_take(self)

		
	return FreeForAllProtocol, FreeForAllConnection