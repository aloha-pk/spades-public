# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# BASIC BOTS
# fakes a connection and partially replicates player behavior
# 
# pathfinding was stripped out since it is unfinished and depended
# on the C++ navigation module
# 
# requires adding the 'local' attribute to server.py's ServerConnection
# 
# *** 201,206 ****
# --- 201,207 ----
#	   last_block = None
#	   map_data = None
#	   last_position_update = None
# +	 local = False
#	   
#	   def __init__(self, *arg, **kw):
#		   BaseConnection.__init__(self, *arg, **kw)
# *** 211,216 ****
# --- 212,219 ----
#		   self.rapids = SlidingWindow(RAPID_WINDOW_ENTRIES)
#	   
#	   def on_connect(self):
# +		 if self.local:
# +			 return
#		   if self.peer.eventData != self.protocol.version:
#			   self.disconnect(ERROR_WRONG_VERSION)
#			   return
# 
# bots should stare at you and pull the pin on a grenade when you get too close
# /addbot [amount] [green|blue]
# /toggleai

from math import cos, sin
from enet import Address
from twisted.internet.reactor import seconds, callLater
from pyspades.protocol import BaseConnection
from pyspades.server import input_data, weapon_input, set_tool, grenade_packet
from pyspades.world import Grenade
from pyspades.common import Vertex3
from pyspades.collision import vector_collision, distance_3d_vector
from pyspades.constants import *
from commands import admin, add, name, get_team
import math
import random
from twisted.internet import reactor
LOGIC_FPS = 4.0

@admin
@name('stationary')
def stationary(connection):
	protocol = connection.protocol
	for bot in protocol.bots:
		bot.stationary = not bot.stationary
	return "Movement Toggled"
add(stationary)

@admin
@name('addbot')
def add_bot(connection, amount = None, team = None):
	protocol = connection.protocol
	if team:
		bot_team = get_team(connection, team)
	blue, green = protocol.blue_team, protocol.green_team
	amount = int(amount or 1)
	for i in xrange(amount):
		if not team:
			bot_team = blue if blue.count() < green.count() else green
		bot = protocol.add_bot(bot_team)
		if not bot:
			return "Added %s bot(s)" % i
	return "Added %s bot(s)" % amount

add(add_bot)

class LocalPeer:
	#address = Address(None, 0)
	address = Address('255.255.255.255', 0)
	roundTripTime = 0.0
	
	def send(self, *arg, **kw):
		pass
	
	def reset(self):
		pass

