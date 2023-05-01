# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import add, admin
from pyspades.common import to_coordinates, coordinates
import clearbox
import cbc

# requires clearbox.py in the /scripts directory

@admin
def db(connection):
	if connection.deboxing > 0:
		connection.deboxing = 0
		return 'DeBox cancelled'
	else:
		connection.deboxing = 1
		return 'Break first corner block'
add(db)

def apply_script(protocol, connection, config):
	protocol, connection = cbc.apply_script(protocol, connection, config)
	coords1 = 0	#initializing coords
	coords2 = 0
	
	class ClearBoxMakerConnection(connection):
		def __init__(self, *arg, **kw):
			connection.__init__(self, *arg, **kw)
			self.deboxing = 0
			self.clearbox_x = 0
			self.clearbox_y = 0
			self.clearbox_z = 0
		
		def clear_box_solid(self, x1, y1, z1, x2, y2, z2):
			clearbox.clear_solid(self.protocol, x1, y1, z1, x2, y2, z2, self.god)
		
		def clear_box(self, x1, y1, z1, x2, y2, z2):
			clearbox.clear(self.protocol, x1, y1, z1, x2, y2, z2, self.god)
		
		def on_block_removed(self, x, y, z):
			if self.deboxing == 2:
				self.coords2 = to_coordinates(*(self.get_location()[:2]))
				if (self.coords1 != self.coords2):	#checking that person is in the same sector they started in
					self.deboxing = 0
					self.send_chat('You must remain inside your sector.  Debox Cancelled.')
                                        return
				self.deboxing = 0
				self.clear_box(self.clearbox_x, self.clearbox_y, self.clearbox_z, x, y, z)
				self.send_chat('Destroying box!')
			if self.deboxing == 1:
				self.coords1 = to_coordinates(*(self.get_location()[:2]))	#getting grid coords 1st block
				self.clearbox_x = x
				self.clearbox_y = y
				self.clearbox_z = z
				self.send_chat('Now break opposite corner block')
				self.deboxing = 2
			return connection.on_block_removed(self, x, y, z)
	
	class ClearBoxMakerProtocol(protocol):
		def on_map_change(self, map):
			for connection in self.clients:
				connection.deboxing = 0
			protocol.on_map_change(self, map)
	
	return ClearBoxMakerProtocol, ClearBoxMakerConnection







