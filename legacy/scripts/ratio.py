# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
K/D ratio script.

Author: TheGrandmaster
Maintainer: mat^2
"""

from commands import get_player, add
from pyspades.constants import *
from twisted.internet.reactor import seconds
from pyspades.common import prettify_timespan

# True if you want to include the headshot-death ratio in the ratio
# NOTE: this makes the message overflow into two lines
HEADSHOT_RATIO = False

# List other types of kills as well
EXTENDED_RATIO = False

#Adds rate of kills
KILLS_PER_MINUTE = True

# "ratio" must be AFTER "votekick" in the config.txt script list
RATIO_ON_VOTEKICK = True
IRC_ONLY = False

def ratio(connection, user=None):
    msg = "You have"
    if user != None:
        connection = get_player(connection.protocol, user)
        msg = "%s has"
        if connection not in connection.protocol.players:
            raise KeyError()
        msg %= connection.name
    if connection not in connection.protocol.players:
        raise KeyError()
    
    kills = connection.ratio_kills
    deaths = float(max(1,connection.ratio_deaths))
    headshotkills = connection.ratio_headshotkills
    meleekills = connection.ratio_meleekills
    grenadekills = connection.ratio_grenadekills
    
    msg += " a kill-death ratio of %.2f" % (kills/deaths)
    if HEADSHOT_RATIO:
        msg += ", headshot-death ratio of %.2f" % (headshotkills/deaths)
    msg += " (%s kills, %s deaths" % (kills, connection.ratio_deaths)
    if EXTENDED_RATIO:
        msg += ", %s headshot, %s melee, %s grenade" % (headshotkills, meleekills, grenadekills)
    if KILLS_PER_MINUTE:
        dt = (seconds() - connection.time_login) /60
        msg += ", %.2f kills per minute" % (kills/dt)
    msg += ")."
    return msg

add(ratio)

def apply_script(protocol, connection, config):
    class RatioConnection(connection):
        ratio_kills = 0
        ratio_headshotkills = 0
        ratio_meleekills = 0
        ratio_grenadekills = 0
        ratio_deaths = 0
        time_login = 0
        
        def on_kill(self, killer, type, grenade):
            if killer is not None and self.team is not killer.team:
                if self != killer:
                    killer.ratio_kills += 1
                    killer.ratio_headshotkills += type == HEADSHOT_KILL
                    killer.ratio_meleekills    += type == MELEE_KILL
                    killer.ratio_grenadekills  += type == GRENADE_KILL
            
            self.ratio_deaths += 1
            return connection.on_kill(self, killer, type, grenade)

        def on_login(self, name):
            if self.time_login == 0:
                self.time_login = seconds()
            return connection.on_login(self, name)
    class RatioProtocol(protocol):
        def on_votekick_start(self, instigator, victim, reason):
            result = protocol.on_votekick_start(self, instigator, victim, reason)
            if result is None and RATIO_ON_VOTEKICK:
                message = ratio(instigator, victim.name)
                if IRC_ONLY:
                    self.irc_say('* ' + message)
                else:
                    self.send_chat(message, irc = True)
            return result
    
    return RatioProtocol, RatioConnection