def apply_script(protocol, connection, config):
	class BotProtocol(protocol):
		bots = None
		ai_enabled = True
		
		def add_bot(self, team):
			if len(self.connections) + len(self.bots) >= 32:
				return None
			bot = self.connection_class(self, None)
			bot.join_game(team)
			self.bots.append(bot)
			return bot
		
		def on_world_update(self):
			if self.bots and self.ai_enabled:
				do_logic = self.loop_count % int(UPDATE_FPS / LOGIC_FPS) == 0
				for bot in self.bots:
					if do_logic:
						bot.think()
					bot.update()
			protocol.on_world_update(self)
		
		def on_map_change(self, map):
			self.bots = []
			protocol.on_map_change(self, map)
		
		def on_map_leave(self):
			for bot in self.bots[:]:
				bot.disconnect()
			self.bots = None
			protocol.on_map_leave(self)
	
	class BotConnection(connection):
		stationary = True
		aim = None
		aim_at = None
		input = None
		acquire_targets = True
		grenade_call = None
		forward = False
		_turn_speed = None
		_turn_vector = None
		def _get_turn_speed(self):
			return self._turn_speed
		def _set_turn_speed(self, value):
			self._turn_speed = value
			self._turn_vector = Vertex3(cos(value), sin(value), 0.0)
		turn_speed = property(_get_turn_speed, _set_turn_speed)
		
		def __init__(self, protocol, peer):
			if peer is not None:
				return connection.__init__(self, protocol, peer)
			self.local = True
			connection.__init__(self, protocol, LocalPeer())
			self.on_connect()
			#~ self.saved_loaders = None
			self._send_connection_data()
			self.send_map()
			
			self.aim = Vertex3()
			self.target_orientation = Vertex3()
			self.turn_speed = 0.15 # rads per tick
			self.input = set()
		
		def join_game(self, team):
			self.name = 'CPUbot%s' % str(self.player_id)
			self.team = team
			self.set_weapon(SMG_WEAPON, True)
			self.protocol.players[(self.name, self.player_id)] = self
			self.on_login(self.name)
			self.admin = True
			self.spawn()
		
		def disconnect(self, data = 0):
			if not self.local:
				return connection.disconnect(self)
			if self.disconnected:
				return
			self.protocol.bots.remove(self)
			self.disconnected = True
			self.on_disconnect()
		
		def think(self):
			self.last_activity = reactor.seconds()
			obj = self.world_object
			pos = obj.position
			if not self.stationary:
				x,y,z = self.world_object.velocity.x,self.world_object.velocity.y,self.world_object.velocity.z
				vel = math.fabs(x)+math.fabs(y)+math.fabs(z) 
				if vel < 0.015 and self.forward:
					self.input.add('jump')
			# find nearby foes
			nougat = 512
			target = None
			if self.acquire_targets:
				for player in self.team.other.get_players():
					dist = distance_3d_vector(self.world_object.position, player.world_object.position)
					if dist < nougat:
						nougat = dist
						target = player
						if dist > 64:
							self.forward = True
						else:
							self.forward = False
				if target is not None:
					self.aim_at = target	
			
				
			# replicate player functionality
			if self.protocol.game_mode == CTF_MODE:
				other_flag = self.team.other.flag
				if vector_collision(pos, self.team.base):
					if other_flag.player is self:
						self.capture_flag()
					self.check_refill()
				if not other_flag.player and vector_collision(pos, other_flag):
					self.take_flag()
		
		def update(self):
			obj = self.world_object
			pos = obj.position
			ori = obj.orientation
			if self.forward and not self.stationary:
				self.input.add('up')
			if self.aim_at and self.aim_at.world_object:
				aim_at_pos = self.aim_at.world_object.position
				self.aim.set_vector(aim_at_pos)
				self.aim -= pos
				distance_to_aim = self.aim.normalize() # don't move this line
				# look at the target if it's within sight
				#if obj.can_see(*aim_at_pos.get()):
				self.target_orientation.set_vector(self.aim)
				# creeper behavior
				if self.acquire_targets:
					if distance_to_aim < 131.0 and self.grenade_call is None:
						self.grenade_call = callLater(0.1, self.throw_grenade,
							0.0, self.aim_at)
			
			# orientate towards target
			diff = ori - self.target_orientation
			diff.z = 0.0
			diff = diff.length_sqr()
			if diff > 0.001:
				p_dot = ori.perp_dot(self.target_orientation)
				if p_dot > 0.0:
					ori.rotate(self._turn_vector)
				else:
					ori.unrotate(self._turn_vector)
				new_p_dot = ori.perp_dot(self.target_orientation)
				if new_p_dot * p_dot < 0.0:
					ori.set_vector(self.target_orientation)
			else:
				ori.set_vector(self.target_orientation)
			
			#if self.grenade_call:
