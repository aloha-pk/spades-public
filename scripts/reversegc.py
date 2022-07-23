# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

# this is a bit of a hack; it compares raw names instead of IDs, as the block_info system only stores names and team IDs.
# using player connection instances would probably be very BAD so i have not switched it to that
# this is why i added "/might/" :/
# -muffin

from twisted.internet.reactor import seconds
from piqueserver.commands import command, admin, get_player

@command('reversegc', 'rgc')
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

def apply_script(protocol, connection, config):
	return protocol, connection
