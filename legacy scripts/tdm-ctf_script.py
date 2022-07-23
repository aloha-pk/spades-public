# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
A mix between TDM and CTF.

Set cap_limit to 1 in config.
Add reverse_onectf script in config.

Maintainer: FerrariFlunker
"""

from pyspades.constants import *

import commands

def score(connection):
    return connection.protocol.get_kill_count()
commands.add(score)

def apply_script(protocol, connection, config):
    class TDMCTFConnection(connection):        

        def on_spawn(self, pos):
            self.send_chat(self.explain_game_mode())
            self.send_chat(self.protocol.get_kill_count())            
            return connection.on_spawn(self, pos)

        def on_flag_capture(self):
            result = connection.on_flag_capture(self)
            self.protocol.intel_end_game(self)
            return result

        def on_flag_drop(self):
            self.protocol.onectf_reset_flags()
            return connection.on_flag_drop(self)
        
        def on_kill(self, killer, type, grenade):
            result = connection.on_kill(self, killer, type, grenade)
            self.protocol.check_end_game(killer)
            return result

        def explain_game_mode(self):
            return ('TDM-CTF: Kill the enemy to reach the kill limit OR capture the intel to instantly win.')
            
    class TDMCTFProtocol(protocol):
        kill_limit = config.get('kill_limit', 100)                
    
        def get_kill_count(self):
            green_kills = self.green_team.kills
            blue_kills = self.blue_team.kills
            diff = green_kills - blue_kills
            if green_kills>blue_kills:
                return ("SCORE:  %s leads %s-%s (+%s, %s left). Playing to %s kills." %
                        (self.green_team.name, green_kills, blue_kills,
                        diff,
                        self.kill_limit - green_kills,
                        self.kill_limit))
            elif green_kills<blue_kills:
                return ("SCORE:  %s leads %s-%s (+%s, %s left). Playing to %s kills." %
                        (self.blue_team.name, blue_kills, green_kills,
                        -diff,
                        self.kill_limit - blue_kills,
                        self.kill_limit))
            else:
                return ("SCORE:  %s-%s, %s left. Playing to %s kills." %
                        (green_kills,
                         blue_kills,
                        self.kill_limit - green_kills,
                        self.kill_limit))
        
        def check_end_game(self, player):
            if self.green_team.kills>=self.kill_limit:
                msg = ("%s Team Wins, %s - %s" % (self.green_team.name, self.green_team.kills, self.blue_team.kills))
                self.repeat_server_message(msg)
                self.reset_game(player)
                protocol.on_game_end(self)
                self.onectf_reset_flags()
            elif self.blue_team.kills>=self.kill_limit:
                msg = ("%s Team Wins, %s - %s" % (self.green_team.name, self.blue_team.kills, self.green_team.kills))
                self.repeat_server_message(msg)
                self.reset_game(player)        
                protocol.on_game_end(self)
                self.onectf_reset_flags()

        def intel_end_game(self, player):
            if player.team is self.green_team:
                msg = ("%s has capped the intel!  %s Team Wins!" % (player.name, self.green_team.name))
                self.repeat_server_message(msg)
            elif player.team is self.blue_team:
                msg = ("%s has capped the intel!  %s Team Wins!" % (player.name, self.blue_team.name))
                self.repeat_server_message(msg)     

        def repeat_server_message(self, message):
            for x in range(6):
                self.send_chat(message)
    
    return TDMCTFProtocol, TDMCTFConnection