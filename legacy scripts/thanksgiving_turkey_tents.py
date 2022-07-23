# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Thanksgiving Turkey Tents
-this script adds a poorly modeled turkey ontop of each tent-

Creator: FerrariFlunker
"""
from twisted.internet.reactor import callLater, seconds
from pyspades.server import block_action, set_color
from pyspades.constants import DESTROY_BLOCK, BUILD_BLOCK
from pyspades.contained import BlockAction, SetColor
from pyspades.constants import *
from pyspades import world
from array import *

S_HAPPY_THANKSGIVING = 'Happy Thanksgiving from aloha.pk!'
S_TENT_TURKEY = 'The tent turkey is all powerful and cannot be destroyed.'
GREY = (128, 128, 128)
ORANGE = (222, 126, 0)
BROWN = (140, 79, 0)
DARK_BROWN = (79, 45, 2)
RED = (222, 55, 0)
BLUE_TENT_COORDS = []
GREEN_TENT_COORDS = []
GREY_BLOCKS = [[1, 1, 1], [2, 1, 1], [3, 1, 1], [4, 1, 1], [5, 1, 1], [6, 1, 1],
          [1, 2, 1], [2, 2, 1], [3, 2, 1], [4, 2, 1], [5, 2, 1], [6, 2, 1],
          [1, 3, 1], [2, 3, 1], [3, 3, 1], [4, 3, 1], [5, 3, 1], [6, 3, 1],
          [1, 4, 1], [2, 4, 1], [3, 4, 1], [4, 4, 1], [5, 4, 1], [6, 4, 1],
          [1, 5, 1], [2, 5, 1], [3, 5, 1], [4, 5, 1], [5, 5, 1], [6, 5, 1],
          [1, 5, 1], [2, 5, 1], [3, 5, 1], [4, 5, 1], [5, 5, 1], [6, 5, 1]]
ORANGE_BLOCKS = [[2, 3, 2], [2, 4, 2], [5, 3, 2], [5, 4, 2],
                 [2, 3, 3], [5, 3, 3],
                 [2, 3, 4], [5, 3, 4],
                 [3, 7, 7], [4, 7, 7]]
BROWN_BLOCKS = [[3, 2, 5], [3, 3, 5], [3, 4, 5], [3, 5, 5], 
                [4, 2, 5], [4, 3, 5], [4, 4, 5], [4, 5, 5],
                [2, 2, 5], [2, 3, 5], [2, 4, 5], 
                [5, 2, 5], [5, 3, 5], [5, 4, 5],
                [3, 2, 6], [3, 3, 6], [3, 4, 6], [3, 5, 6],  
                [4, 2, 6], [4, 3, 6], [4, 4, 6], [4, 5, 6],    
                [2, 2, 6], [2, 3, 6], [2, 4, 6], 
                [5, 2, 6], [5, 3, 6], [5, 4, 6],
                [3, 4, 7], [3, 5, 7], [3, 6, 7],
                [4, 4, 7], [4, 5, 7], [4, 6, 7],
                [3, 5, 8], [3, 6, 8],
                [4, 5, 8], [4, 6, 8]]
DARK_BROWN_BLOCKS = [[1, 1, 5], [2, 1, 5], [3, 1, 5], [4, 1, 5],
                    [3, 1, 6], [4, 1, 6], 
                    [5, 1, 5], [6, 1, 5],
                    [1, 1, 6], [2, 1, 6],  
                    [5, 1, 6], [6, 1, 6],
                    [2, 1, 7], [3, 1, 7], [4, 1, 7], [5, 1, 7],
                    [3, 1, 8], [4, 1, 8]]
RED_BLOCKS = [[4, 6, 6]]  

                   
def apply_script(protocol, connection, config):

    class TurkeyProtocol(protocol):
        def __init__(self, *args, **kwargs):
            protocol.__init__(self, *args, **kwargs) 
            self.thanksgiving_server_message()           

        def buildTurkeyOnBlueTent(self, tentX, tentY, tentZ):
            int = -1
            for i in GREY_BLOCKS:
                int += 1
                x = GREY_BLOCKS[int][0] 
                y = GREY_BLOCKS[int][1]
                z = GREY_BLOCKS[int][2]
                z = -z  
                self.singleBlock(y + tentX - 3, x + tentY - 4, z + tentZ + 1, GREY)
            int = -1
            for i in ORANGE_BLOCKS:
                int += 1
                x = ORANGE_BLOCKS[int][0] 
                y = ORANGE_BLOCKS[int][1]
                z = ORANGE_BLOCKS[int][2]
                z = -z    
                self.singleBlock(y + tentX - 3, x + tentY - 4, z + tentZ + 1, ORANGE)
            int = -1
            for i in BROWN_BLOCKS:
                int += 1
                x = BROWN_BLOCKS[int][0] 
                y = BROWN_BLOCKS[int][1]
                z = BROWN_BLOCKS[int][2]
                z = -z    
                self.singleBlock(y + tentX - 3, x + tentY - 4, z + tentZ + 1, BROWN)
            int = -1
            for i in DARK_BROWN_BLOCKS:
                int += 1
                x = DARK_BROWN_BLOCKS[int][0] 
                y = DARK_BROWN_BLOCKS[int][1]
                z = DARK_BROWN_BLOCKS[int][2]
                z = -z    
                self.singleBlock(y + tentX - 3, x + tentY - 4, z + tentZ + 1, DARK_BROWN)
            int = -1
            for i in RED_BLOCKS:
                int += 1
                x = RED_BLOCKS[int][0] 
                y = RED_BLOCKS[int][1]
                z = RED_BLOCKS[int][2]
                z = -z    
                self.singleBlock(y + tentX - 3, x + tentY - 4, z + tentZ + 1, RED)

        def buildTurkeyOnGreenTent(self, tentX, tentY, tentZ):
            int = -1
            for i in GREY_BLOCKS:
                int += 1
                x = GREY_BLOCKS[int][0] 
                y = GREY_BLOCKS[int][1]
                z = GREY_BLOCKS[int][2]
                x = -x
                y = -y
                z = -z    
                self.singleBlock(y + tentX + 2, x + tentY + 3, z + tentZ + 1, GREY)
            int = -1
            for i in ORANGE_BLOCKS:
                int += 1
                x = ORANGE_BLOCKS[int][0] 
                y = ORANGE_BLOCKS[int][1]
                z = ORANGE_BLOCKS[int][2]
                x = -x
                y = -y
                z = -z    
                self.singleBlock(y + tentX + 2, x + tentY + 3, z + tentZ + 1, ORANGE)
            int = -1
            for i in BROWN_BLOCKS:
                int += 1
                x = BROWN_BLOCKS[int][0] 
                y = BROWN_BLOCKS[int][1]
                z = BROWN_BLOCKS[int][2]
                x = -x
                y = -y
                z = -z    
                self.singleBlock(y + tentX + 2, x + tentY + 3, z + tentZ + 1, BROWN)
            int = -1
            for i in DARK_BROWN_BLOCKS:
                int += 1
                x = DARK_BROWN_BLOCKS[int][0] 
                y = DARK_BROWN_BLOCKS[int][1]
                z = DARK_BROWN_BLOCKS[int][2]
                x = -x
                y = -y
                z = -z    
                self.singleBlock(y + tentX + 2, x + tentY + 3, z + tentZ + 1, DARK_BROWN)
            int = -1
            for i in RED_BLOCKS:
                int += 1
                x = RED_BLOCKS[int][0] 
                y = RED_BLOCKS[int][1]
                z = RED_BLOCKS[int][2]
                x = -x
                y = -y
                z = -z    
                self.singleBlock(y + tentX + 2, x + tentY + 3, z + tentZ + 1, RED)

        def singleBlock(self, x, y, z, color):
            block_action.x = x
	    block_action.y = y
	    block_action.z = z
	    block_action.player_id = 32
	    self.map.set_point(x, y, z, color)
	    block_action.value = DESTROY_BLOCK
	    self.send_contained(block_action, save = True)
	    block_action.value = BUILD_BLOCK
	    self.send_contained(block_action, save = True)

	def on_base_spawn(self, x, y, z, base, entity_id):
            if entity_id is BLUE_BASE:
               self.buildTurkeyOnBlueTent(x, y, z)
               BLUE_TENT_COORDS.append(x)
               BLUE_TENT_COORDS.append(y)
               BLUE_TENT_COORDS.append(z)
            elif entity_id is GREEN_BASE:
               self.buildTurkeyOnGreenTent(x, y, z)
               GREEN_TENT_COORDS.append(x)
               GREEN_TENT_COORDS.append(y)
               GREEN_TENT_COORDS.append(z)
            return protocol.on_base_spawn(self, x, y, z, base, entity_id)

	def thanksgiving_server_message(self):
            self.send_chat(S_HAPPY_THANKSGIVING)
            callLater(300, self.thanksgiving_server_message)

    class TurkeyConnection(connection):        

        def invalid_turkey_destroy(self, x, y, z):
            if x >= BLUE_TENT_COORDS[0] - 5 and x <= BLUE_TENT_COORDS[0] + 5:
               if y >= BLUE_TENT_COORDS[1] - 4 and y <= BLUE_TENT_COORDS[1] + 4:
                  if z >= BLUE_TENT_COORDS[2] - 10 and z <= BLUE_TENT_COORDS[2] + 10:
                     return True
            elif x >= GREEN_TENT_COORDS[0] - 5 and x <= GREEN_TENT_COORDS[0] + 5:     
                 if y >= GREEN_TENT_COORDS[1] - 4 and y <= GREEN_TENT_COORDS[1] + 4:
                    if z >= GREEN_TENT_COORDS[2] - 10 and z <= GREEN_TENT_COORDS[2] + 10:
                       return True
            else:
                 return False

        def on_block_destroy(self, x, y, z, mode):
            if self.invalid_turkey_destroy(x, y, z):
               self.send_chat(S_TENT_TURKEY)
	       return False
            return connection.on_block_destroy(self, x, y, z, mode)

        def on_block_build_attempt(self, x, y, z):
            if self.invalid_turkey_destroy(x, y, z):
               self.send_chat(S_TENT_TURKEY)
	       return False
            return connection.on_block_build_attempt(self, x, y, z)

        def on_line_build_attempt(self, points):
            for point in points:
                x, y, z = point
                if self.invalid_turkey_destroy(x, y, z):
                   self.send_chat(S_TENT_TURKEY)
	           return False
            return connection.on_line_build_attempt(self, points)
	            

                  
    return TurkeyProtocol, TurkeyConnection