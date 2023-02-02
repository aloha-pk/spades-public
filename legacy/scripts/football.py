# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from math import cos, sin, radians
from weakref import WeakKeyDictionary
from functools import partial
from twisted.internet.reactor import callLater, seconds
from pyspades.common import Vertex3
from pyspades.server import move_object, weapon_reload, create_player, input_data
from pyspades.collision import distance_3d_vector
from pyspades.constants import *
from commands import name, add, get_player, admin

@name('addball')
@admin
def add_ball(connection, player = None):
    protocol = connection.protocol
    if player is not None:
        player = get_player(protocol, player)
    elif connection in protocol.players:
        player = connection
    else:
        raise ValueError()
    obj = player.world_object
    if obj is None:
        raise ValueError()
    
    ball = protocol.create_ball(obj.position.get())
    if ball is None:
        return 'Ball limit reached'
    ball.velocity.set_vector(obj.orientation)
    ball.velocity.normalize()
    ball.velocity *= 0.5
    ball.last_kicked_by = player
    return 'Ball created'

@name('noballs')
@admin
def remove_balls(connection):
    protocol = connection.protocol
    for ball in protocol.balls:
        ball.remove()
    protocol.balls = []
    return 'Balls removed'

@name('murderball')
def toggle_murderball(connection):
    protocol = connection.protocol
    protocol.murderball = murderball = not protocol.murderball
    on_off = 'ON' if murderball else 'OFF'
    if murderball:
        protocol.send_chat('MURDERBALL MODE! Weapons enabled')
    else:
        protocol.send_chat('Football mode. Weapons disabled')
    protocol.irc_say('* %s toggled murderball %s' % (connection.name, on_off))

add(add_ball)
add(remove_balls)

STEPS = 8
STEP_SIZE = 1.0 / STEPS
RESTITUTION = 0.58
FRICTION = 0.988
GRAVITY = 0.013 * STEP_SIZE
DAMPING = 0.997 ** STEP_SIZE
COOLDOWN = 0.02
Z_OFFSET = GRAVITY
SEND_THRESHOLD = GRAVITY
SEND_FPS = 30.0
SEND_FREQUENCY = 1 / SEND_FPS
KICK_RANGE = 1.6
KICK_RANGE_SQR = KICK_RANGE ** 2
KICK_COOLDOWN = 0.5
DRIBBLE_FORCE = 0.7
DRIBBLE_ANGLE = radians(5.0)
KICK_FORCE = 0.61
KICK_ANGLE = radians(22.0)
HIGH_KICK_FORCE = 0.53
HIGH_KICK_ANGLE = radians(42.0)
STOP_RANGE = KICK_RANGE + 0.2
STOP_RANGE_SQR = STOP_RANGE ** 2
STUCK_BALL_TIMEOUT = 30.0 # seconds

def aabb_2d(x, y, i, j, u, v):
    return x >= i and y >= j and x < u and y < v

def aabb(x, y, z, i, j, k, u, v, w):
    return x >= i and y >= j and z >= k and x < u and y < v and z < w

def solid_or_outside(map, x, y, z, area_check = None):
    if z < 0 or z >= 63 or (area_check and not area_check(x, y, z)):
        return True
    result = map.get_solid(x, y, z)
    return result is None or result

def empty_weapon(player):
    weapon = player.weapon_object
    weapon.set_shoot(False)
    weapon.current_ammo = 0
    weapon.current_stock = 0
    weapon_reload.player_id = player.player_id
    weapon_reload.clip_ammo = weapon.current_ammo
    weapon_reload.reserve_ammo = weapon.current_stock
    player.send_contained(weapon_reload)
    player.tool = BLOCK_TOOL if player.blocks > 0 else SPADE_TOOL

def fill_create_player(player, team):
    x, y, z = player.world_object.position.get()
    create_player.x = x
    create_player.y = y
    create_player.z = z
    create_player.name = player.name
    create_player.player_id = player.player_id
    create_player.weapon = player.weapon
    create_player.team = team.id

def force_jump(player):
    world_object = player.world_object
    world_object.jump = True
    input_data.player_id = player.player_id
    input_data.up = world_object.up
    input_data.down = world_object.down
    input_data.left = world_object.left
    input_data.right = world_object.right
    input_data.jump = world_object.jump
    input_data.crouch = world_object.crouch
    input_data.sneak = world_object.sneak
    input_data.sprint = world_object.sprint
    player.protocol.send_contained(input_data)

