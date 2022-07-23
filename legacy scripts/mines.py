# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# Mine script by MuffinTastic
# I apologize in advance.

import math

from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater, seconds

from pyspades.server import orientation_data, grenade_packet
from pyspades.common import coordinates, to_coordinates, Vertex3, make_color
from pyspades.world import Grenade
from pyspades.constants import *
from pyspades.contained import BlockAction, SetColor

from commands import name, add, admin, get_player, InvalidPlayer, alias

MINE_COLOR_DOCILE = (0,255,0)
MINE_COLOR_ACTIVE = [(0,0,255), #team 1 (blue)
					 (255,0,0)] #team 2 (red)

BABEL_PLATFORM_WIDTH  = 100
BABEL_PLATFORM_HEIGHT = 32

BABEL_PLATFORM_WIDTH  /= 2
BABEL_PLATFORM_HEIGHT /= 2

def setBlockColor(self, x, y, z, color):
	set_color = SetColor()
	set_color.value = make_color(*color)
	set_color.player_id = 32
	self.protocol.send_contained(set_color, save = True)

	block_action   = BlockAction()
	block_action.x = x
	block_action.y = y
	block_action.z = z
	block_action.player_id = 32
	block_action.value = DESTROY_BLOCK
	self.protocol.send_contained(block_action, save = True)
	block_action.value = BUILD_BLOCK
	self.protocol.send_contained(block_action, save = True)
	self.protocol.map.set_point(x, y, z, color)
	
def destroyBlock(self, x, y, z):
	block_action = BlockAction()
	block_action.x = x
	block_action.y = y
	block_action.z = z
	block_action.player_id = 32
	block_action.value = DESTROY_BLOCK
	self.protocol.send_contained(block_action, save = True)
	self.protocol.map.destroy_point(x, y, z)



