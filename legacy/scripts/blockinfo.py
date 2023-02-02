# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
A tool for identifying griefers.

Maintainer: hompy

Edited: 5:41 AM 12/16/2017 UTC, by MuffinTastic
"""

from twisted.internet.reactor import seconds
from pyspades.collision import distance_3d_vector
from pyspades.common import prettify_timespan
from commands import add, admin, name, get_player, alias

# "blockinfo" must be AFTER "votekick" in the config.txt script list
GRIEFCHECK_ON_VOTEKICK = True
IRC_ONLY = True

@name('griefcheck')
@alias('gc')
def grief_check(connection, player, time = None):
	player = get_player(connection.protocol, player)
	protocol = connection.protocol
	color = connection not in protocol.players and connection.colors
	minutes = float(time or 2)
	team_blocks = 0
	enemy_blocks = 0
	map_blocks = 0
	own_blocks = 0
	if minutes < 0.0:
		raise ValueError()
	time = seconds() - minutes * 60.0
	blocks_removed = player.blocks_removed or []
	blocks = [b[1] for b in blocks_removed if b[0] >= time]
	team_id = player.team.id
	for info in blocks:
		if info:
			name,team=info
			if name != player.name and team == team_id:
				team_blocks+=1
			elif name == player.name:
				own_blocks +=1
			elif team != team_id:
				enemy_blocks +=1
		else:
			map_blocks+=1
	player_name = player.name
	if color:
		player_name = (('\x0303' if player.team.id else '\x0302') +
			player_name + '\x0f')
	if len(blocks) == 0:
		message = 'No blocks removed in the last '
	else:
		message = '%s removed %s blocks: %s Team, %s Enemy, %s Own and %s Map in the last ' % (player_name,len(blocks),team_blocks,enemy_blocks, own_blocks, map_blocks)
	if minutes == 1.0:
		minutes_s = 'minute'
	else:
		minutes_s = '%s minutes' % ('%f' % minutes).rstrip('0').rstrip('.')
	message += minutes_s + '.'
	if len(blocks):
		infos = set(blocks)
		infos.discard(None)
		if color:
			names = [('\x0303' if team else '\x0302') + name for name, team in
				infos]
		else:
			names = set([name for name, team in infos])
		if len(names) > 0:
			message += (' Some of them were placed by ' +
				('\x0f, ' if color else ', ').join(names))
			message += '\x0f.' if color else '.'
		else:
			message += ' All of them were map blocks.'
		last = blocks_removed[-1]
		time_s = prettify_timespan(seconds() - last[0], get_seconds = True)
		message += ' Last one was destroyed %s ago' % time_s
		whom = last[1]
		if whom is None and len(names) > 0:
			message += ', and was part of the map'
		elif whom is not None:
			name, team = whom
			if color:
				name = ('\x0303' if team else '\x0302') + name + '\x0f'
			message += ', and belonged to %s' % name
		message += '.'
	switch_sentence = False
	if player.last_switch is not None and player.last_switch >= time:
		time_s = prettify_timespan(seconds() - player.last_switch,
			get_seconds = True)
		message += ' %s joined %s team %s ago' % (player_name,
			player.team.name, time_s)
		switch_sentence = True
	teamkills = len([t for t in player.teamkill_times or [] if t >= time])
	if teamkills > 0:
		s = ', and killed' if switch_sentence else ' %s killed' % player_name
		message += s + ' %s teammates in the last %s' % (teamkills, minutes_s)
	if switch_sentence or teamkills > 0:
		message += '.'
	votekick = getattr(protocol, 'votekick', None)
	if (votekick and votekick.victim is player and
		votekick.victim.world_object and votekick.instigator.world_object):
		instigator = votekick.instigator
		tiles = int(distance_3d_vector(player.world_object.position,
			instigator.world_object.position))
		instigator_name = (('\x0303' if instigator.team.id else '\x0302') +
			instigator.name + '\x0f')
		message += (' %s is %d tiles away from %s, who started the votekick.' %
			(player_name, tiles, instigator_name))
	return message

add(grief_check)

# below is a bit of a hack; it compares raw names instead of IDs, as the block_info system only stores names and team IDs.
# using player connection instances would probably be very BAD so i have not switched it to that
# this is why i added "/might/" :/
# -muffin

@name('reversegc')
@alias('rgc')
def reverse_grief_check(connection, player, time = None):
	player = get_player(connection.protocol, player)
	protocol = connection.protocol
	minutes = float(time or 2)
	if minutes < 0.0:
		raise ValueError()
	time = seconds() - minutes * 60.0
	candidates = []
	for loop_player in protocol.players.values():
		if loop_player.blocks_removed is None:
			continue
		blocks = [b[1] for b in loop_player.blocks_removed if b[0] >= time]
		for info in blocks:
			if info:
				if info[0] == player.name:
					candidates.append(loop_player)
					break
	message = "%d player(s) /might/ have destroyed %s's blocks in the last " % (len(candidates), player.name)
	if time == 1.0:
		minutes_s = "minute"
	else:
		minutes_s = "%s minutes" % ('%f' % minutes).rstrip('0').rstrip('.')
	message += minutes_s
	if len(candidates) > 0:
		candidates_s = ", ".join(["%s #%d" % (p.name, p.player_id) for p in candidates])
		message += ":\n" + candidates_s
	return message
add(reverse_grief_check)

def apply_script(protocol, connection, config):
	has_votekick = 'votekick' in config.get('scripts', [])
	
	class BlockInfoConnection(connection):
		blocks_removed = None
		teamkill_times = None
		
		def on_reset(self):
			self.blocks_removed = None
			self.teamkill_times = None
			connection.on_reset(self)
		
		def on_block_build(self, x, y, z):
			if self.protocol.block_info is None:
				self.protocol.block_info = {}
			self.protocol.block_info[(x, y, z)] = (self.name, self.team.id)
			connection.on_block_build(self, x, y, z)
		
		def on_line_build(self, points):
			if self.protocol.block_info is None:
				self.protocol.block_info = {}
			name_team = (self.name, self.team.id)
			for point in points:
				self.protocol.block_info[point] = name_team
			connection.on_line_build(self, points)
		
		def on_block_removed(self, x, y, z):
			if self.protocol.block_info is None:
				self.protocol.block_info = {}
			if self.blocks_removed is None:
				self.blocks_removed = []
			pos = (x, y, z)
			info = (seconds(), self.protocol.block_info.pop(pos, None))
			self.blocks_removed.append(info)
			connection.on_block_removed(self, x, y, z)
		
		def on_kill(self, killer, type, grenade):
			if killer and killer.team is self.team:
				if killer.teamkill_times is None:
					killer.teamkill_times = []
				killer.teamkill_times.append(seconds())
			return connection.on_kill(self, killer, type, grenade)
	
	class BlockInfoProtocol(protocol):
		block_info = None
		
		def on_map_change(self, map):
			self.block_info = None
			protocol.on_map_change(self, map)
		
		def on_votekick_start(self, instigator, victim, reason):
			result = protocol.on_votekick_start(self, instigator, victim, reason)
			if result is None and GRIEFCHECK_ON_VOTEKICK:
				message = grief_check(instigator, victim.name)
				if IRC_ONLY:
					self.irc_say('* ' + message)
				else:
					self.send_chat(message, irc = True)
			return result
	
	return BlockInfoProtocol, BlockInfoConnection