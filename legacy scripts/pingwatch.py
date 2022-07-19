# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from twisted.internet.reactor import seconds
from scheduler import Scheduler
from commands import alias, add, get_player, join_arguments, InvalidPlayer
import random

@alias('pw')
def pingwatch(connection, value = None):
    if value is None and connection.pingwatcher is not None:
        connection.pingwatcher.end(True)
    elif value is None:
        pass
    else:
        if connection.pingwatcher is not None:
            last_target = connection.pingwatcher.target
            connection.pingwatcher.end(True)
        player = get_player(connection.protocol, value)
        if connection.pingwatcher is None:
            connection.pingwatcher = PingWatcher(connection, player)
        elif player is not last_target:
            connection.pingwatcher = PingWatcher(connection, player)
add(pingwatch)

class PingWatcher(object):
    schedule = None
    
    def __init__(self, watcher, target):
        self.watcher = watcher
        self.target = target
        self.ended = False
        
        schedule = Scheduler(watcher.protocol)
        schedule.loop_call(1.0, self.send_chat_update)
        self.schedule = schedule
    
   
    def release(self):
        self.watcher = None
        self.target = None
        self.votes = None
        if self.schedule:
            self.schedule.reset()
        self.schedule = None
        
    def end(self, watcher_disconnected=False):
        self.ended = True
        if not watcher_disconnected:
            self.watcher.send_chat("stopped watching target's ping")
        self.release()
    
    def send_chat_update(self):
        if self.target.name is None:
            self.end()
        else:
            ping = self.target.latency
            if hasattr(self.target, 'spoofed_ping') and self.target.spoofed_ping:
                ping = random.randrange(self.target.spoofed_ping_min, self.target.spoofed_ping_max)
            self.watcher.send_chat("{target}'s ping is {ping} ms".format(target = self.target.name, ping = ping))

def apply_script(protocol, connection, config):
    class PingwatchConnection(connection):
        pingwatcher = None
        
        def on_disconnect(self):
            if self.pingwatcher is not None:
                self.pingwatcher.end(True)
            connection.on_disconnect(self)

    return protocol, PingwatchConnection
