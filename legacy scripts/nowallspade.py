# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from pyspades.server import * 
from commands import name, add, admin, alias
import commands     

@alias('tws') 
@admin
@name('togglewallspading') 
def togglewallspading(self):                    
    	self.protocol.is_fluffy = not self.protocol.is_fluffy     
    	if not self.protocol.is_fluffy: return 'Spading someone behind a wall is possible again now!'                  
    	else: return 'You canot spade people through walls anymore. (killjoy)'                
commands.add(togglewallspading)            


def apply_script(protocol, connection, config): 

    class nowallspadingprotocol(protocol):
        is_fluffy = True
    
    class nowallspadingconnection(connection):

        def on_hit(self, hit_amount, hit_player, type, grenade): 

            if hit_player.protocol.is_fluffy:

                pos =  hit_player.world_object.position

                if not self.world_object.can_see(pos.x, pos.y, pos.z) and self.tool == SPADE_TOOL and self.team != hit_player.team: 

                    return False 

            return connection.on_hit(self, hit_amount, hit_player, type, grenade) 

    return nowallspadingprotocol, nowallspadingconnection
