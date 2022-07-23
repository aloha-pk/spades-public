# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Scrip t by kmsi(kmsiapps@gmail.com)
Blocks Specific Weapons. (ex. smg..)
Usage : /blocksmg, /blockrifle, /blockshotgun, /blocknade, /blockspade
"""
from commands import add, admin
from pyspades.constants import *

#Edit here to change default settings
BlockSMGBool = False
BlockRifleBool = False
BlockShotgunBool = False
BlockNadeBool = False
BlockSpadeBool = False

@admin
def blocksmg(connection):
    global BlockSMGBool
    if BlockSMGBool:
        BlockSMGBool=False
        connection.protocol.send_chat('SMG is enabled now.')
    elif BlockSMGBool == False:
        BlockSMGBool=True
        connection.protocol.send_chat('SMG is disabled now.')
add(blocksmg)
        
@admin        
def blockrifle(connection):
    global BlockRifleBool
    if BlockRifleBool:
        BlockRifleBool=False
        connection.protocol.send_chat('Rifle is enabled now.')
    elif BlockRifleBool == False:
        BlockRifleBool=True
        connection.protocol.send_chat('Rifle is disabled now.')
add(blockrifle)
        
@admin 
def blockshotgun(connection):
    global BlockShotgunBool
    if BlockShotgunBool:
        BlockShotgunBool=False
        connection.protocol.send_chat('Shotgun is enabled now.')
    elif BlockShotgunBool == False:
        BlockShotgunBool=True
        connection.protocol.send_chat('Shotgun is disabled now.')
add(blockshotgun)
 
@admin 
def blocknade(connection):
    global BlockNadeBool
    if BlockNadeBool:
        BlockNadeBool=False
        connection.protocol.send_chat('Grenade is enabled now.')
    elif BlockNadeBool == False:
        BlockNadeBool=True
        connection.protocol.send_chat('Grenade is disabled now.')
add(blocknade)
        
@admin        
def blockspade(connection):
    global BlockSpadeBool
    if BlockSpadeBool:
        BlockSpadeBool=False
        connection.protocol.send_chat('Spade is enabled now.')
    elif BlockSpadeBool == False:
        BlockSpadeBool=True
        connection.protocol.send_chat('Spade is disabled now.')
add(blockspade)
        
def apply_script(protocol, connection, config):
    class BlockWeaponConnection(connection):
        global BlockSMGBool
        global BlockRifleBool
        global BlockShotgunBool
        global BlockNadeBool
        global BlockSpadeBool
        
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if self.weapon==SMG_WEAPON and BlockSMGBool:
                self.send_chat('SMG is disabled now. Use another weapon!')
                return False
            elif self.weapon==RIFLE_WEAPON and BlockRifleBool:
                self.send_chat('Rifle is disabled now. Use another weapon!')
                return False
            elif self.weapon==SHOTGUN_WEAPON and BlockShotgunBool:
                self.send_chat('Shotgun is disabled now. Use another weapon!')
                return False
            elif self.tool==SPADE_TOOL and BlockSpadeBool:
                self.send_chat('Spade is disabled now. Use another weapon!')
                return False
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)
            
        def on_grenade(self, time_left):
            if BlockNadeBool:
                self.send_chat('Grenade is disabled now. Use another weapon!')
                return False
            return connection.on_grenade(self, time_left)
    return protocol, BlockWeaponConnection