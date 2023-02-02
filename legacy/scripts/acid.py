# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from twisted.internet.reactor import callLater
from pyspades.server import block_action
from twisted.internet.task import LoopingCall
from pyspades.constants import *
import random
from commands import name, get_player, add, admin
ACID_COUNT = 70
@admin
def acid(connection, value):
    connection.protocol.acid_eat = int(value)
    return value
add(acid)


def apply_script(protocol, connection, config):
    class AcidConnection(connection):
        acid_loop = None
        
        def do_acid(self):
            if self.acid_pos is None or self.acid_blocks <= 0 or self.weapon != SHOTGUN_WEAPON:
                self.acid_loop.stop()
            x,y,z = self.acid_pos[0], self.acid_pos[1], self.acid_pos[2]
            if x < 0 or x > 511 or y < 0 or y > 511 or z < 1 or z > 61:
                self.acid_loop.stop()
            self.break_block(x,y,z)
            self.acid_blocks -= 1
            map = self.protocol.map
            self.acid_pos = self.get_next_acid(self.acid_pos)
            
        def get_next_acid(self, position):
            acid_list = []
            map = self.protocol.map
            for i in [-1, 1]:
                if self.acid_check(position[0]+i,position[1],position[2]):
                    acid_list.append((position[0]+i,position[1],position[2]))
                if self.acid_check(position[0],position[1]+i,position[2]):
                    acid_list.append((position[0],position[1]+i,position[2]))
                if self.acid_check(position[0],position[1],position[2]+i):
                    acid_list.append((position[0],position[1],position[2]+i))
            if acid_list == []:
                self.acid_blocks = 0
                return position
            return random.choice(acid_list)
            
        def acid_check(self, x, y, z):
            if self.protocol.map.get_solid(x,y,z) and (x > 0 and x < 511 and y > 0 and y < 511 and z > 0 and z < 62):
                return True
            return False
            
        def break_block(self,x,y,z,looped = False):
            self.protocol.map.remove_point(x, y, z)
            block_action.x = x
            block_action.y = y
            block_action.z = z
            block_action.value = DESTROY_BLOCK
            block_action.player_id = self.player_id
            self.protocol.send_contained(block_action, save = True)

        def big_nade(self,cx,cy,cz):
            cx, cy, cz = int(cx),int(cy),int(cz)
            for a in [-1,1]:
                self.do_nade(cx+a,cy,cz)
                self.do_nade(cx,cy+a,cz)
                self.do_nade(cx,cy,cz+a)
                    
        def do_nade(self,x,y,z):
            map = self.protocol.map
            for nade_x in xrange(x - 1, x + 2):
                for nade_y in xrange(y - 1, y + 2):
                    for nade_z in xrange(z - 1, z + 2):
                        if map.destroy_point(nade_x, nade_y, nade_z):
                            self.on_block_removed(nade_x, nade_y, nade_z)
            block_action.x = x
            block_action.y = y
            block_action.z = z
            block_action.value = GRENADE_DESTROY
            block_action.player_id = self.player_id
            self.protocol.send_contained(block_action, save = True)
            self.protocol.update_entities()
            
            
        def on_reset(self):
            if self.acid_loop and self.acid_loop.running:
                self.acid_loop.stop()
            connection.on_reset(self)
       
        def on_disconnect(self):
            if self.acid_loop and self.acid_loop.running:
                self.acid_loop.stop()
            self.acid_loop = None
            connection.on_disconnect(self)

        def on_block_removed(self, x, y, z):
            if self.tool == WEAPON_TOOL and self.acid_loop and self.weapon == SHOTGUN_WEAPON:
                self.acid_pos = (x,y,z)
                self.acid_blocks = self.protocol.acid_eat
                if not self.acid_loop.running:
                    self.acid_loop.start(0.1)
            connection.on_block_removed(self, x, y, z)
            
        def on_block_destroy(self, x, y, z, mode):
            map = self.protocol.map
            if mode == SPADE_DESTROY and self.weapon == SMG_WEAPON:
                self.do_nade(x,y,z)
        
        def on_block_build(self, x, y, z):
            map = self.protocol.map
            if self.weapon == SHOTGUN_WEAPON:
                for nade_x in xrange(x - 1, x + 2):
                    for nade_y in xrange(y - 1, y + 2):
                        if map.build_point(nade_x, nade_y, z, self.color):
                            self.acid_build(nade_x, nade_y, z)
            if self.weapon == RIFLE_WEAPON:
                for addz in xrange(0,4):
                    if map.build_point(x, y, z-addz, self.color):
                        self.acid_build(x, y, z-addz)
        def on_line_build(self, points):
            map = self.protocol.map
            if self.weapon == SMG_WEAPON:
                for point in points:
                    x,y,z = point[0], point[1], point[2]
                    if map.build_point(x+1, y, z, self.color):
                        self.acid_build(x+1, y, z)
                    if map.build_point(x, y, z+1, self.color):
                        self.acid_build(x, y, z+1)
                    if map.build_point(x+1, y, z+1, self.color):
                        self.acid_build(x+1, y, z+1)
        def acid_build(self, x, y, z):
            map = self.protocol.map
            block_action.x = x
            block_action.y = y
            block_action.z = z
            block_action.value = BUILD_BLOCK
            block_action.player_id = self.player_id
            self.protocol.send_contained(block_action, save = True)
            self.protocol.update_entities()

        def grenade_exploded(self, grenade):
            if self.name is None or self.team.spectator:
                return
            if grenade.team is not None and grenade.team is not self.team:
                # could happen if the player changed team
                return
            position = grenade.position
            x = position.x
            y = position.y
            z = position.z
            if x < 0 or x > 512 or y < 0 or y > 512 or z < 0 or z > 63:
                return
            if self.weapon == RIFLE_WEAPON:
                self.big_nade(int(x),int(y),int(z))
            connection.grenade_exploded(self,grenade)

        def on_login(self, name):
            self.acid_loop = LoopingCall(self.do_acid)
            connection.on_login(self, name)


    class AcidProtocol(protocol):      
        acid_eat = ACID_COUNT

    return AcidProtocol, AcidConnection
