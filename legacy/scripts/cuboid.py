# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

import __builtin__
from itertools import product
from pyspades.world import cube_line
from pyspades.server import block_action, block_line
from pyspades.constants import *
from commands import add, admin, name

S_PLANE_USAGE = 'Usage: /plane <-x> <+x> <-y> <+y>'
S_PLANE_CANCEL = 'No longer plane-building'
S_PLANE = 'Dig or build to make or remove slabs, with the block as center. ' \
    'Abort with /plane'
S_EXIT_BLOCKING_STATE = "You must first leave {state} mode!"
S_TOO_MANY_PARAMETERS = 'ERROR: too many parameters'
S_NOT_ENOUGH_PARAMETERS = 'ERROR: not enough parameters'
S_WRONG_PARAMETER_TYPE = 'ERROR: wrong parameter type'

def parseargs(signature, args):
    signature = signature.split()
    if len(args) > len(signature):
        raise ValueError(S_TOO_MANY_PARAMETERS)
    result = []
    optional = False
    for i, s in enumerate(signature):
        func_name = s.strip('[]')
        optional = optional or func_name != s
        try:
            typecast = getattr(__builtin__, func_name)
            result.append(typecast(args[i]))
        except ValueError:
            raise ValueError(S_WRONG_PARAMETER_TYPE)
        except IndexError:
            if not optional:
                raise ValueError(S_NOT_ENOUGH_PARAMETERS)
            result.append(None)
    return result

@admin
def plane(connection, *args):
    protocol = connection.protocol
    if connection not in protocol.players:
        raise ValueError()
    player = connection
    state = player.states.top()
    
    if state:
        if state.get_parent().name == 'plane' and not args:
            # cancel plane command
            player.states.exit()
            return
        elif state.blocking:
            # can't switch from a blocking mode
            return S_EXIT_BLOCKING_STATE.format(state = state.name)
    
    usage = S_PLANE_USAGE
    try:
        x1, x2, y1, y2 = parseargs('int int int int', args)
        player.states.exit()
        player.states.enter(PlaneState(x1, y1, x2, y2))
    except ValueError as err:
        player.send_chat(usage)
        return str(err)
    except IndexError:
        return usage

#add(plane)

def prism(x1, y1, z1, x2, y2, z2):
    return product(xrange(x1, x2), xrange(y1, y2), xrange(z1, z2))

def prism_lines(x1, y1, z1, x2, y2, z2):
    u, v, w = x2 - x1, y2 - y1, z2 - z1
    if u > max(v, w):
        for y in xrange(y1, y2):
            for z in xrange(z1, z2):
                yield x1, y, z, x2 - 1, y, z
    elif v > max(w, u):
        for z in xrange(z1, z2):
            for x in xrange(x1, x2):
                yield x, y1, z, x, y2 - 1, z
    else:
        for x in xrange(x1, x2):
            for y in xrange(y1, y2):
                yield x, y, z1, x, y, z2 - 1

def plane_operation(player, x, y, z, size, value):
    theta = player.world_object.orientation
    th_cos, th_sin = int(round(theta.x)), int(round(theta.y))
    if abs(th_cos) == abs(th_sin):
        return
    x, y, z = int(x), int(y), int(z)
    x1, z1, x2, z2 = size
    y1, y2 = 0, 0
    u1 = y1 * th_cos - x1 * th_sin + x
    v1 = y1 * th_sin + x1 * th_cos + y
    w1 = z1 + z
    u2 = y2 * th_cos - x2 * th_sin + x
    v2 = y2 * th_sin + x2 * th_cos + y
    w2 = z2 + z
    u1, u2 = max(0, min(u1, u2)), min(511, max(u1, u2, 0) + 1)
    v1, v2 = max(0, min(v1, v2)), min(511, max(v1, v2, 0) + 1)
    w1, w2 = max(0, min(w1, w2) + 1), min(63, max(w1, w2) + 1)
    protocol = player.protocol
    if value == DESTROY_BLOCK:
        block_action.value = value
        block_action.player_id = player.player_id
        for i, j, k in prism(u1, v1, w1, u2, v2, w2):
            if protocol.map.destroy_point(i, j, k):
                block_action.x = i
                block_action.y = j
                block_action.z = k
                protocol.send_contained(block_action, save = True)
    elif value == BUILD_BLOCK:
        block_line.player_id = player.player_id
        for i1, j1, k1, i2, j2, k2 in prism_lines(u1, v1, w1, u2, v2, w2):
            line = cube_line(i1, j1, k1, i2, j2, k2)
            for i, j, k in line:
                protocol.map.set_point(i, j, k, player.color)
            block_line.x1 = i1
            block_line.y1 = j1
            block_line.z1 = k1
            block_line.x2 = i2
            block_line.y2 = j2
            block_line.z2 = k2
            protocol.send_contained(block_line, save = True)
    
class State(object):
    name = None
    blocking = False
    parent_state = None
    
    def on_enter(self, protocol, player):
        pass
    
    def on_exit(self, protocol, player):
        pass
    
    def get_parent(self):
        return self.parent_state if self.parent_state else self

class PlaneState(State):
    name = 'plane'
    
    def __init__(self, x1, y1, x2, y2):
        self.size = (x1, y1, x2, y2)
    
    def on_enter(self, protocol, player):
        return S_PLANE
    
    def on_exit(self, protocol, player):
        return S_PLANE_CANCEL

class StateStack:
    stack = None
    protocol = None
    connection = None
    
    def __init__(self, connection):
        self.stack = []
        self.connection = connection
        self.protocol = connection.protocol
    
    def top(self):
        return self.stack[-1] if self.stack else None
    
    def enter(self, state):
        self.stack.append(state)
        result = state.on_enter(self.protocol, self.connection)
        if result:
            self.connection.send_chat(result)
    
    def push(self, state):
        self.stack.append(state)
    
    def pop(self):
        state = self.stack.pop()
        result = state.on_exit(self.protocol, self.connection)
        if result:
            self.connection.send_chat(result)
        state = self.top()
        if state:
            result = state.on_enter(self.protocol, self.connection)
            if result:
                self.connection.send_chat(result)
    
    def exit(self):
        while self.stack:
            self.pop()

def apply_script(protocol, connection, config):
    class CuboidConnection(connection):
        states = None
        
        def on_reset(self):
            if self.states:
                self.states.stack = []
            connection.on_reset(self)
        
        def on_login(self, name):
            if self.states is None:
                self.states = StateStack(self)
            connection.on_login(self, name)
        
        def on_disconnect(self):
            self.states = None
            connection.on_disconnect(self)
        
        def on_block_removed(self, x, y, z):
            state = self.states.top()
            if state and state.name == 'plane':
                plane_operation(self, x, y, z, state.size, DESTROY_BLOCK)
            connection.on_block_removed(self, x, y, z)
        
        def on_block_build(self, x, y, z):
            state = self.states.top()
            if state and state.name == 'plane':
                plane_operation(self, x, y, z, state.size, BUILD_BLOCK)
            connection.on_block_build(self, x, y, z)
        
        def on_line_build(self, points):
            state = self.states.top()
            if state and state.name == 'plane':
                for x, y, z in points:
                    plane_operation(self, x, y, z, state.size, BUILD_BLOCK)
            connection.on_line_build(self, points)
    
    return protocol, CuboidConnection

