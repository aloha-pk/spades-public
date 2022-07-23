# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Match script, useful for public matches. Features verbose announcements
on IRC and a custom timer.

Maintainer: mat^2
"""

from twisted.internet import reactor
from twisted.internet.task import LoopingCall

import json
import commands


@commands.admin
def pm(connection, value, *arg):
    player = commands.get_player(connection.protocol, value)
    message = commands.join_arguments(arg)
    player.send_chat('PM from %s: %s' % (connection.name, message))
    return 'PM sent to %s' % player.name

commands.add(pm)

@commands.admin
@commands.name('timer')
def start_timer(connection, end):
    connection.protocol.start_record()
    return connection.protocol.start_timer(int(end) * 60)

@commands.admin
@commands.name('pause')
def pause_timer(connection):
    return connection.protocol.pause_timer()

@commands.admin
@commands.name('unpause')
def unpause_timer(connection):
    return connection.protocol.unpause_timer()

@commands.admin
@commands.name('stoptimer')
def stop_timer(connection):
    connection.protocol.stop_record()
    return connection.protocol.stop_timer()

@commands.admin
@commands.name('startrecord')
def start_record(connection):
    connection.protocol.start_record()
    return 'Recording started.'

@commands.admin
@commands.name('stoprecord')
def stop_record(connection):
    connection.protocol.stop_record()
    return 'Recording stopped.'

@commands.admin
@commands.name('saverecord')
def save_record(connection, value):
    if not connection.protocol.save_record(value):
        return 'No record file available.'
    return 'Record saved.'

commands.add(start_timer)
commands.add(pause_timer)
commands.add(unpause_timer)
commands.add(stop_timer)
commands.add(start_record)
commands.add(stop_record)
commands.add(save_record)

def apply_script(protocol, connection, config):
    class MatchConnection(connection):
        def on_chat(self, value, global_message):
            if self.protocol.match_in_progress and not self.protocol.timer_paused:
                if global_message and self.team is self.protocol.spectator_team:
                    return False
            return connection.on_chat(self, value, global_message)

        def on_flag_take(self):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            self.add_message("%s took %s's flag!" %
                (self.printable_name, self.team.other.name.lower()))
            self.protocol.add_touch(self)
            return connection.on_flag_take(self)
        
        def on_flag_drop(self):
            self.add_message("%s dropped %s's flag!" %
                (self.printable_name, self.team.other.name.lower()))
            x, y, z = self.get_location()
            if self.team.other.flag.z >= 63:
                x_offset = 3
                y_offset = 5
                z = self.protocol.map.get_z(x, y)
                if y > 256:
                    self.team.other.flag.set(x - x_offset, y - y_offset, z - 1)
                if y < 256:
                    self.team.other.flag.set(x - x_offset, y + y_offset, z - 1)
                self.team.other.flag.update()
            return connection.on_flag_drop(self)
                
        def on_flag_capture(self):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            self.add_message("%s captured %s's flag!" %
                (self.printable_name, self.team.other.name.lower()))
            self.protocol.add_capture(self)
            return connection.on_flag_capture(self)
        
        def on_kill(self, killer, type, grenade):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            if killer is None:
                killer = self
            self.add_message("%s was killed by %s!" %
                (self.printable_name, killer.printable_name))
            self.protocol.add_kill(self, killer)
            return connection.on_kill(self, killer, type, grenade)

        def on_hit(self, hit_amount, player, type, grenade):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            return connection.on_hit(self, hit_amount, player, type, grenade)

        def on_block_build_attempt(self, x, y, z):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            return connection.on_block_build_attempt(self, x, y, z)
        
        def on_line_build_attempt(self, points):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            return connection.on_line_build_attempt(self, points)

        def on_block_destroy(self, x, y, z, mode):
            if not self.protocol.match_in_progress or self.protocol.timer_paused:
                return False
            return connection.on_block_destroy(self, x, y, z, mode)

        def add_message(self, value):
            self.protocol.messages.append(value)
    
    class MatchProtocol(protocol):
        timer_left = None
        timer_paused = False
        paused_at = None
        timer_call = None
        timer_end = None
        record = None
        saved_positions = {}
        match_in_progress = False

        def __init__(self, *arg, **kw):
            protocol.__init__(self, *arg, **kw)
            self.messages = []
            self.send_message_loop = LoopingCall(self.display_messages)
            self.send_message_loop.start(3)
            
        def start_timer(self, end):
            if self.timer_end is not None:
                return 'Timer is running already.'
            self.timer_end = reactor.seconds() + end
            self.send_chat('Timer started, ending in %s minutes' % (end / 60),
                irc = True)
            self.display_timer(True)
            self.match_in_progress = True
            for p in self.players:
                player = self.players[p]
                player.spawn(player.team.get_random_location(force_land=True))

        def pause_timer(self):
            if not self.match_in_progress:
                return 'No match in progress!'
            self.timer_paused = True
            self.paused_at = reactor.seconds()
            for id in self.players:
                player = self.players[id]
                if player.team is not self.spectator_team:
                    x, y, z = player.world_object.position.get()
                    self.saved_positions[id] = (x, y, z)
            self.send_chat('Match paused')

        def unpause_timer(self):
            if not (self.match_in_progress and self.timer_paused):
                return 'No match in progress or match not currently paused!'
            self.timer_paused = False
            delay = reactor.seconds() - self.paused_at
            self.timer_end += delay
            for id in self.players:
                player = self.players[id]
                if player.team != self.spectator_team:
                    try:
                        player.set_location(self.saved_positions[id])
                    except:
                        pass
                        # player.spawn(player.team.get_random_location(force_land=True))
            self.send_chat('Match unpaused')
        
        def stop_timer(self):
            if self.timer_call is not None:
                self.timer_call.cancel()
                self.send_chat('Timer stopped.')
                self.timer_call = None
                self.timer_end = None
                self.match_in_progress = False
            else:
                return 'No timer in progress.'
        
        def display_timer(self, silent = False):
            time_left = self.timer_end - reactor.seconds()
            minutes_left = time_left / 60.0
            next_call = 60
            if not silent and not self.timer_paused:
                if time_left <= 0:
                    self.send_chat('Timer ended!', irc = True)
                    self.timer_end = None
                    self.save_record('match_{}.json'.format(reactor.seconds()))
                    self.stop_record()
                    self.match_in_progress = False
                    return
                elif minutes_left <= 1:
                    self.send_chat('%s seconds left' % int(time_left), 
                        irc = True)
                    next_call = max(1, int(time_left / 2.0))
                else:
                    self.send_chat('%s minutes left' % int(minutes_left), 
                        irc = True)
            self.timer_call = reactor.callLater(next_call, self.display_timer)
        
        def display_messages(self):
            if not self.messages:
                return
            message = self.messages.pop(0)
            self.irc_say(message)
        
        # recording
        
        def add_kill(self, player, killing_player):
            if self.record is None:
                return
            self.get_record(player.name)['deaths'] += 1
            self.get_record(killing_player.name)['kills'] += 1

        def add_touch(self, player):
            if self.record is None:
                return
            self.get_record(player.name)['touches'] += 1

        def add_capture(self, player):
            if self.record is None:
                return
            self.get_record(player.name)['captures'] += 1
        
        def get_record(self, name):
            try:
                return self.record[name]
            except KeyError:
                record = {'deaths' : 0, 'kills' : 0, 'touches' : 0, 'captures' : 0}
                self.record[name] = record
                return record
        
        def start_record(self):
            self.record = {}
        
        def stop_record(self):
            self.record = None
        
        def save_record(self, value):
            if self.record is None:
                return False
            json.dump(self.record, open(value, 'wb'))
            return True
        
    return MatchProtocol, MatchConnection
