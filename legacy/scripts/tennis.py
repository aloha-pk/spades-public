# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# tennis.py last modified 2013-03-05 13:39:41
# complements tennis.vxl
# maintained by izzy

from pyspades.constants import *
from math import sqrt

def point_distance2(c1, c2):
    if c1.world_object is not None and c2.world_object is not None:
        p1 = c1.world_object.position
        p2 = c2.world_object.position
        return (p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2

def apply_script(protocol, connection, config):
    class TennisConnection(connection):
        def __init__(self, *arg, **kw):
            connection.__init__(self, *arg, **kw)

        def on_flag_take(self):
            self.send_chat("Intel disabled.")
            return False
            return connection.on_flag_take(self)

        def on_block_build_attempt(self, x, y, z):
            self.send_chat('Building disabled.')
            return False
            return connection.on_block_build_attempt(self, x, y, z)

        def on_line_build_attempt(self, points):
            self.send_chat('Building disabled.')
            return False
            return connection.on_line_build_attempt(self, points)

        def on_join(self):
            self.send_chat('Block destruction disabled.')
            return connection.on_join(self)

        def on_hit(self, hit_amount, hit_player, type, grenade):
            result = connection.on_hit(self, hit_amount, hit_player, type, grenade)
            if result == False:
                return False
            if result is not None:
                hit_amount = result
            dist = sqrt(point_distance2(self, hit_player))
            if not grenade:
                if self.weapon is not SHOTGUN_WEAPON:
                    self.send_chat('ATTENTION: Shotgun and grenades only!')
                    return False
                if self.tool is WEAPON_TOOL and self.tool is not (SPADE_TOOL or BLOCK_TOOL) and self.weapon is not (RIFLE_WEAPON or SMG_WEAPON):
                    pctint = (100 * self.protocol.shotgun_multiplier - self.protocol.shotgun_pct_per_block * dist)
                    pct = (100 * self.protocol.shotgun_multiplier - self.protocol.shotgun_pct_per_block * dist)
                    pct = max(0,pct)/100.0
                    hit_amount = int(hit_amount * pct)
                    self.send_chat('BULLET STRENGTH: %s%%' % int(pctint))
                    return hit_amount
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)

    class TennisProtocol(protocol):
        game_mode = CTF_MODE
        shotgun_pct_per_block = config.get('shotgun_pct_per_block', 1.8)
        shotgun_multiplier = config.get('shotgun_multiplier', 1.3)
        def on_flag_spawn(self, x, y, z, flag, entity_id):
            if entity_id == GREEN_FLAG:
                return (0, 0, 63)
            if entity_id == BLUE_FLAG:
                return (0, 0, 63)
            return protocol.on_flag_spawn(self, x, y, z, flag, entity_id)

    return TennisProtocol, TennisConnection