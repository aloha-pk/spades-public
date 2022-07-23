# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Lightning 

*Lightning bolts randomly spawn throughout the map*

Creator: FerrariFlunker
"""
from twisted.internet.reactor import callLater, seconds
from pyspades.server import block_action, set_color, make_color, orientation_data, grenade_packet
from pyspades.common import coordinates, Vertex3
from pyspades.constants import *
from pyspades import world
from pyspades.world import Grenade
import random



LIGHTNING_COLOR = (255, 255, 255)
LIGHTNING_POINTS = []

                   
def apply_script(protocol, connection, config):

    class LightningProtocol(protocol):
        def __init__(self, *args, **kwargs):
            protocol.__init__(self, *args, **kwargs) 
            self.startLightning()


	def startLightning(self):
	    randomTimer = random.randint(10, 15)
            randomX = random.randint(112, 384)
            randomY = random.randint(192, 320)
            self.buildLightning(randomX, randomY, 1)
            callLater(randomTimer, self.startLightning)
	     

	def buildLightning(self, xPos, yPos, zPos):
            solid = self.map.get_solid(xPos, yPos, zPos)
            if solid or solid is None or zPos == 59:
               callLater(.6, self.destroyLightning)
               self.lightningBlast(xPos, yPos, zPos)
	       self.flashSky()               
            else:               
               self.singleBlock(xPos, yPos, zPos, LIGHTNING_COLOR)
               randomX = random.randint(-1, 1)
               randomY = random.randint(-1, 1)
               callLater(.01, self.buildLightning, xPos + randomX, yPos + randomY, zPos + 1)

	
	def destroyLightning(self):
            while len(LIGHTNING_POINTS) > 0:  
                x = LIGHTNING_POINTS[0][0]
                y = LIGHTNING_POINTS[0][1]
                z = LIGHTNING_POINTS[0][2]
                block_action.x = x 
                block_action.y = y 
                block_action.z = z 
                block_action.player_id = 32
                block_action.value = DESTROY_BLOCK 
                self.send_contained(block_action, save = True)
                self.map.destroy_point(x, y, z) 
	        LIGHTNING_POINTS.remove(LIGHTNING_POINTS[0])

	
	def flashSky(self):
            original_fog_color = self.fog_color
            self.set_fog_color((240, 243, 247))
	    callLater(.15, self.resetFog, original_fog_color)


	def resetFog(self, color):
            self.set_fog_color(color)


        def lightningBlast(self, xPos, yPos, zPos):
            position = Vertex3(xPos, yPos, zPos - 1)
            velocity = Vertex3(0.0, 0.0, 0.0)
            grenade = self.world.create_object(Grenade, 0.0, position, None, velocity, None)
            grenade_packet.value = 0.0
            grenade_packet.player_id = 32
            grenade_packet.position = position.get()
            grenade_packet.velocity = velocity.get()
            self.send_contained(grenade_packet)
                 

	
	def singleBlock(self, x, y, z, color):
            LIGHTNING_POINTS.append([x, y, z])
            self.map.set_point(x, y, z, color)
            set_color.value = make_color(*color) 
            set_color.player_id = 32
            self.send_contained(set_color) 
            block_action.x = x 
            block_action.y = y 
            block_action.z = z 
            block_action.player_id = 32
            block_action.value = DESTROY_BLOCK 
            self.send_contained(block_action, save = True) 
            block_action.value = BUILD_BLOCK 
            self.send_contained(block_action, save = True)     

                               

        

	                  
    return LightningProtocol, connection