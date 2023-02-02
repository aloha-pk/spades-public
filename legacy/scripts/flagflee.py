# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import admin, add
from twisted.internet import task
from pyspades.common import Vertex3
from pyspades.collision import distance_3d_vector
import traceback

protocol = None
speed = 1

@admin
def flagflee(connection):
	global protocol
	protocol = connection.protocol
	protocol.flagflee = not protocol.flagflee
	if protocol.flagflee:
		protocol.blue_team.flag.realpos = protocol.blue_team.flag.copy()
		protocol.green_team.flag.realpos = protocol.green_team.flag.copy()
		return "Happy April Fool's!"
	else:
		return "Flag will now behave like a boring lump of charcoal :("
add(flagflee)

@admin
def flagspeed(connection, sp = 1):
	global speed
	speed = float(sp)
	return "Done"
add(flagspeed)

def flagthink():
	#print "protocol", protocol
	if protocol is not None and protocol.flagflee:
		try:
			for flag in [protocol.blue_team.flag, protocol.green_team.flag]:
				if distance_3d_vector(flag, flag.realpos) > 5: #TODO: make sure this works
					flag.realpos = flag.copy()
				#print "flag", flag
				steering = Vertex3()
				for player in protocol.connections.values():
					if player.hp > 0 and not player.world_object.sneak:
						#print "player", player
						distance = distance_3d_vector(flag.realpos, player.world_object.position)
						time_think_ahead = distance
						#print "time", time_think_ahead
						predicted_player_pos = player.world_object.position + player.world_object.velocity * time_think_ahead
						#print "prediction", predicted_player_pos
						player_weight = 1 - distance / 32
						if player_weight < 0:
							player_weight = 0
						#print "weight", player_weight
						desired_velocity = (flag.realpos - player.world_object.position).normal() * speed * player_weight
						#print "vel", desired_velocity
						steering += desired_velocity
						#print "steer", steering
				flag.realpos += steering
				#print "realpos", flag.realpos.get()
				ux = int(flag.realpos.x)
				uy = int(flag.realpos.y)
				x = max(10, min(501, ux))
				y = max(10, min(501, uy))
				if x != ux:
					flag.realpos.x = x
				if y != uy:
					flag.realpos.y = y
				z = protocol.map.get_z(x, y)
				flag.realpos.z = z
				flag.set(x, y, z)
				flag.update()
		except Exception as e:
			print "FLAGTHINK IS FAILING"
			print e
			print traceback.format_exc()
			protocol.flagflee = False
task.LoopingCall(flagthink).start(0.1)

def apply_script(protocol, connection, config):
	class FlagFleeProtocol(protocol):
		flagflee = False
		#flagthink = flagthink
		def ffsetup(self):
			global protocol
			protocol = self
			
	return FlagFleeProtocol, connection


