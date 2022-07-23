# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Author Nick Christensen AKA a_girl

This script applies a layer of snow to the map on each map change.  Unlike a previous version
written by someone else, it actually adds a layer instead of repainting the top one.

As you walk, the snow blocks are removed from beneath the player's feet.  This feature
hasn't been tested on a full server so may induce a lot of lag.

Players that land on snow have their fall damage reduced by a customizable amount.

You can change the initial amount of snow on the map (ie 2 blocks deep instead of 1).  This will eventually have an
in game command.

Future versions will include a periodic storm option that will add more snow during gameplay.
"""


from pyspades.server import block_action
from itertools import product
from twisted.internet.reactor import callLater
from pyspades.constants import *

INITIAL_MAP_SNOW = True		#The map loads with a layer of snow already present.
INITIAL_SNOW_AMOUNT = 1		#Number of blocks deep the initial snow is.
FALL_DAMAGE_FACTOR = .25 	#If you land on snow, you take 1/4 normal fall damage.
SNOW_MELT = True
SNOW_MELT_DELAY = .75
MAP_SIZE_X = 512
MAP_SIZE_Y = 512
MAP_SIZE_Z = 64
SNOW_COLOR = (240, 240, 240)
HEAD_HEIGHT = 2.3
BODY_WIDTH = .9


def hash(x, y, z):
	index = (x * (MAP_SIZE_Y * MAP_SIZE_Z)) + (y * (MAP_SIZE_Z)) + (z)
	return index
	
def unhash(index):
	x = index // (x * (MAP_SIZE_Y * MAP_SIZE_Z))
	index %= (MAP_SIZE_Y * MAP_SIZE_Z)
	y = index // (y * (MAP_SIZE_Z))
	index %= (y * (MAP_SIZE_Z))
	z = index
	return x, y, z

def apply_script(protocol, connection, config):
	
	class snowConnection(connection):	
	
		def on_block_removed(self, x, y, z):
			self.protocol.snow_list[hash(x, y, z)] = False
			return connection.on_block_removed(self, x, y, z)
			
		def on_block_build(self, x, y, z):
			if self.name != None:
				self.protocol.snow_list[hash(x, y, z)] = False
	
		def on_line_build(self, points):
			if self.name != None:
				for point in points:
					x, y, z = point[0], point[1], point[2]
					self.protocol.snow_list[hash(x, y, z)] = False
		
		def on_fall(self, damage):
			value = connection.on_fall(self, damage)
			print value, damage
			if value == False:
				return False
			position = self.world_object.position
			x, y, z = position.x, position.y, position.z
			z += HEAD_HEIGHT
			z = int(z)
			for i in self.protocol.position_offset:
				for j in self.protocol.position_offset:
					xTemp = x + i
					yTemp = y + j
					xTemp = int(xTemp)
					yTemp = int(yTemp)
					if self.protocol.map.get_solid(xTemp, yTemp, z) == True:
						if self.protocol.snow_list[hash(xTemp, yTemp, z)] == False:
							return value
			return int(damage * FALL_DAMAGE_FACTOR)
					
	class snowProtocol(protocol):
	
		snow_list = []
		snowmeltgenerator = False
		position_offset = [(-.5 * BODY_WIDTH), (.5 * BODY_WIDTH)]
		
		def on_map_change(self, map):
			self.snowmeltgenerator = False
			if INITIAL_MAP_SNOW == True:
				self.snow_list = [False] * (MAP_SIZE_X * MAP_SIZE_Y * MAP_SIZE_Z)
				for x, y in product(xrange(MAP_SIZE_X), xrange(MAP_SIZE_Y)):
					z = map.get_z(x, y) - 1
					if z < 62:
						for run in xrange(INITIAL_SNOW_AMOUNT):
							map.set_point(x, y, z - run, SNOW_COLOR)
							self.snow_list[hash(x, y, z - run)] = True
			if SNOW_MELT == True:
				self.snowmeltgenerator = True
				self.snow_melt_generator()
			return protocol.on_map_change(self, map)
			
		def snow_melt_generator(self):
			if self.snowmeltgenerator == False:
				return
			player_list = self.players.values()
			for player in player_list:
				section_list = []
				if player.world_object == None:
					continue
				position = player.world_object.position
				x, y, z = position.x, position.y, position.z
				z += HEAD_HEIGHT
				z = int(z)
				for i in self.position_offset:
					for j in self.position_offset:
						xTemp = x + i
						yTemp = y + j
						xTemp = int(xTemp)
						yTemp = int(yTemp)
						section_list.append((xTemp, yTemp, z))
				for point in section_list:
					if self.map.get_solid(point[0], point[1], point[2]) == True:
						if self.snow_list[hash(point[0], point[1], point[2])] == False:
							callLater(SNOW_MELT_DELAY, self.snow_melt_generator)
							return
				for point in section_list:		
					if self.map.get_solid(point[0], point[1], point[2]) == True:
						if self.snow_list[hash(point[0], point[1], point[2])] == True:
							self.break_snow(point[0], point[1], point[2])
			callLater(SNOW_MELT_DELAY, self.snow_melt_generator)
	
		def break_snow(self, x, y, z):
			block_action.player_id = 101
			block_action.x = x
			block_action.y = y
			block_action.z = z
			block_action.value = DESTROY_BLOCK
			self.send_contained(block_action, True)
			self.map.destroy_point(x, y, z)
			
	return snowProtocol, snowConnection

