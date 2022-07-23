# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from math import sin
from twisted.internet.reactor import seconds
from pyspades.common import Vertex3
from commands import admin, add, name, get_player

SIZE_MULTIPLIER = 1.5

@admin
def big(connection, player = None):
    player = scale_head(connection, SIZE_MULTIPLIER, player)
    message = player.name + "'s" if connection is not player else 'Your'
    message += ' head is ' + stringify_head_multiplier(player.head_multiplier)
    return message + '!'

@admin
def small(connection, player = None):
    player = scale_head(connection, 1.0 / SIZE_MULTIPLIER, player)
    message = player.name + "'s" if connection is not player else 'Your'
    message += ' head is ' + stringify_head_multiplier(player.head_multiplier)
    return message + '!'

@admin
def wobble(connection, player = None):
    player = scale_head(connection, 1.0, player)
    third = connection is not player
    message = player.name if third else 'You'
    if player.head_wobble_start is None:
        player.head_wobble_start = seconds()
        message += ' begins' if third else ' begin'
        message += ' to bobble. Wobble wobble'
    else:
        player.head_wobble_start = None
        message += ' stops' if third else ' stop'
        message += ' being so indecisive'
    return message

@name('resethead')
@admin
def reset_head(connection, player = None):
    player = scale_head(connection, None, player)
    player.head_wobble_start = None
    third = connection is not player
    message = player.name if third else 'You'
    message += ' thinks' if third else ' think'
    message += ' this stuff was starting to get a little too heady'
    return message

for func in (big, small, wobble, reset_head):
    add(func)

def stringify_head_multiplier(value):
    if value < 1.0:
        return '%.2f times smaller than normal' % (1.0 / value)
    elif value > 1.0:
        return '%.2f times larger than normal' % value
    else:
        return 'just the right size'

def scale_head(connection, value, player = None):
    protocol = connection.protocol
    if player is not None:
        player = get_player(protocol, player)
    elif connection in protocol.players:
        player = connection
    else:
        raise ValueError()
    
    value = (player.head_multiplier or 1.0) * value if value else None
    player.head_multiplier = value
    if value is not None:
        protocol.bighead_players.add(player)
    else:
        protocol.bighead_players.discard(player)
    if player.temp_orientation is None:
        player.temp_orientation = Vertex3()
    return player

def apply_script(protocol, connection, config):
    class BigHeadConnection(connection):
        head_multiplier = None
        head_wobble_start = None
        temp_orientation = None
    
    class BigHeadProtocol(protocol):
        bighead_players = None
        
        def on_map_change(self, map):
            self.bighead_players = set()
            protocol.on_map_change(self, map)
        
        def update_network(self):
            for player in self.bighead_players:
                if not player.world_object:
                    continue
                head_multiplier = player.head_multiplier
                if player.head_wobble_start is not None:
                    elapsed = seconds() - player.head_wobble_start
                    head_multiplier += sin(elapsed) * 0.25 * head_multiplier
                orientation = player.world_object.orientation
                player.temp_orientation.set_vector(orientation)
                orientation *= head_multiplier
            protocol.update_network(self)
            for player in self.bighead_players:
                if not player.world_object:
                    continue
                orientation = player.world_object.orientation
                orientation.set_vector(player.temp_orientation)
    
    return BigHeadProtocol, BigHeadConnection