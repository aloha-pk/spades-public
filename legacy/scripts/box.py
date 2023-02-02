# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import add, admin
from pyspades.common import to_coordinates, coordinates
import buildbox
import cbc

# requires buildbox.py script in the /scripts folder

@admin
def box(connection, filled = ""):
	if connection.boxing > 0:
		connection.boxing = 0
		return 'Building generator cancelled'
	else:
		connection.boxing = 1
		connection.boxing_filled = filled.lower() == "filled"
		return 'Place first corner block'
add(box)

def apply_script(protocol, connection, config):
	protocol, connection = cbc.apply_script(protocol, connection, config)
	coords1 = 0	#initializing coords
	coords2 = 0
	
	class BoxMakerConnection(connection):
		def __init__(self, *arg, **kw):
			connection.__init__(self, *arg, **kw)
			self.boxing = 0
			self.boxing_filled = 0
			self.box_x = 0
			self.box_y = 0
			self.box_z = 0
		
		def build_box_filled(self, x1, y1, z1, x2, y2, z2, color = None):
			buildbox.build_filled(self.protocol, x1, y1, z1, x2, y2, z2, color or self.color, self.god, self.god_build)
		
		def build_box(self, x1, y1, z1, x2, y2, z2, color = None):
			buildbox.build_empty(self.protocol, x1, y1, z1, x2, y2, z2, color or self.color, self.god, self.god_build)
		
		def on_block_build(self, x, y, z):
			if self.boxing == 2:
				self.coords2 = to_coordinates(*(self.get_location()[:2]))
				if (self.coords1 != self.coords2):	#checking that person is in the same sector they started in
					self.boxing = 0
					self.send_chat('You must remain inside your sector.  Boxing Cancelled.')
                                        return
				self.boxing = 0
				if self.boxing_filled == 0:
					self.build_box(self.box_x, self.box_y, self.box_z, x, y, z)
				else:
					self.build_box_filled(self.box_x, self.box_y, self.box_z, x, y, z)
				self.send_chat('Box created!')
			if self.boxing == 1:
				self.coords1 = to_coordinates(*(self.get_location()[:2]))	#getting grid coords 1st block
				self.box_x = x
				self.box_y = y
				self.box_z = z
				self.send_chat('Now place opposite corner block')
				self.boxing = 2
			return connection.on_block_build(self, x, y, z)
	
	class BoxMakerProtocol(protocol):
		def on_map_change(self, map):
			for connection in self.clients:
				connection.boxing = 0
			protocol.on_map_change(self, map)
	
	return BoxMakerProtocol, BoxMakerConnection









