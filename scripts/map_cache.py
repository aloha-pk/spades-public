"""
Author: Rakete175
License: GPL-3
Purpose: Implement map caching - useful for game modes with static maps

"""

from time import monotonic
from pyspades.bytes import ByteWriter
import enet
from twisted.logger import Logger
log = Logger()
from typing import Optional
from pyspades.mapgenerator import ProgressiveMapGenerator
from pyspades.contained import MapStart, HandShakeInit, MapChunk, BlockAction
from pyspades.constants import TC_MODE, DESTROY_BLOCK


class MapCache:
    def __init__(self, max_maps=1):
        self.cache = {}
        self.max_maps = max_maps

    def add_map(self, map_id, map_data):
        if len(self.cache) >= self.max_maps:
            oldest_map_id = list(self.cache.keys())[0]
            del self.cache[oldest_map_id]
        self.cache[map_id] = map_data

    def del_map(self, map_id):
        if self.cache.get(map_id) is not None:
            del self.cache[map_id]

    def get_map(self, map_id):
        return self.cache.get(map_id)

    def has_map(self, map_id):
        return map_id in self.cache

    def reset_cache(self):
        self.cache.clear()

map_cache = MapCache()

class MapCacheException(Exception):
    pass

class ArenaGate: #from arena.py, to avoid a dependency
    def __init__(self, x, y, z, protocol_obj):
        self.blocks = []
        self.protocol_obj = protocol_obj
        solid, self.color = self.protocol_obj.map.get_point(x, y, z)
        if not solid:
            raise MapCacheException(
                'The arena gate coordinate (%i, %i, %i) is not solid.' % (x, y, z))
        self.record_gate(x, y, z)


    def record_gate(self, x, y, z):
        if x < 0 or x > 511 or y < 0 or x > 511 or z < 0 or z > 63:
            return False
        solid, color = self.protocol_obj.map.get_point(x, y, z)
        if solid:
            coordinate = (x, y, z)
            if color[0] != self.color[0] or color[1] != self.color[1] or color[2] != self.color[2]:
                return True
            for block in self.blocks:
                if coordinate == block:
                    return False
            self.blocks.append(coordinate)
            returns = (self.record_gate(x + 1, y, z),
                       self.record_gate(x - 1, y, z),
                       self.record_gate(x, y + 1, z),
                       self.record_gate(x, y - 1, z),
                       self.record_gate(x, y, z + 1),
                       self.record_gate(x, y, z - 1))
            if True in returns:
                self.protocol_obj.support_blocks.append(coordinate)
        return False


