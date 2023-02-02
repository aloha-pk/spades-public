# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

'''
Aplies more YOLO to Servers
Maintainer: Wizardian
'''
from pyspades.server import orientation_data, grenade_packet
from pyspades.common import coordinates, Vertex3
from pyspades.constants import *
from pyspades.world import Grenade
from commands import add, admin, get_player, name, alias
import time
 
DEFAULT_MOD = 1.30
DEFAULT_TXE = 0.75
 
@alias('lc')
@name('launchercommands')
def launcher_commands(self):
    return '/ns (short nades)   /nw (wide nades)   /tn (timebomb nades)   /bn (fast, bouncing nades)   /kz (kamikaze mode!!)'
add(launcher_commands)
 
 
@name('omfg')
@admin
def toggle_rockets(connection):
    protocol = connection.protocol
    protocol.omfgrockets = not protocol.omfgrockets
    if protocol.omfgrockets:
        return 'rockets for everypony ... jey!'
    return 'rockets are now turned off!'
add(toggle_rockets)
 
 
@name('dtime')
@admin
def dtime(connection):
    return 'time is %s' % time.time()
add(dtime)
 
@name('nspeed')
@admin
def nspeed(connection, value=DEFAULT_MOD):
    try:
        newVal = int(value)
    except ValueError:
        return "Not a numeric string."
    if newVal <= 0:
        return "Has to be more than 0."
    if newVal >= 100:
        return "You can't see the nades anymore then :3 use less than 100 (99 max)"
    connection.omfg_mod = newVal
    return 'nspeed set to %s' % newVal
add(nspeed)
 
 
@name('ns')
def nm(connection):
    connection.omfg_txe = 0.9
    connection.omfg_mod = 1.30
    return 'Using short distance nadelauncher now.'
add(nm)
 
@name('nw')
def nw(connection):
    connection.omfg_txe = 1.6
    connection.omfg_mod = 1.5
    return 'Using wide distance nadelauncher now.'
add(nw)
 
 
@alias('timebomb')
@alias('timebombs')
@name('tn')
def timebomb(connection):
    connection.omfg_txe = 8
    connection.omfg_mod = 1.5
    return 'Using timebombs now.'
add(timebomb)
 
@name('bn')
def bn(connection):
    connection.omfg_txe = 0.19
    connection.omfg_mod = 5
    return 'Using fast, bouncing nades now.'
add(bn)
 
@alias('kamikaze')
@name('kz')
def alohasnackbar(connection):
    connection.omfg_txe = 0.01
    connection.omfg_mod = 2
    return 'KAMIKAZE MODE ACTIVATED!!!'
add(alohasnackbar)
 
@name('ntime')
@admin
def ntime(connection, value=DEFAULT_TXE):
    try:
        newVal = float(value)
    except ValueError:
        return "Not a numeric string."
    if newVal <= 0:
        return "Has to be more than 0."
    if newVal >= 15:
        return "Has to be less than 15 (max 14)"
    connection.omfg_txe = newVal
    return 'ntime set to %s' % newVal
add(ntime)
 
 
def apply_script(protocol, connection, config):
    class OhNoOhGodProtocol(protocol):
        omfgrockets = True
 
    class OhNoOhGodConnection(connection):
        omfg_txe = DEFAULT_TXE
        omfg_mod = DEFAULT_MOD
 
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if not self.protocol.omfgrockets:
                return connection.on_hit(self, hit_amount, hit_player, type, grenade)
 
            if self.weapon == SHOTGUN_WEAPON and self.tool == WEAPON_TOOL:
                if grenade is None:
                    return False
 
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)
         
        lastshot = 0
 
        def on_shoot_set(self, fire):
            if not self.protocol.omfgrockets:
                return connection.on_shoot_set(self, fire)
            if not self.weapon == SHOTGUN_WEAPON:
                return connection.on_shoot_set(self, fire)
            if not self.tool == WEAPON_TOOL:
                return connection.on_shoot_set(self, fire)
            if fire == True:
                if time.time() - self.lastshot <= 0.8:
                    return connection.on_shoot_set(self, fire)
                self.lastshot = time.time()
                value = self.omfg_txe
            else:
                return connection.on_shoot_set(self, fire)
 
            x, y, z = self.world_object.orientation.x, self.world_object.orientation.y, self.world_object.orientation.z
            mod = self.omfg_mod
            grenade_packet.value = value
            grenade_packet.player_id = self.player_id
            grenade_packet.position = (self.world_object.position.x, self.world_object.position.y, self.world_object.position.z) 
            grenade_packet.velocity = (x * mod, y * mod, z * mod)
            self.protocol.send_contained(grenade_packet)
            position = Vertex3(self.world_object.position.x, self.world_object.position.y, self.world_object.position.z) 
            velocity = Vertex3(x * mod, y * mod, z * mod)
            airstrike = self.protocol.world.create_object(Grenade, value, 
                position, None, 
                velocity, self.grenade_exploded)
            return connection.on_shoot_set(self, fire)
 
    return OhNoOhGodProtocol, OhNoOhGodConnection
