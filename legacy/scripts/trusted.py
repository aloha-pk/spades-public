# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Adds the ability to 'trust' certain players, i.e. they cannot be votekicked
or rubberbanded.

Maintainer: mat^2 / hompy
"""

from commands import add, admin, get_player

S_GRANTED = '{player} is now trusted'
S_GRANTED_SELF = "You've been granted trust, and can't be votekicked"
S_CANT_VOTEKICK = "{player} is trusted and can't be votekicked"
S_RESULT_TRUSTED = 'Trusted user'

@admin
def trust(connection, player):
    player = get_player(connection.protocol, player)
    player.on_user_login('trusted', False)
    player.send_chat(S_GRANTED_SELF)
    return S_GRANTED.format(player = player.name)

add(trust)

def apply_script(protocol, connection, config):
    class TrustedConnection(connection):
        def on_user_login(self, user_type, verbose = True, who = None):
            if user_type == 'trusted':
                self.speedhack_detect = False
                votekick = getattr(self.protocol, 'votekick', None)
                if votekick and votekick.victim is self:
                    votekick.end(S_RESULT_TRUSTED)
                    self.protocol.votekick = None
            return connection.on_user_login(self, user_type, verbose, who)
    
    class TrustedProtocol(protocol):        
        def on_votekick_start(self, instigator, victim, reason):
            if victim.user_types.trusted:
                return S_CANT_VOTEKICK.format(player = victim.name)
            return protocol.on_votekick_start(self, instigator, victim, reason)
    
    return TrustedProtocol, TrustedConnection
