# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater, seconds
from pyspades.color import interpolate_rgb
from pyspades.server import fog_color
from pyspades.common import make_color
from commands import add, admin, get_player

S_SPECTATING = "{player} is spectating"
S_NOT_ALIVE = "{player} is waiting to respawn"
S_LIGHTNING = "{player} was struck by angry lightning!!!"
S_LIGHTNING_SELF = "You were struck down by angry lightning!!!"
S_LIGHTNING_IRC = "* {admin} called down lightning on {player}"

FOG_INTERVAL = 0.05

def wrap_if_necessary(func_or_value):
    try: func_or_value()
    except: return lambda: func_or_value
    else: return func_or_value

@admin
def lightning(connection, player = None):
    # And I will strike down upon thee with great vengeance and furious anger
    # those who would attempt to poison and destroy My brothers
    
    protocol = connection.protocol
    if player:
        player = get_player(protocol, player)
        is_spectator = player.team and player.team.spectator
        if is_spectator:
            return S_SPECTATING.format(player = player.name)
        if player.hp < 0:
            return S_NOT_ALIVE.format(player = player.name)
        
        callLater(0.1, player.kill)
        callLater(0.1, create_explosion_effect_at_player, player)
        
        message = S_LIGHTNING.format(player = player.name)
        protocol.send_chat(message, sender = player)
        player.send_chat(S_LIGHTNING_SELF)
        if connection in protocol.players:
            message = S_LIGHTNING_IRC.format(admin = connection.name,
                player = player.name)
        else:
            message = '* ' + message
        protocol.irc_say(message)
    effects = [
        FogHold(0.05, (0, 0, 0)),
        FogGradient(0.8, (255, 255, 255), (0, 0, 0), ease_in),
        FogHold(1.0, (0, 0, 0)),
        FogGradient(4.0, (0, 0, 0), protocol.get_real_fog_color, ease_out)
    ]
    protocol.set_fog_effects(effects)

@admin
def fade(connection, r, g, b, time = None):
    color = (int(r), int(g), int(b))
    time = float(time) if time is not None else 1.0
    time = max(0.1, time)
    protocol = connection.protocol
    fade_time = time * 0.25
    effects = [
        FogGradient(fade_time, protocol.get_real_fog_color, color, ease_in),
        FogHold(time, color),
        FogGradient(fade_time, color, protocol.get_real_fog_color, ease_out)
    ]
    protocol.set_fog_effects(effects)

add(lightning)
add(fade)

from pyspades.common import Vertex3
from pyspades.world import Grenade
from pyspades.server import grenade_packet

def create_explosion_effect_at_player(player):
    obj = player.world_object
    if obj is None:
        return
    protocol = player.protocol
    grenade = protocol.world.create_object(Grenade, 0.0, obj.position,
        None, Vertex3(), None)
    grenade_packet.value = grenade.fuse
    grenade_packet.player_id = 32
    grenade_packet.position = grenade.position.get()
    grenade_packet.velocity = grenade.velocity.get()
    protocol.send_contained(grenade_packet)

class FogEffect:
    def start(self):
        pass
    
    def done(self):
        fog_effects = self.protocol.fog_effects
        self.release()
        if fog_effects:
            fog_effects[-1].start()
    
    def release(self):
        self.protocol.fog_effects.remove(self)
    
    def send_fog(self, sender = None):
        sender = sender or self.protocol
        color = self.get_color()
        fog_color.color = make_color(*color)
        sender.send_contained(fog_color, save = True)

class FogHold(FogEffect):
    def __init__(self, duration, color):
        self.duration = duration
        self.color = wrap_if_necessary(color)
        self.call = None
    
    def start(self):
        if not self.call or not self.call.active():
            self.call = callLater(self.duration, self.done)
        if self.protocol.fog_effects[-1] is self:
            self.send_fog()
    
    def get_color(self):
        return self.color()
    
    def release(self):
        if self.call and self.call.active():
            self.call.cancel()
        self.call = None
        FogEffect.release(self)

class FogSimple(FogEffect):
    def __init__(self, color):
        self.color = wrap_if_necessary(color)
    
    def start(self):
        if self.protocol.fog_effects[-1] is self:
            self.send_fog()
        self.done()
    
    def get_color(self):
        return self.color()

linear = lambda t: t
ease_out = quadratic = lambda t: t * t
ease_in = quadratic_inverse = lambda t: 1.0 - ((1.0 - t) ** 2)

class FogGradient(FogEffect):
    def __init__(self, duration, begin, end, interpolator = linear):
        self.duration = duration
        self.begin = wrap_if_necessary(begin)
        self.end = wrap_if_necessary(end)
        self.interpolator = interpolator
        self.loop = LoopingCall(self.apply)
        self.complete = False
    
    def start(self):
        if not self.loop.running:
            self.final_time = seconds() + self.duration
            self.loop.start(FOG_INTERVAL, now = True)
    
    def get_color(self):
        t = 1.0 - (self.final_time - seconds()) / self.duration
        t = min(1.0, self.interpolator(t))
        return interpolate_rgb(self.begin(), self.end(), t)
    
    def apply(self):
        fog_effects = self.protocol.fog_effects
        if self.complete:
            self.done()
            return
        if fog_effects[-1] is self:
            self.send_fog()
        self.complete = seconds() >= self.final_time
    
    def release(self):
        if self.loop.running:
            self.loop.stop()
        self.loop = None
        FogEffect.release(self)

def apply_script(protocol, connection, config):
    class FogEffectProtocol(protocol):
        fog_effects = None
        
        _fog_color = protocol.fog_color
        def _get_fog_color(self):
            if self.fog_effects:
                return self.fog_effects[-1].get_color()
            return self._fog_color
        def _set_fog_color(self, value):
            self._fog_color = value
        fog_color = property(_get_fog_color, _set_fog_color)
        
        def get_real_fog_color(self):
            return self._fog_color
        
        def set_fog_color(self, color):
            if not self.fog_effects:
                return protocol.set_fog_color(self, color)
            self.fog_color = color
        
        def on_map_change(self, map):
            self.fog_effects = []
            protocol.on_map_change(self, map)
        
        def on_map_leave(self):
            self.clear_fog_effects()
            self.fog_effects = None
            protocol.on_map_leave(self)
        
        def clear_fog_effects(self):
            for fog_effect in self.fog_effects[:]:
                fog_effect.release()
        
        def set_fog_effect(self, effect):
            self.clear_fog_effects()
            self.fog_effects.append(effect)
            effect.protocol = self
            effect.start()
        
        def set_fog_effects(self, effects):
            self.clear_fog_effects()
            for effect in reversed(effects):
                effect.protocol = self
                self.fog_effects.append(effect)
            if self.fog_effects:
                self.fog_effects[-1].start()
    
    return FogEffectProtocol, connection