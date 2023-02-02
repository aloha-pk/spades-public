# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import orientation_data, weapon_reload
from pyspades.constants import *
from commands import add, admin, name, reset_game

@admin
@name('melee')
def meleetoggle(connection):
    protocol = connection.protocol
    protocol.melee_mode = not protocol.melee_mode
    connection.send_chat("Melee is %s" % ['off', 'on'][protocol.melee_mode])

add(meleetoggle)

def apply_script(protocol, connection, config):
    class MeleeProtocol(protocol):
        def __init__(self, *arg, **kw):
            protocol.__init__(self, *arg, **kw)
            self.melee_mode = True
    
    class MeleeConnection(connection):
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if self.protocol.melee_mode and (type != MELEE_KILL or (hit_player.tool == BLOCK_TOOL and hit_player.has_intel == False)):
                if hit_player.tool == BLOCK_TOOL and hit_player.team != self.team:
                    hit_player.shield -= 1
                    hit_player.send_chat('Shield status %s%%' % hit_player.shield)
                if hit_player.shield > 0:
                    return False
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)
        
        def on_grenade(self, time_left):
            if self.protocol.melee_mode:
                return False
        
        def on_flag_capture(self):
            self.has_intel = False
            return connection.on_flag_capture(self)
        
        def on_flag_take(self):
            self.has_intel = True
            return connection.on_flag_take(self)
        
        def on_join(self):
            self.has_intel = False
            return connection.on_join(self)
        
        def on_spawn(self, pos):
            self.clear_ammo()
            self.shield = 100

        def on_refill(self):
            self.clear_ammo()

        def on_flag_drop(self):
            self.has_intel = False
            flag = self.team.other.flag
            if flag.z == 63:
                    reset_game(self)
            return connection.on_flag_drop(self)
            
        def on_block_build_attempt(self, x, y, z):
            self.refill()
            self.clear_ammo()
            return connection.on_block_build_attempt(self, x, y, z)
          
        # clear_ammo() method by infogulch
        def clear_ammo(self):
            weapon_reload.player_id = self.player_id
            weapon_reload.clip_ammo = 0
            weapon_reload.reserve_ammo = 0
            self.grenades = 0
            self.weapon_object.clip_ammo = 0
            self.weapon_object.reserve_ammo = 0
            self.send_contained(weapon_reload)
    
    return MeleeProtocol, MeleeConnection
