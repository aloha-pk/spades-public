# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from twisted.internet.reactor import seconds
from pyspades.collision import distance_3d_vector
from pyspades.server import position_data
from pyspades.constants import *
from commands import name, get_player, add, admin, alias
import commands


@name('analyze')
@alias('an')
def analyze_shot(connection, player = None):
	protocol = connection.protocol
	if not protocol.analyzers:
		protocol.analyzers = {}
	if player is None:
		if protocol.analyzers.has_key(connection.name):
			del protocol.analyzers[connection.name]
			connection.send_chat('You are no longer analyzing anyone.')
		else: 
			protocol.analyzers[connection.name] = connection.name
			connection.send_chat('You are now analyzing yourself.')
			connection.hs, connection.bs, connection.ls = 0, 0, 0
	elif player is not None:
		player = get_player(protocol, player)
		if player not in protocol.players:
			raise ValueError()
		else:
			if protocol.analyzers.has_key(connection.name) and player.name == protocol.analyzers[connection.name]:
				del protocol.analyzers[connection.name]
				connection.send_chat('You are no longer analyzing anyone.')
			elif protocol.analyzers.has_key(connection.name) and player.name != protocol.analyzers[connection.name]:
				connection.send_chat('You are no longer analyzing %s.  You are now analyzing %s.' % (protocol.analyzers[connection.name], player.name))
				protocol.analyzers[connection.name] = player.name
				connection.hs, connection.bs, connection.ls = 0, 0, 0
			elif not protocol.analyzers.has_key(connection.name):
				protocol.analyzers[connection.name] = player.name
				connection.send_chat('You are now analyzing %s' % (player.name))
				connection.hs, connection.bs, connection.ls = 0, 0, 0

add(analyze_shot)

def apply_script(protocol, connection, config):
	class analyze_shotsConnection(connection):
		dist = ""
		weap = ""
		hs, bs, ls = 0, 0, 0
		prev_time = None
		body_part = ""

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if self.name in self.protocol.analyzers.values(): 
				body_damage_values = [49, 29, 27]
				limb_damage_values =  [33, 18, 16]
				if type == HEADSHOT_KILL or hit_amount in body_damage_values or hit_amount in limb_damage_values:
					if not grenade:
						dist = int(distance_3d_vector(self.world_object.position, hit_player.world_object.position))
						weap = self.weapon_object.name
						self.pres_time = seconds()
						if self.prev_time is None:
							dt = None
						else: dt = (self.pres_time - self.prev_time) * 1000
						self.prev_time = seconds()
						if type == HEADSHOT_KILL:
							body_part = "HEADSHOT"
						elif hit_amount in body_damage_values:
							body_part = "Body"
						elif hit_amount in limb_damage_values:
							body_part = "Limb"
						for name in self.protocol.analyzers.keys():
							if self.protocol.analyzers[name] == self.name:
								analyzer = get_player(self.protocol, name)
								if analyzer not in self.protocol.players:
									raise ValueError()
								else:
									if body_part == "HEADSHOT":
										analyzer.hs += 1
										counter = analyzer.hs
									elif body_part == "Body":
										analyzer.bs += 1
										counter = analyzer.bs
									elif body_part == "Limb":
										analyzer.ls += 1
										counter = analyzer.ls
									if dt is not None:
										analyzer.send_chat('%s shot %s dist: %d blocks dT: %.0f ms %s %s(%d)' % (self.name, hit_player.name, dist, dt, weap, body_part, counter))
									else:
										analyzer.send_chat('%s shot %s dist: %d blocks dT: NA %s %s(%d)' % (self.name, hit_player.name, dist, weap, body_part, counter))
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)
		def on_weapon_set(self, value):
			if self.name in self.protocol.analyzers.values():
				for name in self.protocol.analyzers:
					if self.protocol.analyzers[name] == self.name:
						analyzer = get_player(self.protocol, name)
						analyzer.hs, analyzer.bs, analyzer.ls = 0, 0, 0
			return connection.on_weapon_set(self, value)	   
								 
		def on_disconnect(self):
			if self.name in self.protocol.analyzers.values():
				for name in self.protocol.analyzers.keys():
					if self.protocol.analyzers[name] == self.name:
						del self.protocol.analyzers[name]
						analyzer = get_player(self.protocol, name)
						if name != self.name:
							analyzer.send_chat('You are no longer analyzing %s.  Player disconnected.' % (self.name))
			if self.protocol.analyzers.has_key(self.name):
				del self.protocol.analyzers[self.name]
			return connection.on_disconnect(self)									  
	class analyze_protocol(protocol):
		analyzers = {}
		def on_map_change(self, map):
			self.analyzers = {}
			protocol.on_map_change(self, map)
	return analyze_protocol, analyze_shotsConnection