def apply_script(protocol, connection, config):
    class MapCacheProtocol(protocol):
        map_writer = None
        arena_enabled = False
        support_blocks = []
        map_version = 0

        def get_map_id(self):
            return str(self.map_version)

        def set_map(self, map_obj):
            self.map = map_obj
            self.world.map = map_obj
            self.on_map_change(map_obj)
            self.team_1.initialize()
            self.team_2.initialize()
            self.support_blocks = []
            self.map_version = 0
            if self.game_mode == TC_MODE:
                self.reset_tc()
            if self.arena_enabled:
                extensions = self.map_info.extensions
                if 'arena_gates' in extensions:
                    for gate in extensions['arena_gates']:
                        ArenaGate(*gate, protocol_obj=self)
            self.players = {}
            map_cache.reset_cache()
            self.map_writer = None
            if self.connections:
                data = ProgressiveMapGenerator(self.map, parent=True)
                for connection in list(self.connections.values()):
                    if connection.player_id is None:
                        continue
                    if connection.map_data is not None:
                        connection.disconnect()
                        continue
                    connection.reset()
                    connection._send_connection_data()
                    connection.classic_transfer=True
                    connection.send_map(data.get_child())
            self.update_entities()

    class MapCacheConnection(connection):
        classic_transfer = True

        def on_disconnect(self):
            map_id = self.protocol.get_map_id()
            if not map_cache.has_map(map_id) and map_cache.has_map("_" + map_id) and self.protocol.map_writer is self:
                map_cache.del_map("_"+map_id)
                self.protocol.map_writer = None
            return connection.on_disconnect(self)

        def _connection_ack(self) -> None:
            self._send_connection_data()
            starttime=monotonic()
            map_id = self.protocol.get_map_id()
            log.debug("Map ID " + map_id)
            if not map_cache.has_map(map_id):
                log.debug("generating new map...")
                self.classic_transfer=True
                self.send_map(ProgressiveMapGenerator(self.protocol.map))
            else:
                log.debug("sending cached map")
                self.classic_transfer=False
                self.send_map()
            log.debug("Map handling: " + str(round((monotonic()-starttime)*1000)) + "ms")

        def send_map(self, data: Optional[ProgressiveMapGenerator] = None, first_time_called=True) -> None:
            map_id = self.protocol.get_map_id()
            if not map_cache.has_map(map_id) or self.classic_transfer:
                containedlist = []
                if data is not None:
                    self.map_data = data
                    map_start = MapStart()
                    map_start.size = data.get_size()
                    self.send_contained(map_start)
                    writer = ByteWriter()
                    map_start.write(writer)
                    data = bytes(writer)
                    if self.protocol.map_writer is None and first_time_called: #only write one version
                        containedlist.append(data)
                elif self.map_data is None:
                    return

                if not self.map_data.data_left():
                    if self.protocol.map_writer is self:
                        self.protocol.map_writer = self
                        all_contained = map_cache.get_map("_" + map_id) + containedlist
                        map_cache.del_map("_"+map_id)
                        map_cache.add_map(map_id, all_contained)
                    log.debug("done sending map data to {player}", player=self)
                    self.map_data = None
                    for data in self.saved_loaders:
                        packet = enet.Packet(bytes(data), enet.PACKET_FLAG_RELIABLE)
                        self.peer.send(0, packet)
                    self.saved_loaders = None
                    self.on_join()
                    if not self.client_info:
                        handshake_init = HandShakeInit()
                        self.send_contained(handshake_init)
                    return
                for _ in range(10):
                    if not self.map_data.data_left():
                        break
                    map_data = MapChunk()
                    map_data.data = self.map_data.read(8192)
                    self.send_contained(map_data)
                    writer = ByteWriter()
                    map_data.write(writer)
                    data = bytes(writer)
                    containedlist.append(data)
                if map_cache.has_map("_" + map_id) and self.protocol.map_writer is self:
                    lastlist = map_cache.get_map("_" + map_id)
                    map_cache.add_map("_"+map_id, lastlist + containedlist)
                elif not map_cache.has_map(map_id) and self.protocol.map_writer is None and first_time_called:
                    self.protocol.map_writer = self
                    map_cache.add_map("_"+map_id, containedlist)
            else:
                containedlist = map_cache.get_map(map_id)
                for data in containedlist:
                    packet = enet.Packet(bytes(data), enet.PACKET_FLAG_RELIABLE)
                    self.peer.send(0, packet)
                log.debug("done sending map data to {player}", player=self)
                self.map_data = None
                for data in self.saved_loaders:
                    packet = enet.Packet(bytes(data), enet.PACKET_FLAG_RELIABLE)
                    self.peer.send(0, packet)
                self.saved_loaders = None
                if self.protocol.arena_enabled and self.protocol.arena_running: #send removal of fence packets when game is running
                    block_action = BlockAction()
                    block_action.player_id = 32
                    block_action.value = DESTROY_BLOCK
                    for block in self.protocol.support_blocks:
                        block_action.x, block_action.y, block_action.z = block
                        self.send_contained(block_action)
                self.on_join()
                if not self.client_info:
                    handshake_init = HandShakeInit()
                    self.send_contained(handshake_init)

        def continue_map_transfer(self) -> None:
            if self.classic_transfer:
                self.send_map(first_time_called=False)

        def on_block_build(self, x, y, z):
            # This map cache is meant for static maps.
            # These hooks here help to avoid a client-server desync in case someone places blocks nevertheless, such as in god mode.
            self.protocol.map_version += 1
            self.protocol.map_writer = None
            return connection.on_block_build(self, x, y, z)

        def on_block_removed(self, x, y, z):
            self.protocol.map_version += 1
            self.protocol.map_writer = None
            return connection.on_block_removed(self, x, y, z)
    return MapCacheProtocol, MapCacheConnection
