# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
push.py last modified 8:17 PM 3/11/2016
Contributors: danhezee, StackOverflow, izzy, Danke, MuffinTastic

The concept:
    Each team spawns at a set location with the enemy intel.
    They must "push" the intel towards their control point, which is also at a set location.

How to setup new maps:
    Spawn and CP locations must be configured via extensions in the map's map_name.txt metadata. Example:

extensions = {
    'push': True,
    'push_spawn_range' : 5,
    'push_blue_spawn' : (91, 276, 59),
    'push_blue_cp' : (91, 276, 59),
    'push_green_spawn' : (78, 86, 59),
    'push_green_cp' : (78, 86, 59),
    'water_damage' : 100
}
"""

from pyspades.constants import *
from random import randint
from commands import add, admin
from twisted.internet.task import LoopingCall
from pyspades.common import make_color
from pyspades.server import set_color, block_action
import random

# If ALWAYS_ENABLED is False, then the 'push' key must be set to True in
# the 'extensions' dictionary in the map's map_name.txt metadata
ALWAYS_ENABLED = True

#team is associated intel team
def reset_intel(protocol, team):
    extensions = protocol.map_info.extensions

    if team is protocol.green_team and extensions.has_key('push_blue_spawn'):
        z = protocol.map.get_z(*extensions.get('push_blue_spawn'))
        pos = (extensions.get('push_blue_spawn')[0], extensions.get('push_blue_spawn')[1], z)

    if team is protocol.blue_team and extensions.has_key('push_green_spawn'):
        z = protocol.map.get_z(*extensions.get('push_green_spawn'))
        pos = (extensions.get('push_green_spawn')[0], extensions.get('push_green_spawn')[1], z)

    team.flag.set(*pos)
    team.flag.update()
    protocol.send_chat("The %s intel has been reset." % team.name)

@admin
def resetblueintel(connection):
    reset_intel(connection.protocol, connection.protocol.blue_team)

@admin
def resetgreenintel(connection):
    reset_intel(connection.protocol, connection.protocol.green_team)

add(resetblueintel)
add(resetgreenintel)

def get_entity_location(self, entity_id):
    extensions = self.protocol.map_info.extensions

    if entity_id == BLUE_BASE and extensions.has_key('push_blue_cp'):
        return extensions['push_blue_cp']
    elif entity_id == GREEN_BASE and extensions.has_key('push_green_cp'):
        return extensions['push_green_cp']
    #this next part might seem counter intuitive but you need the blue intel to spawn near the greens and vice versa
    elif entity_id == BLUE_FLAG and extensions.has_key('push_green_spawn'):
        return extensions['push_green_spawn']
    elif entity_id == GREEN_FLAG and extensions.has_key('push_blue_spawn'):
        return extensions['push_blue_spawn']
    
def get_spawn_location(connection):
    extensions = connection.protocol.map_info.extensions
    #distance from spawn center to randomly spawn in
    spawn_range = 5;
    if extensions.has_key('push_spawn_range'):
        spawn_range = extensions['push_spawn_range']
        
    if connection.team is connection.protocol.blue_team:
        if extensions.has_key('push_blue_spawn'):
            xb = extensions.get('push_blue_spawn')[0]
            yb = extensions.get('push_blue_spawn')[1]
            xb += randint(-spawn_range, spawn_range)
            yb += randint(-spawn_range, spawn_range)
            return (xb, yb, connection.protocol.map.get_z(xb, yb))
    
    if connection.team is connection.protocol.green_team:
        if extensions.has_key('push_green_spawn'):
            xb = extensions.get('push_green_spawn')[0]
            yb = extensions.get('push_green_spawn')[1]
            xb += randint(-spawn_range, spawn_range)
            yb += randint(-spawn_range, spawn_range)
            return (xb, yb, connection.protocol.map.get_z(xb, yb))

def apply_script(protocol, connection, config):
    class PushConnection(connection):
        def on_login(self, name):
            self.mylastblocks = [(-4,-1,-14),(-11,-5,-9),(-19,-20,-8),(-5,-2,-5),(-19,-20,0)]
            return connection.on_login(self, name)
            
        def random_color(self):
            color = (0, random.randint(min(32,self.team.color[1]), max(self.team.color[1],32))*self.team.color[1]/255,
                        random.randint(min(32,self.team.color[2]), max(self.team.color[2],32))*self.team.color[2]/255 )
            self.color = color
            set_color.player_id = self.player_id
            set_color.value = make_color(*color)
            self.send_contained(set_color)
            self.protocol.send_contained(set_color, save = True)
            
        def check_block_same_team(self, block):
            block_info = self.protocol.map.get_point(block[0], block[1], block[2])
            if block_info[0] == True:
                if self.team is self.protocol.blue_team:
                    if block_info[1][0] == 0 and block_info[1][1] == 0 and block_info[1][2] > 0:
                        return True
                elif self.team is self.protocol.green_team:
                    if block_info[1][0] == 0 and block_info[1][1] > 0 and block_info[1][2] == 0:
                        return True
            return False

        def build_block(self,x,y,z,looped = False):
            if (x < 0 or x > 511 or y < 0 or y > 511 or z < 1 or z > 61) is False:
                self.protocol.map.set_point(x, y, z, self.color)
                block_action.x = x
                block_action.y = y
                block_action.z = z
                block_action.value = BUILD_BLOCK
                block_action.player_id = self.player_id
                self.protocol.send_contained(block_action, save = True)

        def on_line_build_attempt(self, points):
            if connection.on_line_build_attempt(self, points) is not False:
                for point in points:
                    x,y,z = point[0], point[1], point[2]
                    
                    if not self.check_block_same_team(point):
                        self.mylastblocks.pop(0)
                        self.mylastblocks.append((x,y,z))
                        
                    self.random_color()
                    self.build_block(x,y,z)
            return False

        def on_block_build_attempt(self, x, y, z):
            if connection.on_block_build_attempt(self, x, y, z) is not False:
                self.mylastblocks.pop(0)
                self.mylastblocks.append((x,y,z))
                self.random_color()
                self.build_block(x,y,z)
            return False

        def on_block_destroy(self, x, y, z, value):
            if not (self.admin or self.user_types.moderator or self.user_types.guard or self.user_types.trusted):
                if value == DESTROY_BLOCK:
                    blocks = ((x, y, z),)
                elif value == SPADE_DESTROY:
                    blocks = ((x, y, z), (x, y, z + 1), (x, y, z - 1))
                elif value == GRENADE_DESTROY:
                    blocks = []
                    for nade_x in xrange(x - 1, x + 2):
                        for nade_y in xrange(y - 1, y + 2):
                            for nade_z in xrange(z - 1, z + 2):
                                blocks.append((nade_x, nade_y, nade_z))
                
                destroy_blocks = True
                
                for block in blocks:
                    if not (block in self.mylastblocks):
                        if self.check_block_same_team(block):
                            self.send_chat("You can't destroy your team's blocks. Attack the enemy!")
                            destroy_blocks = False
                            break
                            
                for block in blocks:
                    if block in self.mylastblocks and destroy_blocks:
                        self.mylastblocks.remove(block)
                        self.mylastblocks.append((-1,-1,-1))
                
                return connection.on_block_destroy(self, x, y, z, value) if destroy_blocks else False
                                
            return connection.on_block_destroy(self, x, y, z, value)

    class PushProtocol(protocol):
        game_mode = CTF_MODE
        push = False
        check_loop = None

        def check_intel_locations(self):
            if self.blue_team.flag is not None:
                if self.blue_team.flag.get()[2] >= 63:
                    reset_intel(self, self.blue_team)
            if self.green_team.flag is not None:
                if self.green_team.flag.get()[2] >= 63:
                    reset_intel(self, self.green_team)

        def on_map_change(self, map):
            extensions = self.map_info.extensions
            if ALWAYS_ENABLED:
                self.push = True
            else:
                if extensions.has_key('push'):
                    self.push = extensions['push']
                else:
                    self.push = False
            if self.push:
                self.map_info.get_entity_location = get_entity_location
                self.map_info.get_spawn_location = get_spawn_location
                self.check_loop = LoopingCall(self.check_intel_locations)
                self.check_loop.start(0.5)
            return protocol.on_map_change(self, map)

    return PushProtocol, PushConnection