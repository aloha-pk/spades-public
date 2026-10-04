# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Map optimizations for arena's special case.

DESCRIPTION
Arena is a gamemode with static  maps, where  the only blocks that  change are
the gates  whenever a round is currently running. Instead of regenerating  the
map on each round, this script replaces the map loading behavior with one that
only generates the map on map change (and  startup), and sends BlockActions to
destroy the gates if a player joins while a round is running.

NOTES
This  script  is **only** for  arena.  Any modification to  the map done after
set_map()  has  been called will NOT be taken into  account. This means things
such as godbuild or togglebuild would  create blocks  that newer players  will
not see.

AUTHORS
Rakete <https://aloha.pk/u/rakete>
utf <https://aloha.pk/u/001>

"""

import enet
from pyspades.constants import TC_MODE
from pyspades.constants import DESTROY_BLOCK
from pyspades.mapgenerator import ProgressiveMapGenerator
from pyspades import contained as loaders
from twisted.logger import Logger

log = Logger()

map_chunks = []
map_size = 0

def apply_script(protocol, connection, config):
    class ArenaOptimizerConnection(connection):
        def send_map(self, data = None):
            global map_chunks
            global map_size

            map_start = loaders.MapStart()
            map_start.size = map_size
            self.send_contained(map_start)

            for chunk in map_chunks:
                map_data = loaders.MapChunk()
                map_data.data = chunk
                self.send_contained(map_data)
            self.map_data = None

            for data in self.saved_loaders:
                packet = enet.Packet(bytes(data), enet.PACKET_FLAG_RELIABLE)
                self.peer.send(0, packet)
            self.saved_loaders = None

            self.on_join()
            if not self.client_info:
                handshake_init = loaders.HandShakeInit()
                self.send_contained(handshake_init)

            if self.protocol.arena_running:
                for gate in self.protocol.gates:
                    block_action = loaders.BlockAction()
                    block_action.player_id = 32
                    block_action.value = DESTROY_BLOCK
                    for x, y, z in gate.support_blocks:
                        block_action.x = x
                        block_action.y = y
                        block_action.z = z
                        self.send_contained(block_action)

                self.protocol.destroy_gates()

    class ArenaOptimizerProtocol(protocol):
        def set_map(self, map_obj):
            global map_chunks
            global map_size

            self.map = map_obj
            self.world.map = map_obj
            self.on_map_change(map_obj)

            self.team_1.initialize()
            self.team_2.initialize()
            if self.game_mode == TC_MODE:
                self.reset_tc()

            self.players = {}

            map_generator = ProgressiveMapGenerator(self.map)
            map_chunks = []
            map_size = 0

            while map_generator.data_left():
                chunk = map_generator.read(8192)
                map_chunks += [chunk]
                map_size += len(chunk)

            if self.connections:
                for conn in list(self.connections.values()):
                    if conn.player_id is None:
                        continue

                    if conn.map_data is not None:
                        conn.disconnect()
                        continue

                    conn.reset()
                    conn._send_connection_data()
                    conn.send_map()

            self.update_entities()

    return ArenaOptimizerProtocol, ArenaOptimizerConnection
