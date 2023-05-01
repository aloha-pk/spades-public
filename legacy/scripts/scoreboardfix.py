# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# scoreboardfix.py  |  fixes scoreboard / name glitch! \:D/
# contributors: MuffinTastic
# last edited: 12:23 PM 12:23 3/22/2016 PDT

import pyspades.contained as loaders

player_left = loaders.PlayerLeft()

def apply_script(protocol, connection, config):
	class ScoreboardFixConnection(connection):
		nameglitch_fix_enabled = False
		
		def on_disconnect(self):
			if self.nameglitch_fix_enabled:
				if self.player_id is not None and self.team is None:
					player_left.player_id = self.player_id
					
					for _connection in self.protocol.connections.values():
						if _connection.nameglitch_fix_enabled:
							_connection.send_contained(player_left)
			
			connection.on_disconnect(self)
				
	class ScoreboardFixProtocol(protocol):
		
		def on_map_change(self, map):
			for connection in self.connections.values():
				connection.nameglitch_fix_enabled = True
				
			protocol.on_map_change(self, map)
			
	return ScoreboardFixProtocol, ScoreboardFixConnection