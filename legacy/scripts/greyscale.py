# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

def apply_script(protocol, connection, config):
	class DesaturateProtocol(protocol):
		def on_map_change(self, map):
			protocol.on_map_change(self, map)
			for x in xrange(512):
				for y in xrange(512):
					for z in xrange(63):
						if self.map.get_solid(x,y,z):
							c = self.map.get_color(x,y,z)
							nc = int((c[0]+c[1]+c[2])/3)
							self.map.set_point(x,y,z,(nc,nc,nc))
				if (x/5.120) % 25  == 0:	
					print "Desaturating - %s percent complete" % int(x/5.12)
			protocol.on_map_change(self, map)
	return DesaturateProtocol, connection

