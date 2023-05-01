# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Modified version of GreaseMonkey's smgsucks.py

Public Domain
"""

from pyspades.constants import *

def apply_script(protocol, connection, config):
    class RifleOnlyConnection(connection):
        def on_weapon_set(self, wpnid):
            if wpnid != RIFLE_WEAPON:
                self.send_chat("Weapon forbidden on this server - rifles only!")
                return False
            return connection.on_weapon_set(self, wpnid)
        def set_weapon(self, weapon, local = False, no_kill = False, *args, **kwargs):
            if weapon != RIFLE_WEAPON:
                self.send_chat("Weapon forbidden on this server - rifles only!")
                weapon = RIFLE_WEAPON
                if local:
                    no_kill = True
                    local = False
            return connection.set_weapon(self, weapon, local, no_kill, *args, **kwargs)
    
    return protocol, RifleOnlyConnection

