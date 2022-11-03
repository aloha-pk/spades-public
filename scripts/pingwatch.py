# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

from piqueserver.scheduler import Scheduler
from piqueserver.commands import get_player, command
import random


@command('pingwatch', 'pw')
def pingwatch(connection, *args):
    if not args and connection.pingwatcher:
        connection.pingwatcher.end(True)
    elif args:
        player = get_player(connection.protocol, ' '.join(args))
        if connection.pingwatcher:
            last_target = connection.pingwatcher.target
            connection.pingwatcher.end(True)
            if player is not last_target:
                connection.pingwatcher = PingWatcher(connection, player)
        else:
            connection.pingwatcher = PingWatcher(connection, player)


class PingWatcher:
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
        # self.votes = None  # not used?
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
            self.watcher.send_chat("{target}'s ping is {ping} ms".format(target=self.target.name, ping=ping))


def apply_script(protocol, connection, config):
    class PingWatchConnection(connection):
        pingwatcher = None

        def on_disconnect(self):
            if not self.pingwatcher:
                self.pingwatcher.end(True)
            connection.on_disconnect(self)

    return protocol, PingWatchConnection
