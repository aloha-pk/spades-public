# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org


from pyspades.contained import WeaponReload, SetTool
from piqueserver.commands import command
from pyspades.constants import FALL_KILL, GRENADE_TOOL
import enet
import struct
set_tool = SetTool()

COMMAND_IS_LOUD = False
INFINITE_BLOCKS = True


def send_player_property_packet(self):     
    PACKET_EXT_BASE = 64  # 0x40                                          
    EXT_PLAYER_PROPERTIES = 0  # 0x00                                     
                                                                            
    player_id = self.player_id                                            
    health = self.hp                                                      
    blocks = self.blocks = 50                                                           
    grenades = self.grenades                                              
    ammo_clip = self.weapon_object.current_ammo                           
    ammo_reserved = self.weapon_object.current_stock                      
    score = self.kills                                                    
    subID = 0
                                                                            
    # Corrected packet structure with all 10 items                        
    packet_data = struct.pack(                                            
        '>B B B B B B B H I',  # Format: Packet ID, subID, player_id, health, blocks, grenades, ammo_clip, ammo_reserved (H), score (I)                           
        PACKET_EXT_BASE, # Packet ID 
        EXT_PLAYER_PROPERTIES,  # sub ID                                                        
        player_id,                                                        
        health,                                                           
        blocks,                                                           
        grenades,                                                         
        ammo_clip,                                                        
        ammo_reserved,                                                    
        score                                                             
    )                                                                     
    self.peer.send(0, enet.Packet(packet_data, enet.PACKET_FLAG_RELIABLE))

@command("iblox", admin_only=True)
def infiniteblocks(connection):
    global INFINITE_BLOCKS
    INFINITE_BLOCKS = not INFINITE_BLOCKS
    on_off = 'ON' if INFINITE_BLOCKS else 'OFF'

    connection.protocol.irc_say(f"* {connection.name} has toggled infinite blocks {on_off}")

    ingame_msg = f"Infinite blocks have been toggled {on_off}!"

    if COMMAND_IS_LOUD:
        connection.protocol.send_chat(ingame_msg)
    else:
        return ingame_msg


def apply_script(protocol, connection, config):
    class InfiBlocksConnection(connection):

        def infiblocks_refill(self):
            if 0 in self.proto_extensions:
                send_player_property_packet(self)
                return
            health = self.hp
            weapon = self.weapon_object
            ammo = weapon.current_ammo
            reserve = weapon.current_stock
            grenades = self.grenades
            self.refill()
            self.set_hp(health, kill_type=FALL_KILL)
            self.grenades = grenades
            weapon.set_shoot(False)
            weapon.current_stock = reserve
            weapon.current_ammo = ammo
            weapon_reload = WeaponReload()
            weapon_reload.player_id = self.player_id
            weapon_reload.clip_ammo = weapon.current_ammo
            weapon_reload.reserve_ammo = weapon.current_stock
            self.send_contained(weapon_reload)

        def on_block_build(self, x, y, z):
            if INFINITE_BLOCKS and self.blocks <= 5:
                self.infiblocks_refill()
            return connection.on_block_build(self, x, y, z)

        def on_line_build(self, points):
            if INFINITE_BLOCKS and self.blocks <= 25:
                self.infiblocks_refill()
            return connection.on_line_build(self, points)

        def on_tool_set_attempt(self, tool):
            if tool == GRENADE_TOOL and self.grenades <= 0:
                set_tool.player_id = self.player_id
                set_tool.value = self.tool
                self.send_contained(set_tool)
                if self.client_info:
                    if self.client_info["client"] == "OpenSpades":
                        self.send_chat_error("Out of Grenades")
                return False
            return connection.on_tool_set_attempt(self, tool)

    return protocol, InfiBlocksConnection
