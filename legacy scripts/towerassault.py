# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
babel_script.py last modified 2014-04-04 13:55:07
Original script by Yourself
Anti grief by izzy
Return intel dropped from platform bug fix by a_girl

Release thread:
http://www.buildandshoot.com/viewtopic.php?t=2586

How to install and configure:

1) Save babel_script.py to 'scripts' folder: http://aloha.pk/files/aos/pyspades/feature_server/scripts/babel_script.py
2) Save babel.py to 'scripts' folder: http://aloha.pk/files/aos/pyspades/feature_server/scripts/babel.py
3) Set game_mode to "babel" in config.txt
4) Add "babel_script" to scripts list in config.txt
5) Set cap_limit to "10" in config.txt
"""

from pyspades.constants import *
from random import randint
from twisted.internet import reactor
import commands

def apply_script(protocol, connection, config):
	class TowerAssaultProtocol(protocol):
		def ta_get_pos(self, entity_id):
			if entity_id == BLUE_BASE:
				return (173, 255, 1)
			elif entity_id == GREEN_BASE:
				return (338, 255, 1)
			elif entity_id == BLUE_FLAG:
				return (188,255,7)
			elif entity_id == GREEN_FLAG:
				return (323,255,7)
				
		def on_game_end(self):
			self.blue_team.set_flag()
			self.green_team.set_flag()
			self.blue_team.set_base()
			self.green_team.set_base()
			return protocol.on_game_end(self)

		def on_flag_spawn(self, x, y, z, flag, entity_id):
			pos = self.ta_get_pos(entity_id)
			x,y,z = pos
			protocol.on_flag_spawn(self, x, y, z, flag, entity_id)
			return pos
			
		def on_base_spawn(self, x, y, z, base, entity_id):
			pos = self.ta_get_pos(entity_id)
			x,y,z = pos
			protocol.on_base_spawn(self, x, y, z, base, entity_id)
			return pos

	class TowerAssaultConnection(connection):
		def return_flag(self):
			self.protocol.send_chat("%s flag returned to base!" % self.team.other.name)
			self.drop_flag()
			self.team.other.set_flag()
			self.team.other.flag.update()

		def on_kill(self, killer, type, grenade):
			if self.team.other and self.team.other.flag.player == self:
				if killer is None:
					self.return_flag()
				elif killer.team == self.team:
					self.return_flag()
			return connection.on_kill(self, killer, type, grenade)
			
		def invalid_build_position(self, x, y, z):
			if x < 190 or x > 322:
				return True
			return False

		def on_block_build_attempt(self, x, y, z):
			if self.invalid_build_position(x, y, z):
				self.send_chat("This area is protected from building!")
				return False
			return connection.on_block_build_attempt(self, x, y, z)
		def ta_get_spawn(self):
			y = randint(249,262)
			if self.team == self.protocol.blue_team:
				x = randint(172,184)
			else:
				x = randint(328,339)
			return (x, y, self.protocol.map.get_z(x, y)-1)
			
		def on_spawn_location(self, pos):
			return self.ta_get_spawn()
			
		def on_line_build_attempt(self, points):
			for point in points:
				if self.invalid_build_position(*point):
					self.send_chat("This area is protected from building!")
					return False
			return connection.on_line_build_attempt(self, points)

		# anti team destruction
		def on_block_destroy(self, x, y, z, mode):
			if self.invalid_build_position(x,y,z):
				self.send_chat("This area is protected from destruction!")
				return False
			return connection.on_block_destroy(self, x, y, z, mode)
	return TowerAssaultProtocol, TowerAssaultConnection