@alias("tm")
@name("togglemine")
@admin
def toggle_mine(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
		player.canPlaceMines = placemine = not player.canPlaceMines
	
		message = 'now place mines' if placemine else 'no longer place mines'
		connection.send_chat("%s can %s" % (player.name, message))
		protocol.irc_say('* %s can %s' % (player.name, message))
	else:
		protocol.mine_place = placemine = not protocol.mine_place
		message = 'enabled' if placemine else 'disabled'
		connection.send_chat("Mine placing is now %s" % (message))
		protocol.irc_say('* Mine placing is now %s' % (message))
add(toggle_mine)

@alias("cm")
@name("clearmines")
@admin
def clear_mines(connection):
	protocol = connection.protocol
	local_pop = []
	
	for minepos, mineinfo in protocol.mine_info.iteritems():
		setBlockColor(connection, minepos[0], minepos[1], minepos[2], mineinfo[4])
		local_pop.append(minepos)
		
	for pos in local_pop:
		del protocol.mine_info[pos]
	del local_pop
	protocol.send_chat("All mines have been cleared by %s!" % connection.name)
add(clear_mines)

@alias("tma")
@name("togglemineadjacency")
@admin
def toggle_mine_adjacency(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
		player.canExplodeAdjacent = explodemine = not player.canExplodeAdjacent
	
		message = 'now explode' if explodemine else 'no longer explode'
		connection.send_chat("%s's adjacent mines can %s" % (player.name, message))
		protocol.irc_say("* %s's adjacent mines can %s" % (player.name, message))
	else:
		protocol.mine_adjacency_explode = explodemine = not protocol.mine_adjacency_explode
		message = 'enabled' if explodemine else 'disabled'
		connection.send_chat("Mine adjacency exploding is now %s" % (message))
		protocol.irc_say('* Mine adjacency exploding is now %s' % (message))
add(toggle_mine_adjacency)

@alias("rfm")
@name("refillmines")
@admin
def refill_mines(connection, *args):
	protocol = connection.protocol
	try:
		player = args[0]
	except IndexError:
		player = None
	
	if player is not None:
		if player == "*":
			for _pList in protocol.players:
				for player in _pList:
					if player.mine_amount <= 5:
						player.mine_amount = 5
					player.send_chat("Mines refilled! %s mines available." % player.mine_amount)
			protocol.irc_say("* %s refilled all players' mines" % (connection.name))
			connection.send_chat("Refilled all players' mines!" % player.name)
		else:
			player = get_player(protocol, player)
			if player.mine_amount <= 5:
				player.mine_amount = 5
			player.send_chat("Mines refilled! %s mines available." % player.mine_amount)
			connection.send_chat("Refilled %s's mines!" % player.name)
			protocol.irc_say("* %s refilled %s's mines" % (connection.name, player.name))
	else:
		player = connection
		if player.mine_amount <= 5:
			player.mine_amount = 5
		player.send_chat("Mines refilled! %s mines available." % player.mine_amount)
		protocol.irc_say("* %s refilled %s's mines" % (connection.name, connection.name))
add(refill_mines)

@alias("tim")
@name("toggleinfinitemines")
@admin
def toggle_infinite_mines(connection):
	protocol = connection.protocol
	protocol.mine_infinite = infmines = not protocol.mine_infinite
	
	message = 'ON' if infmines else 'OFF'
	protocol.send_chat("Infinite mines has been toggled %s" % message)
add(toggle_infinite_mines)

@name("mines")
def mines_avalailable(connection):
	connection.send_chat("%s mines available." % connection.mine_amount)
add(mines_avalailable)
		
def apply_script(protocol, connection, config):
	babel = "babel" == config.get('game_mode', 'ctf') or "babel_script" in config.get('scripts', [])
		
	def coord_on_babel_platform(x, y, z):
		if z <= 2:
			if x >= (256 - BABEL_PLATFORM_WIDTH) and x <= (256 + BABEL_PLATFORM_WIDTH) and y >= (256 - BABEL_PLATFORM_HEIGHT) and y <= (256 + BABEL_PLATFORM_HEIGHT):
				return True
		if z == 1:
			if x >= (256 - BABEL_PLATFORM_WIDTH - 1) and x <= (256 + BABEL_PLATFORM_WIDTH + 1) and y >= (256 - BABEL_PLATFORM_HEIGHT - 1) and y <= (256 + BABEL_PLATFORM_HEIGHT + 1):
				return True
		return False
		
	class MineConnection(connection):
		canPlaceMines = True
		canExplodeAdjacent = True
		rfrsLoop = None
		mine_refreshInterval = 0.4
		mine_killmine = None
		mine_killmessage = True
		mine_amount = 0
		
		def on_spawn(self, pos):
			self.mine_startRefresh()
			self.mine_killmessage = True
			self.mine_amount = 0
			return connection.on_spawn(self, pos)
			
		def on_disconnect(self):
			try:
				if self.rfrsLoop is not None:
					self.rfrsLoop.stop()
			except AssertionError:
				pass
				
			return connection.on_disconnect(self)
			
		def mine_startRefresh(self):
			try:
				if self.rfrsLoop is not None:
					self.rfrsLoop.stop()
			except AssertionError:
				pass
			self.rfrsLoop = LoopingCall(self.mine_refreshWrapper)
			self.rfrsLoop.start(self.mine_refreshInterval)
			
		def mine_refreshWrapper(self):
			#print(self.name + " refresh")
			if self.world_object is not None:
				self.mine_determine(self.get_location(), True)
			if self.mine_amount < 0:
				self.mine_amount = 0
	
		def mine_explode(self, minepos, mineinfo):
			x,y,z = minepos
			if babel == False or babel == True and ((mineinfo[1] == self.protocol.blue_team.id and minepos[0] >= 288) or (mineinfo[1] == self.protocol.green_team.id and minepos[0] <= 224)):
				for nade_x in xrange(x - 1, x + 2):
					for nade_y in xrange(y - 1, y + 2):
						for nade_z in xrange(z - 1, z + 2):
							if self.protocol.map.destroy_point(nade_x, nade_y, nade_z):
								self.on_block_removed(nade_x, nade_y, nade_z)
								destroyBlock(self, nade_x, nade_x, nade_x)
		
			position = Vertex3(x, y, z)
			velocity = Vertex3(0.0, 0.0, 0.0)
			grenade = self.protocol.world.create_object(Grenade, 0.0,
				position, None, velocity, self.grenade_exploded)
			grenade.name = 'mine'
			grenade.fuse = 0.01
			grenade_packet.value = grenade.fuse
			grenade_packet.position = position.get()
			grenade_packet.velocity = velocity.get()
			self.protocol.send_contained(grenade_packet)
			
			if connection.on_block_destroy(self, minepos[0], minepos[1], minepos[2], GRENADE_DESTROY) == False: 
				setBlockColor(self, minepos[0], minepos[1], minepos[2], mineinfo[4])
		
		def mine_determine(self, xyz, walk = False, grenade = False):
			xyz = (math.floor(xyz[0]), math.floor(xyz[1]), math.floor(xyz[2]))
			local_pop = {}
			
			def __killmineoff():
				self.mine_killmine = None
				
			for minepos, mineinfo in self.protocol.mine_info.iteritems():
				try:
					mineOwner = get_player(self.protocol, "#%s" % mineinfo[2])
				except InvalidPlayer:
					mineOwner = None
				if self.hp is not None:
					if walk == True:
						if (minepos[0]-xyz[0] > -3 and minepos[0]-xyz[0] < 3) and (minepos[1]-xyz[1] > -3 and minepos[1]-xyz[1] < 3) and (minepos[2]-xyz[2] > -3 and minepos[2]-xyz[2] < 5):
							if self.team.id != mineinfo[1]:
								if mineinfo[3]:
									if mineOwner is not None:
										self.mine_killmine = (mineinfo[0], mineinfo[2], mineOwner)
										mineOwner.mine_explode(minepos, mineinfo)
									else:
										self.mine_killmine = (mineinfo[0], mineinfo[2], None)
										self.mine_explode(minepos, mineinfo)
									callLater(2.0, __killmineoff)
									local_pop[minepos] = mineinfo
									
					elif grenade == True:
						if (minepos[0]-xyz[0] > -3 and minepos[0]-xyz[0] < 3) and (minepos[1]-xyz[1] > -3 and minepos[1]-xyz[1] < 3) and (minepos[2]-xyz[2] > -3 and minepos[2]-xyz[2] < 3):
							if mineinfo[3]:
								if mineOwner is not None:
									self.mine_killmine = (mineinfo[0], mineinfo[2], mineOwner)
									mineOwner.mine_explode(minepos, mineinfo)
								else:
									self.mine_killmine = (mineinfo[0], mineinfo[2], None)
									self.mine_explode(minepos, mineinfo)
								callLater(2.0, __killmineoff)
								local_pop[minepos] = mineinfo
					elif not walk and not grenade and minepos == xyz:
						if self.tool != SPADE_TOOL:
							if mineinfo[3]:
								if mineOwner is not None:
									mineOwner.mine_explode(minepos, mineinfo)
									self.mine_killmine = (mineinfo[0], mineinfo[2], mineOwner)
								else:
									self.mine_explode(minepos, mineinfo)
									self.mine_killmine = (mineinfo[0], mineinfo[2], None)
								callLater(2.0, __killmineoff)
								
							if mineinfo[2] == self.player_id:
								self.send_chat("You have destroyed one of your mines!")
							else:
								self.send_chat("You have destroyed %s's mine!" % (mineinfo[0]))
								if mineOwner is not None:
									mineOwner.send_chat("%s (%s) destroyed your mine!" % (self.name, self.team.name))
						else:
							self.mine_amount += (1*(not self.protocol.mine_infinite))
							msg = "%s mines available" % self.mine_amount if not self.protocol.mine_infinite else ""
							if mineinfo[2] == self.player_id:
								self.send_chat("You have removed one of your mines! %s" % msg)
							else:
								self.send_chat("You have removed %s's mine! %s" % (mineinfo[0], msg))
								if mineOwner is not None:
									mineOwner.send_chat("%s (%s) removed your mine!" % (self.name, self.team.name))
						local_pop[minepos] = mineinfo
					
			for popposition, mineinfo in local_pop.iteritems():
				self.protocol.mine_info.pop(popposition, None)
			del local_pop
			
		def on_kill(self, killer, type, grenade):
			if type == GRENADE_KILL:
				if self.mine_killmine is not None and self.mine_killmessage == True:
					if self.mine_killmine[1] != self.player_id:
						self.send_chat("%s killed you with a mine!" % (self.mine_killmine[0]))
						if self.mine_killmine[2] is not None:
							self.mine_killmine[2].send_chat("You killed %s with a mine!" % (self.name))
						self.mine_killmessage = False
					else:
						self.send_chat("You killed yourself with your own mine!")
						self.mine_killmessage = False
			return connection.on_kill(self, killer, type, grenade)
						
		def place_mine(self, x, y, z):
			if x < 0 or y < 0 or z < 0 or x >= 512 or y >= 512 or z >= 62:
				return False
			if self.canPlaceMines and self.protocol.mine_place:
				if self.mine_amount > 0 or self.protocol.mine_infinite:
					if not (x, y, z) in self.protocol.mine_info.keys():
						originalBlockColor = self.protocol.map.get_color(x, y, z)
						setBlockColor(self, x, y, z, MINE_COLOR_DOCILE)
						mineinfo = self.protocol.mine_info[(x, y, z)] = (self.name, self.team.id, self.player_id, False) # 4th arg: active
						
						print self.team.id
						
						print self.protocol.blue_team.id
						print self.protocol.green_team.id
						
						def activateMine():
							if (x, y, z) in self.protocol.mine_info.iterkeys():
								if self.team is not None:
									try:
										if not mineinfo[3]:
											setBlockColor(self, x, y, z, MINE_COLOR_ACTIVE[mineinfo[1]])
											self.protocol.mine_info[(x, y, z)] = (mineinfo[0], mineinfo[1], mineinfo[2], True, originalBlockColor)
									except KeyError:
										pass
								else:
									setBlockColor(self, x, y, z, originalBlockColor)
									if (x, y, z) in self.protocol.mine_info.iterkeys():
										del self.protocol.mine_info[(x, y, z)]
							
						self.mine_amount -= (1*(not self.protocol.mine_infinite))
						msg = "%s mines available" % self.mine_amount if not self.protocol.mine_infinite else ""
						self.send_chat("You have placed a mine! %s" % msg)
						callLater(2.5, activateMine)
					else:
						self.send_chat("A mine already exists there!")
				else:
					self.send_chat("You don't have any mines! Go to the tent to refill.")
			else:
				self.send_chat("You cannot place mines!")
			
			return True
		
		def on_secondary_fire_set(self, secondary):
			lookPos = self.world_object.cast_ray(8)
			if self.tool == GRENADE_TOOL and secondary and lookPos is not None:
				if babel == True:
					if not coord_on_babel_platform(*lookPos):
						if self.team is self.protocol.blue_team:
							if self.world_object.position.x >= 128 and self.world_object.position.x <= 211 and self.world_object.position.y >= 240 and self.world_object.position.y <= 272:
								self.send_chat("You can't place mines near your team's tower!")
							else:
								self.place_mine(*lookPos)
								
						if self.team is self.protocol.green_team:
							if self.world_object.position.x >= 301 and self.world_object.position.x <= 384 and self.world_object.position.y >= 240 and self.world_object.position.y <= 272:
								self.send_chat("You can't place mines near your team's tower!")
							else:
								self.place_mine(*lookPos)
				else:
					self.place_mine(*lookPos)
			return connection.on_secondary_fire_set(self, secondary)
		
		def on_block_destroy(self, x, y, z, mode):
			if self.canExplodeAdjacent == True and self.protocol.mine_adjacency_explode == True:
				if mode == GRENADE_DESTROY:
					callLater(0.3, lambda: self.mine_determine((x, y, z), False, True))
				else:
					self.mine_determine((x, y, z))
			else:
				self.mine_determine((x, y, z))
			
			return connection.on_block_destroy(self, x, y, z, mode)
		
		def on_refill(self):
			if self.mine_amount < 5:
				self.mine_amount = 5
				self.send_chat("Mines refilled! %s mines available." % self.mine_amount)
			else:
				self.send_chat("Mines are already full! %s mines available." % self.mine_amount)
			return connection.on_refill(self)
	
	class MineProtocol(protocol):
		mine_info = None
		clearInterval = 0.2
		mine_adjacency_explode = True
		mine_place = True
		mine_infinite = False
		
		def __init__(self, *arg, **kw):
			protocol.__init__(self, *arg, **kw)
			self.mine_info = {}
			self.clearLoop = LoopingCall(self.clearInvMines)
			self.clearLoop.start(self.clearInterval)
		
		def clearInvMines(self):
			mine_pop = []
			#print("server refresh")
			for minepos, mineinfo in self.mine_info.iteritems():
				is_solid = self.map.get_solid(minepos[0], minepos[1], minepos[2])
				if is_solid == False:
					mine_pop.append(minepos)
					
			for position in mine_pop:
				self.mine_info.pop(position, None)
				mine_pop.remove(position)
				
		def on_map_change(self, map):
			self.mine_info = None
			self.mine_info = {}
			
			return protocol.on_map_change(self, map)
			
	return MineProtocol, MineConnection