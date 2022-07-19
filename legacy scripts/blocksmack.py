# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import name, add, admin, alias 
from pyspades.constants import BLOCK_TOOL
from pyspades.server import *        
import commands
from pyspades.collision import vector_collision, distance_3d_vector

@alias('bss') 
@admin
@name('blocksmackstrength')
def set_smack_strength(self, value):
    self.protocol.smack_strength = int(value)
    return 'Done, block_smack_strength set to %i.' % (self.protocol.smack_strength)
commands.add(set_smack_strength)

@alias('bsa')
@admin
@name('blocksmackangle')
def set_smack_angle(self, value):
	self.protocol.smack_angle = int(value)
	return 'Done, block_smack_angle set to %i.' % (self.protocol.smack_angle)
commands.add(set_smack_angle)

@alias('bst')
@admin
@name('blocksmacktolerance')
def set_smack_tolerance(self, value):
	self.protocol.smack_tolerance = float(value)
	return 'Done, block_smack_tolerance set to %f.' % (self.protocol.smack_tolerance)
commands.add(set_smack_tolerance)

@alias('bsr')
@admin
@name('blocksmackrange')
def set_smack_range(self,again_a_fucking_value):
	self.protocol.smack_range = int(again_a_fucking_value)
	return 'Done, block_smack_range set to %i.' % (self.protocol.smack_range)
commands.add(set_smack_range)


def apply_script(protocol, connection, config): # im getting crazy when there are not exactly two clear lines before this function

    class blocksmackconnection(connection):

        previous_data_x = 0 # my absolutey
        previous_data_y = 0 # gangster method
        previous_data_z = 0 # for detecting snaps

        def on_orientation_update(self, x, y, z):

            dat_strength = 100 * ( 1 - ( abs(self.previous_data_x)*abs(x) + abs(self.previous_data_y)*abs(y) + abs(self.previous_data_z)*abs(z) ) )# hahaha i have no idea how to calculate a snap angle, but this works miraculously

            if self.tool == BLOCK_TOOL:  # hmm i think a weapon smack sounds cool as well, but still its awesome to kill with blocks

                for babydonthurtme in self.protocol.players.values(): # i was asking myself what is love , hence this

                    if babydonthurtme.team != self.team and babydonthurtme.team != 2: # no ffa, also spectators suck

                        if dat_strength >= self.protocol.smack_angle: # if the required smack angle has been reached:  im still thinking about how awesome my snap detection method is xd

                            if distance_3d_vector(self.world_object.position, babydonthurtme.world_object.position) <= self.protocol.smack_range: # is that even necessary? i have no idea but this gives me the idea to create another command

                                if self != babydonthurtme: # dont know if this is necessary either, but juust in case

                                    if self.world_object.validate_hit(babydonthurtme.world_object, MELEE, self.protocol.smack_tolerance): # i am so going to abuse this function in the next scripts

                                        go, to, hell = babydonthurtme.get_location()  # NOOO you ruined my  'if' streak Y_Y

                                        if self.world_object.can_see(go, to, hell): # attacking through walls would be illogical with blocks right?

                                            if babydonthurtme.hp is not None: # i dont want to smack corpses, although it sounds pretty cool

                                                babydonthurtme.hit(dat_strength * self.protocol.smack_strength, self, MELEE_KILL) # dat irony

            self.previous_data_x = x # mhh it pains me to admit it
            self.previous_data_y = y # but i was not able to shove
            self.previous_data_z = z # everything into one variable

            return connection.on_orientation_update(self, x, y, z)


    class blocksmackprotocol(protocol):

        smack_strength = 4     # default strength of the smack attack
        smack_angle = 6        # default required angle to detect something like a snap
        smack_tolerance = 1.0  # default smack tolerance
        smack_range = 2        # default smack range


    return blocksmackprotocol, blocksmackconnection # huehuehue my 'default' descriptions are so meaningful
