# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from commands import *
from pyspades.world import *
from pyspades.constants import *
from pyspades.server import *
from pyspades.common import *
   
MAX_BLOOD = 75
BLOOD_COLOR = (175, 17, 28) 
COLOR_OFFSET = 10 #can not be higher than the lowest BLOOD_COLOR RGB value 
   
@admin
@name('blood') 
def toggle_blood(self): 
        self.protocol.blood_on = not self.protocol.blood_on 
        if self.protocol.blood_on: 
                message = 'People are bleeding... everywhere!'
                irc_message = 'Bleeding has been enabled.'
        else: 
                message = 'People have stopped bleeding!'
                irc_message = 'Bleeding has been disabled.'
        self.protocol.irc_say(irc_message)               
        return message 
add (toggle_blood) 
   
@admin
@name ('cblood') 
def clean_blood(self): 
        blood_list = self.protocol.blood.keys() 
        for i in blood_list: 
                self.protocol.blood_index = i 
                x, y, z = self.protocol.blood[i][0], self.protocol.blood[i][1], self.protocol.blood[i][2] 
                R1, B1, G1 = BLOOD_COLOR 
                R2, B2, G2 = self.protocol.map.get_color(x, y, z) 
                if self.protocol.map.get_solid(x, y, z): 
                        if math.fabs(R1-R2) <= COLOR_OFFSET and math.fabs(B1-B2) <= COLOR_OFFSET and math.fabs(G1-G2) <= COLOR_OFFSET:  
                                self.clean_block() 
        self.protocol.blood_index = 0
        self.protocol.blood = {} 
        self.protocol.irc_say('The server has been purged of Blood.') 
        return 'Your bloody mess is now clean!'
add(clean_blood) 
  
def apply_script(protocol, connection, config): 
        class BloodConnection(connection): 
                def on_hit(hitter, hit_amount, hittee, type, grenade): 
                        if MAX_BLOOD <= 0 or hitter.team == hittee.team or not hitter.protocol.blood_on: 
                                return connection.on_hit(hitter, hit_amount, hittee, type, grenade) 
                        #hitter.protocol.send_chat("on hit: " + hitter.name + ", " + str(hit_amount) + ", " + hittee.name + ", " + str(type) + ", " + str(grenade)) 
                        result = connection.on_hit(hitter, hit_amount, hittee, type, grenade) 
                        if result == False: 
                                return False
                        if result is not None: 
                                hit_amount = result 
                        #hitter.protocol.send_chat("hit not cancelled, new damage " + str(hit_amount)) 
                        pos = hittee.world_object.position 
                        pos2 = hitter.world_object.position 
                        for i in range(min(10, int(hit_amount / 10) + 1)): 
                                #hitter.protocol.send_chat("trace") 
                                dir = pos - pos2 
                                dir.normalize() 
                                dir.x = dir.x + random.random() * .4 - .2
                                dir.y = dir.y + random.random() * .4 - .2 
                                dir.z = dir.z + random.random() + .2
                                dir.normalize() 
                                c = Character(hittee.world_object.world, pos, dir) 
                                loc = c.cast_ray() 
                                if loc: 
                                #if cast_ray(hittee.world_object.world.map.map, pos.x, pos.y, pos.z, dir.x, dir.y, dir.z, 8, x, y, z): 
                                        x, y, z = loc 
                                        #hitter.protocol.send_chat(str(x) + ", " + str(y) + ", " + str(z) + ", ray found") 
                                        if x < 0 or y < 0 or z < 0 or z >= 512 or y >= 512 or z >= 63: 
                                                continue
                                        #hitter.protocol.send_chat("painting") 
                                        R1, B1, G1 = BLOOD_COLOR 
                                        R2, B2, G2 = hitter.protocol.map.get_color(x, y, z) 
                                        if math.fabs(R1-R2) <= COLOR_OFFSET and math.fabs(B1-B2) <= COLOR_OFFSET and math.fabs(G1-G2) <= COLOR_OFFSET: 
                                                continue
                                        if hitter.protocol.blood_index >= MAX_BLOOD: 
                                                if hitter.protocol.map.get_solid(hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][0], hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][1], hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][2]): 
                                                        hitter.clean_block() 
                                        hitter.bloody_block(x, y, z) 
                        #hitter.protocol.send_chat("end") 
                        return hit_amount 
                def clean_block(hitter): 
                        hitter.protocol.map.set_point(hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][0], hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][1], hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][2], hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][3]) 
                        set_color.value = make_color(*hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][3]) 
                        set_color.player_id = 32
                        hitter.protocol.send_contained(set_color) 
                        block_action.x = hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][0] 
                        block_action.y = hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][1] 
                        block_action.z = hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD][2] 
                        block_action.player_id = 32
                        block_action.value = DESTROY_BLOCK 
                        hitter.protocol.send_contained(block_action, save = True) 
                        block_action.value = BUILD_BLOCK 
                        hitter.protocol.send_contained(block_action, save = True) 
                        return
                def bloody_block(hitter, x, y, z): 
                        R, G, B = BLOOD_COLOR 
                        R, G, B = R + random.randint(-COLOR_OFFSET,COLOR_OFFSET), G + random.randint(-COLOR_OFFSET,COLOR_OFFSET), B + random.randint(-COLOR_OFFSET,COLOR_OFFSET) 
                        RGB = (R, G, B) 
                        hitter.protocol.blood[hitter.protocol.blood_index % MAX_BLOOD] = (x, y, z, hitter.protocol.map.get_color(x, y, z)) 
                        hitter.protocol.blood_index = hitter.protocol.blood_index + 1
                        #hitter.protocol.send_chat(str(hitter.protocol.blood_index)) 
                        hitter.protocol.map.set_point(x, y, z, RGB) 
                        set_color.value = make_color(*RGB) 
                        set_color.player_id = 32
                        hitter.protocol.send_contained(set_color) 
                        block_action.x = x 
                        block_action.y = y 
                        block_action.z = z 
                        block_action.player_id = 32
                        block_action.value = DESTROY_BLOCK 
                        hitter.protocol.send_contained(block_action, save = True) 
                        block_action.value = BUILD_BLOCK 
                        hitter.protocol.send_contained(block_action, save = True) 
                        return
        class BloodProtocol(protocol): 
                blood = {} 
                blood_index = 0
                blood_on = True
                def on_map_leave(self): 
                        self.blood = {} 
                        self.blood_on = True
                        self.blood_index = 0
                        protocol.on_map_leave(self) 
        return BloodProtocol, BloodConnection