#				self.input.add('primary_fire')
			
			obj.set_orientation(*ori.get())
			self.flush_input()
		
		def flush_input(self):
			input = self.input
			world_object = self.world_object
			z_vel = world_object.velocity.z
			if 'jump' in input and not (z_vel >= 0.0 and z_vel < 0.017):
				input.discard('jump')
			input_changed = not (
				('up' in input) == world_object.up and
				('down' in input) == world_object.down and
				('left' in input) == world_object.left and
				('right' in input) == world_object.right and
				('jump' in input) == world_object.jump and
				('crouch' in input) == world_object.crouch and
				('sneak' in input) == world_object.sneak and
				('sprint' in input) == world_object.sprint)
			if input_changed:
				if not self.freeze_animation:
					world_object.set_walk('up' in input, 'down' in input,
						'left' in input, 'right' in input)
					world_object.set_animation('jump' in input, 'crouch' in input,
						'sneak' in input, 'sprint' in input)
				if (not self.filter_visibility_data and
					not self.filter_animation_data):
					input_data.player_id = self.player_id
					input_data.up = world_object.up
					input_data.down = world_object.down
					input_data.left = world_object.left
					input_data.right = world_object.right
					input_data.jump = world_object.jump
					input_data.crouch = world_object.crouch
					input_data.sneak = world_object.sneak
					input_data.sprint = world_object.sprint
					self.protocol.send_contained(input_data)
			primary = 'primary_fire' in input
			secondary = 'secondary_fire' in input
			input.clear()
			return
			shoot_changed = not (
				primary == world_object.primary_fire and
				secondary == world_object.secondary_fire)
			if shoot_changed:
				if primary != world_object.primary_fire:
					if self.tool == WEAPON_TOOL:
						self.weapon_object.set_shoot(primary)
					if self.tool == WEAPON_TOOL or self.tool == SPADE_TOOL:
						self.on_shoot_set(primary)
				world_object.primary_fire = primary
				world_object.secondary_fire = secondary
				if not self.filter_visibility_data:
					weapon_input.player_id = self.player_id
					weapon_input.primary = primary
					weapon_input.secondary = secondary
					self.protocol.send_contained(weapon_input)
		
		def set_tool(self, tool):
			if self.on_tool_set_attempt(tool) == False:
				return
			self.tool = tool
			if self.tool == WEAPON_TOOL:
				self.on_shoot_set(self.world_object.primary_fire)
				self.weapon_object.set_shoot(self.world_object.primary_fire)
			self.on_tool_changed(self.tool)
			if self.filter_visibility_data:
				return
			set_tool.player_id = self.player_id
			set_tool.value = self.tool
			self.protocol.send_contained(set_tool)
		
		def throw_grenade(self, time_left, target):
			self.grenade_call = None
			if not target.world_object or not self.world_object:
				return
			misschance = 1
			misschance += int(distance_3d_vector(target.world_object.position ,self.world_object.position))/24
			misschance += 1 if target.world_object.sneak else 0
			misschance += 1 if target.world_object.crouch else 0
			u,v,w = target.world_object.velocity.get()
			vel = math.fabs(u)+math.fabs(v)+math.fabs(w) 
			misschance += 1 if int(vel) > 1 else 0
			dice_roll = random.randint(1,misschance)
			successhit = True
			if dice_roll > 1:
				successhit = False
			if not self.hp:
				return
			if self.can_see(target) and target.hp is not None and target.hp > 0:
				#self.input.add('primary_fire')
				self.doshoot()
				if successhit:
					callLater(0.04,target.set_hp,target.hp-5,self,HEADSHOT_KILL)
				callLater(0.04,self.doshoot,False)
				#target.send_chat("dead")
		def doshoot(self,toggle = True):
			self.weapon_object.set_shoot(toggle)
			self.on_shoot_set(toggle)
			if not self.filter_visibility_data:
				weapon_input.player_id = self.player_id
				weapon_input.primary = toggle
				weapon_input.secondary = False
				self.protocol.send_contained(weapon_input)
		def can_see(self,target):
			if target.world_object:
				x,y,z = target.world_object.position.x,target.world_object.position.y,target.world_object.position.z
				if self.world_object.can_see(x,y,z):
					location = self.world_object.cast_ray(256)
					if location and target.world_object:
						if distance_3d_vector(Vertex3(*location),self.world_object.position) < distance_3d_vector(target.world_object.position ,self.world_object.position):
							return False
						return True
					if not location and distance_3d_vector(target.world_object.position ,self.world_object.position) < 132:
						return True
					return False
		def never_do(self):
			self.grenade_call = None
			if not self.hp or not self.grenades:
				return
			self.grenades -= 1
			if self.on_grenade(time_left) == False:
				return
			obj = self.world_object
			grenade = self.protocol.world.create_object(Grenade, time_left,
				obj.position, None, obj.orientation, self.grenade_exploded)
			grenade.team = self.team
			self.on_grenade_thrown(grenade)
			if self.filter_visibility_data:
				return
			grenade_packet.player_id = self.player_id
			grenade_packet.value = time_left
			grenade_packet.position = grenade.position.get()
			grenade_packet.velocity = grenade.velocity.get()
			self.protocol.send_contained(grenade_packet)
		
		def on_spawn(self, pos):
			if not self.local:
				return connection.on_spawn(self, pos)
			self.world_object.set_orientation(1.0, 0.0, 0.0)
			self.aim.set_vector(self.world_object.orientation)
			self.target_orientation.set_vector(self.aim)
			self.set_tool(WEAPON_TOOL)
			self.aim_at = None
			self.acquire_targets = True
			connection.on_spawn(self, pos)
		
		def on_connect(self):
			if self.local:
				return connection.on_connect(self)
			max_players = min(32, self.protocol.max_players)
			protocol = self.protocol
			if len(protocol.connections) + len(protocol.bots) > max_players:
				protocol.bots[-1].disconnect()
			connection.on_connect(self)
		
		def on_disconnect(self):
			for bot in self.protocol.bots:
				if bot.aim_at is self:
					bot.aim_at = None
			connection.on_disconnect(self)
		
		def on_kill(self, killer, type, grenade):
			if self.grenade_call is not None:
				self.grenade_call.cancel()
				self.grenade_call = None
			for bot in self.protocol.bots:
				if bot.aim_at is self:
					bot.aim_at = None
			return connection.on_kill(self, killer, type, grenade)
		
		def _send_connection_data(self):
			if self.local:
				if self.player_id is None:
					self.player_id = self.protocol.player_ids.pop()
				return
			connection._send_connection_data(self)
			
		def on_login(self, name):
			if "cpubot" in name.lower() and not self.local:
				self.kick()
			connection.on_login(self, name)

		def send_map(self, data = None):
			if self.local:
				self.on_join()
				return
			connection.send_map(self, data)
		
		def timer_received(self, value):
			if self.local:
				return
			connection.timer_received(self, value)
		
		def send_loader(self, loader, ack = False, byte = 0):
			if self.local:
				return
			return connection.send_loader(self, loader, ack, byte)
	
	return BotProtocol, BotConnection