class Ball(Vertex3):
    last_action = None
    last_moved = None
    last_kicked_by = None
    stopped = False
    disabled = False
    removed = False
    
    def __init__(self, protocol, entity, *arg, **kw):
        Vertex3.__init__(self, *arg, **kw)
        self.protocol = protocol
        self.entity = entity
        self.velocity = Vertex3()
        self.last_position = Vertex3()
        self.player_to_ball = Vertex3()
        self.distance_to_player = WeakKeyDictionary()
        self.send_position()
    
    def step(self, dt):
        # physics and collision
        
        velocity = self.velocity
        velocity.z += GRAVITY
        velocity *= DAMPING
        old_x, old_y, old_z = self.get()
        self += velocity * dt
        xi, yi, zi = int(self.x), int(self.y), int(self.z - Z_OFFSET)
        
        map = self.protocol.map
        area_check = self.protocol.area_check
        if solid_or_outside(map, xi, yi, zi, area_check):
            old_xi, old_yi, old_zi = int(old_x), int(old_y), int(old_z - Z_OFFSET)
            if zi != old_zi and ((xi == old_xi and yi == old_yi) or not
                solid_or_outside(map, xi, yi, old_zi, area_check)):
                velocity.z *= -1
                velocity *= FRICTION
            elif xi != old_xi and ((yi == old_yi and zi == old_zi) or not
                solid_or_outside(map, old_xi, yi, zi, area_check)):
                velocity.x *= -1
            elif yi != old_yi and ((xi == old_xi and zi == old_zi) or not
                solid_or_outside(map, xi, old_yi, zi, area_check)):
                velocity.y *= -1
            velocity *= RESTITUTION
            self.x = old_x
            self.y = old_y
            self.z = old_z
        if self.z > 62.2:
            self.z -= 1.0
        
        # player interaction
        
        if self.disabled:
            return
        now = seconds()
        last_action = self.last_action
        if last_action is not None and now - last_action <= COOLDOWN:
            # ball has a short cooldown to avoid simultaneous kicking
            return
        player_to_ball = self.player_to_ball
        for player in self.protocol.players.itervalues():
            obj = player.world_object
            if obj is None or player.hp <= 0:
                continue
            pos = obj.position
            player_to_ball.set(self.x - pos.x, self.y - pos.y, 0.0)
            distance_sqr = player_to_ball.length_sqr()
            last_distance = self.distance_to_player.get(player, 0.0)
            self.distance_to_player[player] = distance_sqr
            if self.z < pos.z:
                # ball is above player hitbox
                continue
            if (not self.stopped and last_distance > STOP_RANGE_SQR and
                distance_sqr <= STOP_RANGE_SQR):
                # stop just outside of kicking range
                player_to_ball.normalize()
                player_to_ball *= STOP_RANGE
                velocity.x = 0.0
                velocity.y = 0.0
                new_x = pos.x + player_to_ball.x
                new_y = pos.y + player_to_ball.y
                if not solid_or_outside(map, new_x, new_y, self.z, area_check):
                    self.x, self.y = new_x, new_y
                self.stopped = True
                break
            last_kick = player.last_kick
            if ((last_kick is None or now - last_kick > KICK_COOLDOWN) and
                last_distance > KICK_RANGE_SQR and distance_sqr <= KICK_RANGE_SQR):
                # kick
                player.last_kick = now
                self.last_action = now
                self.stopped = False
                self.kick(player)
                self.last_kicked_by = player
                if obj.velocity.z == 0.0:
                    # this will slow the player down
                    force_jump(player)
                break
    
    def update(self):
        for i in xrange(STEPS):
            self.step(STEP_SIZE)
    
    def network_update(self):
        delta = distance_3d_vector(self.last_position, self)
        if delta > SEND_THRESHOLD:
            self.last_moved = seconds()
            self.send_position()
            self.last_position.set_vector(self)
    
    def kick(self, player):
        pos = player.world_object.position
        dir = Vertex3(self.x - pos.x, self.y - pos.y, 0.0)
        dir.normalize()
        ori = player.world_object.orientation
        ori_flat = Vertex3(ori.x, ori.y, 0.0)
        ori_flat.normalize()
        dot = ori_flat.dot(dir)
        long_kick = player.world_object.velocity.z < 0.0
        high_kick = long_kick and ori.z <= -0.25
        if dot > 0.3:
            # let the player aim the shot if it would be reasonable
            dir.set_vector(ori_flat)
        if high_kick:
            angle, force = HIGH_KICK_ANGLE, HIGH_KICK_FORCE
        elif long_kick:
            angle, force = KICK_ANGLE, KICK_FORCE
        else:
            angle, force = DRIBBLE_ANGLE, DRIBBLE_FORCE
        forward = cos(angle) * force
        up = -sin(angle) * force
        self.velocity.translate(dir.x * forward, dir.y * forward, up)
    
    def reset(self):
        self.velocity.zero()
        self.last_position.zero()
        self.last_action = None
        self.last_kicked_by = None
        self.disabled = False
        self.stopped = False
    
    def remove(self):
        self.protocol.base_entities.append(self.entity)
        self.set_vector(self.entity)
        self.send_position()
        self.removed = True
    
    def send_position(self, sender = None):
        sender = sender or self.protocol.send_contained
        entity = self.entity
        move_object.object_type = entity.id
        move_object.state = entity.team.id if entity.team else NEUTRAL_TEAM
        move_object.x = self.x
        move_object.y = self.y
        move_object.z = self.z
        sender(move_object)

