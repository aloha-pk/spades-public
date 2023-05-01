# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from random import randint
from commands import add, admin, alias


@alias('wc')
@admin
def watercolor(self, r, g, b):
    self.protocol.watercolor_r = int(r)
    self.protocol.watercolor_g = int(g)
    self.protocol.watercolor_b = int(b)
    return 'Done. Meow'
add(watercolor)

@alias('wco')
@admin
def watercoloroffset(self, value):
    if int(value) < 0: return 'Come on boy, you should know that a positive value would be for the best for both of us.'
    else:
        self.protocol.watercolor_offset = int(value)
        return 'Offset value set to %i.' % int(value)
add(watercoloroffset)
        
@alias('twc')
@admin
def togglewatercolor(self):
    self.protocol.watercolor_enabled = not self.protocol.watercolor_enabled
    if self.protocol.watercolor_enabled: return 'Watercolors will be modified.'
    else: return 'Watercolors return to their original values.'
add(togglewatercolor)


def apply_script(protocol, connection, config):
	
    class pinkwaterprotocol(protocol):

        watercolor_r = 255 
        watercolor_g = 0
        watercolor_b = 255
        watercolor_offset = 60
        watercolor_enabled = True

        def on_map_change(self, map):

            if self.watercolor_enabled:

                if self.watercolor_r < self.watercolor_offset: offset_r = self.watercolor_r
                else: offset_r = self.watercolor_offset
                if self.watercolor_g < self.watercolor_offset: offset_g = self.watercolor_g
                else: offset_g = self.watercolor_offset
                if self.watercolor_b < self.watercolor_offset: offset_b = self.watercolor_b
                else: offset_b = self.watercolor_offset

                for x in range(512):
                    for y in range(512):
                        map.set_point(x,y,63,(self.watercolor_r - randint(0, offset_r),
                                              self.watercolor_g - randint(0, offset_g),
                                              self.watercolor_b - randint(0, offset_b)))

            return protocol.on_map_change(self, map)

    return pinkwaterprotocol, connection # i love cats