# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
todo

Maintainer: hompy
"""

# TODO
# Laggy players phase through the floor and their position isn't reset

import json
import os
from math import cos, sin, radians
from datetime import timedelta
from itertools import izip, count
from twisted.internet.reactor import seconds
from twisted.internet.task import LoopingCall
from pyspades.server import set_tool, weapon_reload, create_player, set_hp
from pyspades.server import position_data
from pyspades.weapon import SMG
from pyspades.common import Vertex3
from pyspades.collision import collision_3d
from pyspades.constants import *
from commands import add, admin, name, alias, join_arguments
from map import DEFAULT_LOAD_DIR

EDIT_MODE = True

S_LIST_HEADER = 'Active machineguns: '
S_LIST_EMPTY = 'No active machineguns'
S_LIST_ITEM = "'{label}' #{number}"
S_STATS = ("'{label}' #{number} - Bullets fired: {bullets}, "
    "time active: {time}, players killed: {kills}, user deaths: {deaths}")
S_TOOL_USAGE = 'Usage: /mg <list|stats #>'
S_EDIT_TOOL_USAGE = 'Usage: /mg <new|entry|nest|angles|cancel|list|edit #|' \
    'delete #|stats #|save>'
S_NEW_USAGE = 'Usage: /mg new <machinegun_name>'
S_NEW = "Setting up {team} machinegun '{label}'"
S_ALREADY_EDITING = "You're already editing machinegun '{label}'! Cancel " \
    "with /mg cancel"
S_ENTRY_SET = 'Entry point set to {location}'
S_NEST_SET = 'Nest location set to {location}'
S_ADD_ENTRY = 'Stand at entry point and type /mg entry'
S_ADD_NEST = 'Stand at machinegun nest and type /mg nest'
S_ACTIVE = 'Machinegun #{number} active!'
S_EDIT_FIRST = ('First make a new machinegun with /mg new or edit '
    'an existing one with /mg edit #')
S_EDIT_CANCEL = "No longer editing machinegun '{label}'"
S_EDITING = "Editing machinegun #{number} '{label}'"
S_DELETED = "Deleted machinegun #{number} '{label}'"
S_INVALID_ID = 'Invalid machinegun #! Use /mg list to see existing ones'
S_ANGLES = 'Angles set to {h_fov:.1f}, {up_fov:.1f}, {down_fov:.1f}'
S_ANGLES_USAGE = 'Usage: /mg angles <horiz={h_fov:.1f}> <up={up_fov:.1f}> ' \
    '<down={down_fov:.1f}>'
S_JUMP_TO_USE = '* Jump here to use this machinegun'
S_HP_REQ_NOT_MET = 'You must have full health to use a machinegun'
S_IN_USE_BY = 'This machinegun is being used by {player}!'
S_BELONGS_TO_TEAM = 'This machinegun can only be used by the {team} team!'
S_NOT_WORKING = 'This machinegun is not working'
S_SAVED = 'Machineguns saved'

REQUIRES_FULL_HP = False
DAMAGE_MULTIPLIER = 3.0
SMG_RAPID_INTERVAL = 0.04
REPOSITION_FREQUENCY = 0.05

@alias('mg')
@name('machinegun')
@admin
def machinegun_tools(connection, *args):
    protocol = connection.protocol
    usage = S_EDIT_TOOL_USAGE if EDIT_MODE else S_TOOL_USAGE
    if not args:
        return usage
    result = None
    mode = args[0].lower()
    
    if (mode == 'stats' or
        (EDIT_MODE and
            (mode == 'delete' or
            (mode == 'edit' and connection in protocol.players)))):
        if len(args) != 2:
            return usage
        
        number_arg = args[1]
        if number_arg.startswith('#'):
            number_arg = number_arg[1:]
        i = int(number_arg)
        if i >= len(protocol.machineguns):
            return S_INVALID_ID
    
    # non-edit tools that can be used outside the game
    
    if mode == 'save':
        protocol.dump_machinegun_json()
    elif mode == 'list':
        items = []
        for machinegun, i in izip(protocol.machineguns, count()):
            item = S_LIST_ITEM.format(label = machinegun.label, number = i)
            items.append(item)
        result = S_LIST_HEADER + ', '.join(items) if items else S_LIST_EMPTY
    elif mode == 'stats':
        machinegun = protocol.machineguns[i]
        td = machinegun.get_time_active()
        result = S_STATS.format(label = machinegun.label, number = i,
            bullets = machinegun.rounds_fired, time = td,
            kills = machinegun.kills, deaths = machinegun.deaths)
    
    # editing tools that can be used outside the game
    
    if not EDIT_MODE or result:
        return result
    if mode == 'delete':
        machinegun = protocol.machineguns.pop(i)
        machinegun.release()
        for p in protocol.players.values():
            if p.editing_machinegun is machinegun:
                message = S_EDIT_CANCEL.format(label = machinegun.label)
                p.send_chat(message)
                p.editing_machinegun = None
        return S_DELETED.format(number = i, label = machinegun.label)
    
    # editing tools that must be used ingame
    
    if connection not in protocol.players:
        raise ValueError()
    player = connection
    machinegun = player.editing_machinegun
    
    # with no previous mg selected
    
    if mode == 'edit' or mode == 'new':
        if machinegun:
            return S_ALREADY_EDITING.format(label = machinegun.label)
        
        if mode == 'edit':
            machinegun = protocol.machineguns[i]
            result = S_EDITING.format(number = i, label = machinegun.label)
        elif mode == 'new':
            if len(args) < 2:
                return S_NEW_USAGE
            value = join_arguments(args[1:]).strip()
            if not value:
                return S_NEW_USAGE
            machinegun = Machinegun(protocol, value, player.team)
            machinegun.active = False
            message = S_NEW.format(team = player.team.name, label = value,
                number = len(protocol.machineguns))
            player.send_chat(message)
            result = S_ADD_ENTRY
        
        player.editing_machinegun = machinegun
        return result
    
    # while already editing a mg
    
    if not machinegun:
        return S_EDIT_FIRST
    
    if mode == 'entry' or mode == 'nest':
        x, y, z = player.get_location()
        if player.world_object.crouch:
            z -= 0.9
        if mode == 'entry':
            x = round(x * 2.0) / 2.0
            y = round(y * 2.0) / 2.0
            z = round(z)
            xyz = (x, y, z)
            machinegun.entry_location = xyz
            message = S_ENTRY_SET.format(location = xyz)
        else:
            x = round(x) + machinegun.forward.x
            y = round(y * 2.0) / 2.0
            z = int(z) + 0.6
            xyz = (x, y, z)
            machinegun.location = xyz
            message = S_NEST_SET.format(location = xyz)
        player.send_chat(message)
        
        if machinegun.entry_location is None:
            result = S_ADD_ENTRY
        elif machinegun.location is None:
            result = S_ADD_NEST
        else:
            result = None
            if machinegun not in protocol.machineguns:
                machinegun.active = True
                protocol.machineguns.append(machinegun)
                result = S_ACTIVE.format(number = len(protocol.machineguns) - 1)
                player.editing_machinegun = None
    elif mode == 'cancel':
        result = S_EDIT_CANCEL.format(label = machinegun.label)
        if machinegun not in protocol.machineguns:
            machinegun.release()
        player.editing_machinegun = None
    elif mode == 'angles':
        result = S_ANGLES_USAGE
        if len(args) == 4:
            result = S_ANGLES
            machinegun.horizontal_fov, machinegun.up_fov, machinegun.down_fov = (
                float(args[1]), float(args[2]), float(args[3]))
            machinegun.precalc_angles()
        result = result.format(h_fov = machinegun.horizontal_fov,
            up_fov = machinegun.up_fov, down_fov = machinegun.down_fov)
    return result or usage

add(machinegun_tools)

class Machinegun():
    protocol = None
    label = None
    entry_location = None
    location = None
    rapid_loop = None
    repositioning_loop = None
    active = None
    player = None
    team = None
    forward = None
    horizontal_fov = None
    up_fov = None
    down_fov = None
    min_angle_cos = None
    min_angle_sin = None
    max_angle_sin = None
    player_orientation = None
    reenable_rapid_hack_detect = None
    restore_weapon = None
    last_usage = None
    seconds_active = 0
    rounds_fired = 0
    kills = 0
    deaths = 0
    
    def __init__(self, protocol, label, team, entry_location = None,
        location = None, horizontal_fov = 60.0, up_fov = 25.0, down_fov = 45.0):
        self.protocol = protocol
        self.label = label
        self.entry_location = entry_location
        self.location = location
        self.active = True
        self.team = team
        facing_right = team.id == 0
        self.forward = Vertex3(1.0 if facing_right else -1.0, 0.0, 0.0)
        self.player_orientation = Vertex3()
        self.horizontal_fov = horizontal_fov
        self.up_fov = up_fov
        self.down_fov = down_fov
        self.precalc_angles()
        self.rapid_loop = LoopingCall(self.rapid_cycle)
        self.repositioning_loop = LoopingCall(self.repositioning_cycle)
    
    def precalc_angles(self):
        self.min_angle_cos = cos(radians(self.horizontal_fov))
        self.min_angle_sin = -sin(radians(self.up_fov))
        self.max_angle_sin = sin(radians(self.down_fov))
    
    def player_in_action_range(self, player):
        pos = player.world_object.position
        x, y, z = self.entry_location
        return collision_3d(pos.x, pos.y, pos.z, x, y, z, distance = 2)
    
    def actionable(self, player):
        if not self.player_in_action_range(player):
            return False
        if self.team is not player.team:
            return False
        return True
    
    def action(self, player):
        if (player.world_object is None or player.hp <= 0 or player.machinegun or
            not self.player_in_action_range(player)):
            return
        if not self.active:
            return # S_NOT_WORKING
        if self.team is not player.team:
            return S_BELONGS_TO_TEAM.format(team = self.team.name)
        if player.hp < 100 and REQUIRES_FULL_HP:
            return S_HP_REQ_NOT_MET
        if self.player:
            return S_IN_USE_BY.format(player = self.player.name)
        
        self.player = player
        player.machinegun = self
        if player.weapon != SMG_WEAPON:
            self.restore_weapon = player.weapon
            player.set_weapon(SMG_WEAPON, no_kill = True)
        player.weapon_object.delay = SMG_RAPID_INTERVAL
        self.reenable_rapid_hack_detect = player.rapid_hack_detect
        player.rapid_hack_detect = False
        player.world_object.set_walk(False, False, False, False)
        player.world_object.set_animation(False, False, False, False)
        player.freeze_animation = True
        player.filter_animation_data = True
        self.repositioning_loop.start(REPOSITION_FREQUENCY, now = False)
        self.reset_player(local = False)
        self.last_usage = seconds()
    
    def reset(self):
        if self.rapid_loop.running:
            self.rapid_loop.stop()
        if self.repositioning_loop.running:
            self.repositioning_loop.stop()
        if self.player:
            self.seconds_active += seconds() - self.last_usage
            self.player.machinegun = None
        self.player = None
        self.restore_weapon = None
        self.last_usage = None
    
    def release(self):
        if self.player:
            self.eject_player(no_respawn = True)
        else:
            self.reset()
        self.rapid_loop = None
        self.repositioning_loop = None
    
    def reset_player(self, local = True):
        player = self.player
        weapon = player.weapon_object
        was_shooting = weapon.shoot
        weapon.reset()
        if was_shooting:
            weapon.set_shoot(True)
        old_hp = player.hp
        self.rounds_fired += weapon.ammo - weapon.current_ammo
        player.refill(local = True)
        player.tool = WEAPON_TOOL
        x, y, z = self.location
        create_player.x = x
        create_player.y = y
        create_player.z = z
        create_player.weapon = player.weapon
        create_player.player_id = player.player_id
        create_player.name = player.name
        create_player.team = player.team.id
        if local:
            player.send_contained(create_player)
        else:
            player.protocol.send_contained(create_player, save = True)
        player.resend_hp(old_hp)
    
    def eject_player(self, no_respawn = False):
        player = self.player
        player.rapid_hack_detect = self.reenable_rapid_hack_detect
        weapon = player.weapon_object
        self.rounds_fired += weapon.ammo - weapon.current_ammo
        if self.restore_weapon is not None:
            player.set_weapon(self.restore_weapon, no_kill = True)
        else:
            weapon.reset()
            weapon.delay = SMG.delay
        player.freeze_animation = False
        player.filter_animation_data = False
        if player.hp > 0 and not no_respawn:
            old_hp = player.hp
            player.spawn(self.entry_location)
            player.resend_hp(old_hp)
        self.reset()
    
    def get_time_active(self):
        elapsed = self.seconds_active
        if self.last_usage:
            elapsed += seconds() - self.last_usage
        return timedelta(seconds = int(elapsed))
    
    def on_orientation_update(self, x, y, z):
        temp = self.player_orientation
        temp.set(x, y, 0.0)
        temp.normalize()
        dot = temp.dot(self.forward)
        if (dot < self.min_angle_cos or
            z < self.min_angle_sin or z > self.max_angle_sin):
            self.reset_player()
            return self.forward.get()
    
    def on_shoot_set(self, fire):
        if (fire and self.player.tool == WEAPON_TOOL and
            not self.rapid_loop.running):
            self.rapid_loop.start(SMG_RAPID_INTERVAL, now = False)
    
    def resend_tool(self):
        set_tool.player_id = self.player.player_id
        set_tool.value = self.player.tool
        self.protocol.send_contained(set_tool)
    
    def rapid_cycle(self):
        player = self.player
        weapon = player.weapon_object
        if weapon is None:
            self.reset()
        elif not weapon.shoot:
            self.rapid_loop.stop()
        else:
            self.resend_tool()
            current_ammo = weapon.get_ammo()
            if current_ammo < 5:
                self.rounds_fired += weapon.ammo - current_ammo
                weapon.reset()
                weapon_reload.player_id = player.player_id
                weapon_reload.clip_ammo = weapon.current_ammo
                weapon_reload.reserve_ammo = weapon.current_stock
                weapon.set_shoot(True)
                player.send_contained(weapon_reload)
    
    def repositioning_cycle(self):
        if self.player.world_object is None:
            self.reset()
        # not using set_location to avoid touching the object's position
        x, y, z = self.location
        position_data.x = x
        position_data.y = y
        position_data.z = z
        self.player.send_contained(position_data)
    
    def serialize(self):
        return {
            'label' : self.label,
            'team_id' : self.team.id,
            'entry_location' : self.entry_location,
            'location' : self.location,
            'horizontal_fov' : self.horizontal_fov,
            'up_fov' : self.up_fov,
            'down_fov' : self.down_fov
        }

def apply_script(protocol, connection, config):
    class MachinegunConnection(connection):
        machinegun = None
        editing_machinegun = None
        last_machinegun_message = None
        
        def on_disconnect(self):
            if self.machinegun:
                self.machinegun.reset()
            self.machinegun = None
            connection.on_disconnect(self)
        
        def on_reset(self):
            self.editing_machinegun = None
            connection.on_reset(self)
        
        def on_kill(self, killer, type, grenade):
            if (killer and killer.machinegun and
                (type == WEAPON_KILL or type == HEADSHOT_KILL)):
                killer.machinegun.kills += 1
            if self.machinegun:
                self.machinegun.deaths += 1
                self.machinegun.eject_player(no_respawn = True)
            return connection.on_kill(self, killer, type, grenade)
        
        def on_hit(self, hit_amount, hit_player, type, grenade):
            returned = connection.on_hit(self, hit_amount, hit_player, type,
                grenade)
            if (self.machinegun and returned != False and
                (type == WEAPON_KILL or type == HEADSHOT_KILL)):
                hit_amount = returned or hit_amount
                return hit_amount * DAMAGE_MULTIPLIER
            return returned
        
        def on_grenade(self, time_left):
            if self.machinegun:
                return False
            connection.on_grenade(self, time_left)
        
        def on_spawn(self, pos):
            if self.machinegun:
                # happens only when the game ends
                self.machinegun.eject_player(no_respawn = True)
            connection.on_spawn(self, pos)
        
        def on_block_build_attempt(self, x, y, z):
            if self.machinegun:
                return False
            return connection.on_block_build_attempt(self, x, y, z)
        
        def on_block_destroy(self, x, y, z, mode):
            if self.machinegun:
                if self.tool != WEAPON_TOOL or mode != DESTROY_BLOCK:
                    return False
            return connection.on_block_destroy(self, x, y, z, mode)
        
        def on_position_update(self):
            # send jump action tip when you're near one
            if self.protocol.machineguns and not self.machinegun and self.hp > 0:
                last_message = self.last_machinegun_message
                available = last_message is None or seconds() - last_message > 10.0
                if (available and any(mg.actionable(self) for mg in
                    self.protocol.machineguns)):
                    self.send_chat(S_JUMP_TO_USE)
                    self.last_machinegun_message = seconds()
            connection.on_position_update(self)
        
        def on_orientation_update(self, x, y, z):
            if self.machinegun:
                returned = self.machinegun.on_orientation_update(x, y, z)
                if returned is not None:
                    return returned
            return connection.on_orientation_update(self, x, y, z)
        
        def on_animation_update(self, jump, crouch, sneak, sprint):
            if self.machinegun and (jump or crouch):
                self.machinegun.eject_player()
            elif self.protocol.machineguns and jump:
                result = None
                for machinegun in self.protocol.machineguns:
                    returned = machinegun.action(self)
                    result = ((result if machinegun.team is not self.team
                        else None) or returned)
                if not self.machinegun and result:
                    self.send_chat(result)
            return connection.on_animation_update(self, jump, crouch, sneak,
                sprint)
        
        def on_shoot_set(self, fire):
            if self.machinegun:
                self.machinegun.on_shoot_set(fire)
            connection.on_shoot_set(self, fire)
        
        def resend_hp(self, hp):
            if hp != 100:
                set_hp.hp = hp
                set_hp.not_fall = 0
                set_hp.source_x = 0
                set_hp.source_y = 0
                set_hp.source_z = 0
                self.send_contained(set_hp)
                self.hp = hp
    
    class MachinegunProtocol(protocol):
        machineguns = None
        
        def on_map_change(self, map):
            self.machineguns = []
            self.load_machinegun_json()
            protocol.on_map_change(self, map)
        
        def on_map_leave(self):
            for machinegun in self.machineguns:
                machinegun.release()
            self.machineguns = None
            protocol.on_map_leave(self)
        
        def get_machinegun_json_path(self):
            filename = self.map_info.rot_info.full_name + '_machinegun.txt'
            return os.path.join(DEFAULT_LOAD_DIR, filename)
        
        def load_machinegun_json(self):
            path = self.get_machinegun_json_path()
            if not os.path.isfile(path):
                return
            with open(path, 'r') as file:
                data = json.load(file)
            for entry in data:
                label = entry['label']
                team = self.teams[entry['team_id']]
                entry_location = tuple(entry['entry_location'])
                location = tuple(entry['location'])
                horizontal_fov = entry['horizontal_fov']
                up_fov = entry['up_fov']
                down_fov = entry['down_fov']
                machinegun = Machinegun(self, label, team, entry_location,
                    location, horizontal_fov, up_fov, down_fov)
                self.machineguns.append(machinegun)
        
        def dump_machinegun_json(self):
            if not self.machineguns:
                return
            data = [machinegun.serialize() for machinegun in self.machineguns]
            path = self.get_machinegun_json_path()
            with open(path, 'w') as file:
                json.dump(data, file, indent = 4)
    
    return MachinegunProtocol, MachinegunConnection