def apply_script(protocol, connection, config):
    game_mode_name = config.get('game_mode', 'ctf')
    if game_mode_name == 'football':
        add(toggle_murderball)
    
    class FootballConnection(connection):
        last_kick = None
        
        def score_goal(self, against_team, ball):
            old_team = self.team
            if self.team is against_team:
                # own goal, temporarily switch teams
                self.team = against_team.other
                fill_create_player(self, self.team)
                self.protocol.send_contained(create_player, save = True)
            against_team.flag.player = self
            self.capture_flag()
            if old_team is against_team:
                self.team = old_team
                fill_create_player(self, self.team)
                self.protocol.send_contained(create_player, save = True)
            ball.disabled = True
            flash_color = against_team.other.color
            self.protocol.fog_flash(flash_color)
            callLater(0.4, self.protocol.fog_flash, flash_color)
            callLater(0.8, self.protocol.fog_flash, flash_color)
            callLater(3.0, self.protocol.reset_ball_and_teams, ball)
        
        def on_connect(self):
            if self.protocol.balls:
                is_self = lambda player: player is self
                send_me = partial(self.protocol.send_contained, rule = is_self)
                for ball in self.protocol.balls:
                    ball.send_position(send_me)
            connection.on_connect(self)
        
        def on_reset(self):
            for ball in self.protocol.balls:
                if ball.last_kicked_by is self:
                    ball.last_kicked_by = None
            connection.on_reset(self)
        
        def on_login(self, name):
            if self.protocol.football and not self.protocol.balls:
                self.protocol.create_ball(self.protocol.ball_spawn)
            connection.on_login(self, name)
        
        def on_team_changed(self, old_team):
            if self.team and self.team.spectator:
                for ball in self.protocol.balls:
                    if ball.last_kicked_by is self:
                        ball.last_kicked_by = None
            connection.on_team_changed(self, old_team)
        
        def on_spawn(self, pos):
            if self.protocol.football and not self.protocol.murderball:
                empty_weapon(self)
            connection.on_spawn(self, pos)
        
        def on_hit(self, hit_amount, hit_player, type, grenade):
            if self.protocol.football and not self.protocol.murderball:
                return False
            return connection.on_hit(self, hit_amount, hit_player, type, grenade)
        
        def on_grenade(self, time_left):
            if self.protocol.football and not self.protocol.murderball:
                return False
            return connection.on_grenade(self, time_left)
        
        def grenade_exploded(self, grenade):
            for ball in self.protocol.balls:
                direction = ball - grenade.position
                direction.z = abs(direction.z)
                if direction.z < 0.2:
                    direction.z += 1.0
                distance = direction.normalize()
                range = 8.0
                if distance > range:
                    continue
                max_force = 1.3
                force = min(max_force, (range - distance) / distance * 2.0)
                ball.velocity += direction * force
            connection.grenade_exploded(self, grenade)
        
        def on_flag_take(self):
            if self.protocol.football:
                return False
            return connection.on_flag_take(self)
        
        def on_block_destroy(self, x, y, z, mode):
            if self.protocol.football and not self.protocol.murderball:
                return False
            return connection.on_block_destroy(self, x, y, z, mode)
        
        def on_block_build_attempt(self, x, y, z):
            if self.protocol.football:
                if not self.protocol.murderball:
                    return False
                if self.protocol.is_penalty_area(x, y, z):
                    return False
            return connection.on_block_build_attempt(self, x, y, z)
        
        def on_line_build_attempt(self, points):
            if self.protocol.football:
                if not self.protocol.murderball:
                    return False
                for point in points:
                    if self.protocol.is_penalty_area(*point):
                        return False
            return connection.on_line_build_attempt(self, points)
    
    class FootballProtocol(protocol):
        game_mode = CTF_MODE
        football = game_mode_name == 'football'
        base_entities = None
        balls = None
        _murderball = False
        
        def _get_murderball(self):
            return self._murderball
        def _set_murderball(self, value):
            if self._murderball == value:
                return
            self._murderball = value
            for player in self.players.itervalues():
                if value:
                    player.refill()
                else:
                    empty_weapon(player)
        murderball = property(_get_murderball, _set_murderball)
        
        def create_ball(self, location):
            try:
                entity = self.base_entities.pop()
            except IndexError:
                return
            ball = Ball(self, entity, *location)
            self.balls.append(ball)
            return ball
        
        def reset_ball_and_teams(self, ball):
            if ball.removed:
                ball = self.create_ball(self.ball_spawn)
            else:
                ball.reset()
                ball.set(*self.ball_spawn)
                ball.send_position()
            for player in self.players.values():
                if player.team is not None:
                    player.spawn()
        
        def update_entities(self):
            map = self.map
            for ball in self.balls:
                if map.get_solid(ball.x, ball.y, ball.z - 1):
                    ball.z -= 1
                    while map.get_solid(ball.x, ball.y, ball.z - 1):
                        ball.z -= 1
                    ball.send_position()
            protocol.update_entities(self)
        
        def fog_flash(self, color):
            old_color = self.get_fog_color()
            self.set_fog_color(color)
            callLater(0.2, self.set_fog_color, old_color)
        
        def is_indestructable(self, x, y, z):
            if self.is_penalty_area(x, y, z):
                return True
            return protocol.is_indestructable(self, x, y, z)
        
        def is_penalty_area(self, x, y, z):
            if self.football:
                if (aabb(x, y, z, *self.blue_team.goal) or
                    aabb(x, y, z, *self.green_team.goal)):
                    return True
                for penalty_area in self.penalty_areas:
                    if aabb_2d(x, y, *penalty_area):
                        return True
            return False
        
        def on_map_change(self, map):
            self.balls = []
            self.base_entities = []
            if self.football:
                info = self.map_info.info
                self.ball_spawn = info.ball
                self.area = area = info.area
                self.blue_team.goal = blue_goal = info.blue_goal
                self.green_team.goal = green_goal = info.green_goal
                def area_check(x, y, z):
                    return (aabb_2d(x, y, *area) or 
                        aabb(x, y, z, *blue_goal) or
                        aabb(x, y, z, *green_goal))
                self.area_check = area_check
                self.penalty_areas = getattr(info, 'penalty_areas', [])
                self.murderball = getattr(info, 'murderball', False)
            protocol.on_map_change(self, map)
        
        def on_base_spawn(self, x, y, z, base, entity_id):
            self.base_entities.append(base)
            return protocol.on_base_spawn(self, x, y, z, base, entity_id)
        
        def on_world_update(self):
            removed = False
            for ball in self.balls:
                ball.update()
                if self.football and ball.last_kicked_by and not ball.disabled:
                    x, y, z = ball.get()
                    if aabb(x, y, z, *self.blue_team.goal):
                        ball.last_kicked_by.score_goal(self.blue_team, ball)
                    elif aabb(x, y, z, *self.green_team.goal):
                        ball.last_kicked_by.score_goal(self.green_team, ball)
            if self.loop_count % int(UPDATE_FPS / SEND_FPS) == 0:
                now = seconds()
                for ball in self.balls:
                    ball.network_update()
                    if (self.football and
                        ball.last_action is not None and
                        ball.last_moved is not None and
                        now - ball.last_moved > STUCK_BALL_TIMEOUT):
                        # the ball may be stuck or the game empty, reset match
                        if self.players:
                            self.reset_ball_and_teams(ball)
                        else:
                            ball.remove()
                            removed = True
            if removed:
                self.balls = [ball for ball in self.balls if not ball.removed]
            protocol.on_world_update(self)
    
    return FootballProtocol, FootballConnection