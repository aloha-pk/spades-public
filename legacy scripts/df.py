# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import add, admin
from pyspades.common import to_coordinates, coordinates
import clearbox
import cbc

# requires clearbox.py in the /scripts directory

@admin
def df(connection):
	if connection.deflooring > 0:
		connection.deflooring = 0
		return 'DeFloor cancelled'
	else:
		connection.deflooring = 1
		return 'Break first corner block'
add(df)

def apply_script(protocol, connection, config):
	protocol, connection = cbc.apply_script(protocol, connection, config)
	coords1 = 0	#initializing coords
	coords2 = 0
	
	class ClearFloorMakerConnection(connection):
		def __init__(self, *args, **kwargs):
			connection.__init__(self, *args, **kwargs)
			self.deflooring = 0
			self.clearfloor_x = 0
			self.clearfloor_y = 0
			self.clearfloor_z = 0
		
		def on_block_removed(self, x, y, z):
			if self.deflooring == 2:
				self.coords2 = to_coordinates(*(self.get_location()[:2]))
				if (self.coords1 != self.coords2):	#checking that person is in the same sector they started in
					self.deflooring = 0
					self.send_chat('You must remain inside your sector.  DeFloor Cancelled.')
                                        return
				self.deflooring = 0
				if self.clearfloor_z != z:
					self.send_chat('Surface is uneven! Using first height.')
				clearbox.clear_solid(self.protocol, self.clearfloor_x, self.clearfloor_y, self.clearfloor_z, x, y, self.clearfloor_z, self.god)
				self.send_chat('Floor destroyed!')
			if self.deflooring == 1:
				self.coords1 = to_coordinates(*(self.get_location()[:2]))	#getting grid coords 1st block
				self.clearfloor_x = x
				self.clearfloor_y = y
				self.clearfloor_z = z
				self.send_chat('Now break opposite corner block')
				self.deflooring = 2
			return connection.on_block_removed(self, x, y, z)
	
	class ClearFloorMakerProtocol(protocol):
		def on_map_change(self, map):
			for connection in self.clients:
				connection.deflooring = 0
			protocol.on_map_change(self, map)
	
	return ClearFloorMakerProtocol, ClearFloorMakerConnection












