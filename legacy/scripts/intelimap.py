# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
thepolm3
idea @ TB_
"""

from twisted.internet.task import LoopingCall
from map import check_rotation
from pyspades.commands import add
import commands

def intelimap(connection):
    connection.protocol.overruled=not connection.protocol.ovveruled
    return ("intelimap is ['ON', 'OFF'][connection.protocol.ovveruled] This round")

add(intelimap)
threshold=[]
def apply_script(protocol, connection, config):
    class MapProtocol(protocol):
        overruled=False
        
        def check_next_map(self):
            if not self.overruled:
                nop=len(self.players)
                for i in range(len(threshold)-1):
                    if threshold[i] <= nop < threshold[i+1]:
                        mapindex=i
                        break
                else:
                    mapindex=len(threshold)-1
                self.planned_map=check_rotation([self.get_map_rotation()[mapindex]])[0]

        def on_command(self,command,sender):
            if command=="map" and sender.admin:
                self.overruled=True
            protocol.on_command(self,command,sender)

        def on_map_change(self,map):
            global threshold
            self.overruled=False
            threshold=config.get("map_threshold",[])
            if threshold==[]:
                nop=self.max_players
                rot=self.get_map_rotation()
                step=nop/len(rot)
                for i in range(len(rot)):
                    threshold.append(i*step)
            print(threshold)
            checking=LoopingCall(self.check_next_map)
            checking.start(1)
            protocol.on_map_change(self,map)

    return MapProtocol, connection

