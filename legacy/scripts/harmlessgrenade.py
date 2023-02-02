# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import block_action
from pyspades.constants import *

def apply_script(protocol, connection, config):
    class HarmlessGrenadeConnection(connection):
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
            x = int(x)
            y = int(y)
            z = int(z)
            for player_list in (self.team.other.get_players(), (self,)):
                for player in player_list:
                    if not player.hp:
                        continue
                    damage = grenade.get_damage(player.world_object.position)
                    if damage == 0:
                        continue
                    returned = self.on_hit(damage, player, GRENADE_KILL, grenade)
                    if returned == False:
                        continue
                    elif returned is not None:
                        damage = returned
                    player.set_hp(player.hp - damage, self, 
                        hit_indicator = position.get(), type = GRENADE_KILL,
                        grenade = grenade)
            if not self.admin:
                return
            if self.on_block_destroy(x, y, z, GRENADE_DESTROY) == False:
                return
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
    
    return protocol, HarmlessGrenadeConnection