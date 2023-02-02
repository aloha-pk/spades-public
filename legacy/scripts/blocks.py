# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import alias, get_player, add
from pyspades.constants import *

game_mode = 'ctf'

CTF_SELF_PLACED_BLOCKS = "You have placed {blocks} blocks."
CTF_OTRO_PLACED_BLOCKS = "{name} has placed {blocks} blocks."
BABEL_SELF_PLACED_BLOCKS = "You have contributed {blocks} blocks to your team's tower."
BABEL_OTRO_PLACED_BLOCKS = "{name} has contributed {blocks} blocks to their team's tower."
S_BLOCKS_BABEL_MSG = "/BLOCKS    View you or someone else\'s tower contribution"
S_TOPBLOCKS_BABEL_MSG = "/TOPBLOCKS  View who has the highest contribution to a tower"
S_BLOCKS_DEFAULT_MSG = "/BLOCKS    View you or someone else\'s placed blocks amount"
S_TOPBLOCKS_DEFAULT_MSG = "/TOPBLOCKS  View who has placed the most blocks"
# Babel stuff
BOTH_TOWERS_Y_RANGE = range(240, 273)
BLUE_TOWER_X_RANGE = range(128, 213)
GREEN_TOWER_X_RANGE = range(301, 385)


def blocks(connection, user=None):
    protocol = connection.protocol
    if user is not None:
        connection = get_player(connection.protocol, user)
        if connection not in protocol.players:
            raise ValueError()
    if connection not in protocol.players:
        raise ValueError()
    if user is not None:
        if game_mode == 'babel':
            return BABEL_OTRO_PLACED_BLOCKS.format(name = connection.name, blocks = connection.total_blocks_placed)
        else:
            return CTF_OTRO_PLACED_BLOCKS.format(name=connection.name, blocks=connection.total_blocks_placed)
    else :
        if game_mode == 'babel':
            return BABEL_SELF_PLACED_BLOCKS.format(blocks=connection.total_blocks_placed)
        else:
            return CTF_SELF_PLACED_BLOCKS.format(blocks=connection.total_blocks_placed)
add(blocks)

def topblocks(self):
    playerlist = [player for player in list(self.protocol.players.values())]
    most_blocks = max(player.total_blocks_placed for player in playerlist)
    most_blocks_player = [player for player in playerlist if player.total_blocks_placed == most_blocks]
    for player in most_blocks_player:
        return CTF_OTRO_PLACED_BLOCKS.format(name = player.name, blocks = player.total_blocks_placed)
add(topblocks)

def apply_script(protocol, connection, config):
    global game_mode
    game_mode = config.get('game_mode', 'ctf')

    class BlockProtocol(protocol):
        def __init__(self, *arg, **kw):
            protocol.__init__(self, *arg, **kw)
            self.blocks_server_message()

        def blocks_server_message(self):
            if game_mode == "babel":
                self.help.append(S_BLOCKS_BABEL_MSG)
                self.help.append(S_TOPBLOCKS_BABEL_MSG)
            else:
                self.help.append(S_BLOCKS_DEFAULT_MSG)
                self.help.append(S_TOPBLOCKS_DEFAULT_MSG)


    class BlockConnection(connection):
        def __init__(self, *args, **kwargs):
            connection.__init__(self, *args, **kwargs)
            self.total_blocks_placed = 0

        def on_block_build(self, x, y, z):
            if game_mode == 'babel':
                px = int(self.world_object.position.x)
                py = int(self.world_object.position.y)
                if self.team is self.protocol.blue_team and px in BLUE_TOWER_X_RANGE and py in BOTH_TOWERS_Y_RANGE:
                    self.total_blocks_placed += 1
                if self.team is self.protocol.green_team and px in GREEN_TOWER_X_RANGE and py in BOTH_TOWERS_Y_RANGE:
                    self.total_blocks_placed += 1
                return connection.on_block_build(self, x, y, z)
            else:
                self.total_blocks_placed += 1
            return connection.on_block_build(self, x, y, z)

        def on_line_build(self, points):
            if game_mode == 'babel':
                px = int(self.world_object.position.x)
                py = int(self.world_object.position.y)
                if self.team is self.protocol.blue_team and px in BLUE_TOWER_X_RANGE and py in BOTH_TOWERS_Y_RANGE:
                    self.total_blocks_placed += len(points)
                if self.team is self.protocol.green_team and px in GREEN_TOWER_X_RANGE and py in BOTH_TOWERS_Y_RANGE:
                    self.total_blocks_placed += len(points)
                return connection.on_line_build(self, points)
            else:
                self.total_blocks_placed += len(points)
                return connection.on_line_build(self, points)


    return BlockProtocol, BlockConnection