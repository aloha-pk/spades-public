# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import block_action, set_color
from pyspades.common import make_color
from pyspades.color import rgb_distance
from pyspades.constants import *

DIRT_COLOR = (71, 48, 35)

def restore_color(protocol, x, y, z):
    solid, color = protocol.map.get_point(x, y, z)
    if not solid or color == (0, 0, 0) or rgb_distance(color, DIRT_COLOR) < 30:
        return
    if not protocol.map.is_surface(x, y, z):
        set_color.player_id = 32
        set_color.value = make_color(*color)
        block_action.player_id = 32
        block_action.x = x
        block_action.y = y
        block_action.z = z
        block_action.value = DESTROY_BLOCK
        protocol.send_contained(block_action)
        block_action.value = BUILD_BLOCK
        protocol.send_contained(set_color)
        protocol.send_contained(block_action)

def restore_neighbor_colors(protocol, x, y, z):
    restore_color(protocol, x, y, z - 1)
    restore_color(protocol, x, y, z + 1)
    restore_color(protocol, x - 1, y, z)
    restore_color(protocol, x + 1, y, z)
    restore_color(protocol, x, y - 1, z)
    restore_color(protocol, x, y + 1, z)

def destroy_block(protocol, x, y, z):
    was_solid = protocol.map.get_solid(x, y, z)
    if was_solid is None:
        return False
    block_action.player_id = 32
    block_action.x = x
    block_action.y = y
    block_action.z = z
    block_action.value = DESTROY_BLOCK
    protocol.send_contained(block_action, save = True)
    if not was_solid:
        protocol.map.set_point(x, y, z, (0, 0, 0))
    restore_neighbor_colors(protocol, x, y, z)
    if was_solid:
        protocol.map.destroy_point(x, y, z)
    else:
        protocol.map.remove_point(x, y, z)
    return True

def apply_script(protocol, connection, config):
    class PreserveColorConnection(connection):
        def on_block_removed(self, x, y, z):
            protocol = self.protocol
            destroy_block(protocol, x, y, z)
            connection.on_block_removed(self, x, y, z)
    
    return protocol, PreserveColorConnection