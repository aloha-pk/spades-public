# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

def apply_script(protocol, connection, config):
	class BlackProtocol(protocol):	  
		def on_world_update(self):
			if self.loop_count % 500 == 0:
				self.set_fog_color((0,0,0))
			protocol.on_world_update(self)

	return BlackProtocol, connection

