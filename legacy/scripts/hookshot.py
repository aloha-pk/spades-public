# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from twisted.internet import reactor # as you can see i seriously wasnt trying at all this time
from math import sqrt
from commands import *

@alias('ho')
@admin
def toggle_hookshot(self):
    self.protocol.hooking = not self.protocol.hooking
    if self.protocol.hooking: 
        self.protocol.send_chat('The hookshot has been enabled!')
        return 'The hookshot has been enabled!'
    else: 
        self.protocol.send_chat('The hookshot has been disabled!')
        return 'The hookshot has been disabled!'
add(toggle_hookshot)

@alias('hl')
@admin
def set_hookshot_length(self, value):
    self.protocol.hookshot_length = float(value)
    return 'Hookshot length set to %f.' % self.protocol.hookshot_length
add(set_hookshot_length)

@alias('hc')
@admin
def set_hookshot_cooldown(self, value):
    self.protocol.cooldown_time = float(value)
    return 'Hookshot cooldown-time set to %f.' % self.protocol.cooldown_time
add(set_hookshot_cooldown)
    
def unhook(hooker): # yeah that is basicaly what you are
    hooker.disable_hook = False

def set_loc(hooker, goal, posi, ori, counter):
    if counter > 255 or (posi[0] < 1 and not hooker.admin) or (posi[0] > 511 and not hooker.admin) or posi[1] < 1 or posi[1] > 512 or posi[2] >= 62 or (sqrt((goal[0]-posi[0])**2 + (goal[1]-posi[1])**2 + (goal[2]-posi[2])**2) <= 2) or hooker.protocol.map.get_solid(posi[0]+ori[0],posi[1]+ori[1],posi[2]+ori[2]) or hooker.protocol.map.get_solid(posi[0],posi[1],posi[2]-1): # dat line 
        return False
    elif not hooker.is_here:
        return False
    else: 
        reactor.callLater(0.01*counter, hooker.set_location, (posi[0],posi[1],posi[2]-1)) # who needs vertex3 when you can make everything more complicated
        return set_loc(hooker, goal, (posi[0]+ori[0], posi[1]+ori[1], posi[2]+ori[2]), ori, counter+1) # recursion to make it even more unreadable


def apply_script(protocol, connection, config):

    class hookprotocol(protocol):
        hookshot_length = 90
        hooking = True
        cooldown_time = 0 # only for pussies

    class hooconnection(connection):
        disable_hook = False
        has_intel = False
        is_here = True

        #def on_hit(self, hit_amount, hit_player, type, grenade):
        #    hit_player.disable_hook = True
        #    reactor.callLater(self.protocol.cooldown_time, unhook, hit_player)
        #    return connection.on_hit(self, hit_amount, hit_player, type, grenade)

        def on_animation_update(self, jump, crouch, sneak, sprint):
            if self.protocol.hooking and sneak and self.world_object.cast_ray(self.protocol.hookshot_length) != None and self.disable_hook != True and self.has_intel != True:
                try:
                    a,b,c = self.world_object.cast_ray(self.protocol.hookshot_length)
                    d,e,f = self.world_object.position.get()
                    g,h,i = self.world_object.orientation.get()
                    self.disable_hook = True
                    reactor.callLater(self.protocol.cooldown_time, unhook, self)
                    set_loc(self, (a,b,c), (d,e,f), (g,h,i), 10) # man i should realy stop using so many tuples
                except:
                    return False
            return connection.on_animation_update(self, jump, crouch, sneak, sprint)

        def on_flag_take(u):
            u.has_intel = True
            return connection.on_flag_take(u)

        def on_flag_drop(still_u):
            still_u.has_intel = False
            return connection.on_flag_drop(still_u)

        def on_flag_capture(its_u_again):
            its_u_again.has_intel = False
            return connection.on_flag_capture(its_u_again)

        def on_disconnect(self):
            self.is_here = False
            return connection.on_disconnect(self)

    return hookprotocol, hooconnection