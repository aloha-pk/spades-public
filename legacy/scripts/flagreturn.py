# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Makes the flag returnable in Quake-like fashion.

Maintainer: mat^2
"""

from pyspades.collision import vector_collision

def apply_script(protocol, connection, config):
    game_mode = config.get('game_mode', 'ctf')
    
    if game_mode != 'ctf':
        return protocol, connection

    class ReturnConnection(connection):
        def on_flag_take(self):
            self.team.other.flag.out = True
            return connection.on_flag_take(self)
        
        def on_flag_capture(self):
            self.team.other.flag.out = False
            self.team.other.flag.start = self.team.other.flag.get()
            return connection.on_flag_capture(self)

        def on_position_update(self):
            flag = self.team.flag
            if flag.player is None and flag.out:
                if vector_collision(self.world_object.position, flag):
                    flag.out = False
                    flag.set(*flag.start)
                    flag.update()
                    self.protocol.send_chat('%s intel was returned by %s!' % (
                        self.team.name, self.name), global_message = None)
            return connection.on_position_update(self)
    
    class ReturnProtocol(protocol):
        def __init__(self, *arg, **kw):
            protocol.__init__(self, *arg, **kw)
            for team in self.teams.itervalues():
                if team.spectator:
                    continue
                team.flag.out = False
                team.flag.start = team.flag.get()
        
    return ReturnProtocol, ReturnConnection