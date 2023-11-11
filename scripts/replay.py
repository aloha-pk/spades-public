# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

'''
Codeauthors: VierEck., DryByte (https://github.com/DryByte), modified by FerrariFlunker

More info about the script: https://aloha.pk/t/script-replay-py-server-side-gameplay-recorder-for-pique/23128

Original aos_replay by BR: (https://github.com/BR-/aos_replay)

Recordings resulting from this script are compatible with BR's playback.py

Record gameplay from your server. 

Commands:
/replay <on> <optional: custom filename> <optional: recording length in seconds> <optional: recorded ups>
	turns on a new recording. optionally specify a filename, recording length and/or recorded ups. 
/replay <off>
	turns off current recording.
/replay <ups> <value>
	set the recorded ups to the value during an active recording
You can use /rpy instead of /replay

config.toml copypaste template:
[replay]
autorecording = false #change this to true if u always want to record
auto_minimum_players_required = 2 #how many players required to justify auto start recording
command_minimum_players_required = 1 #how many players required to justify command start recording
recorded_ups = 20
minimum_recorded_ups = 10
maximum_recorded_ups = 60 #set this to 0 if u dont want to cap recorded ups
minimum_recording_length = 30
maximum_recording_length = 3600 #=1hour (in seconds). set this to 0 if u dont want to cap recording length
auto_minimum_length_to_save = 300 #=5minutues (in seconds). set this to 0 if u want to keep short demos
file_name = "rpy_{server}_{time}_{map}"
compress_with_gzip = false
auto_delete_after_time = 604800 #=1week (in seconds). set this to 0 if u want to keep old recordings. 
replay_help = [
  "/rpy ups <recorded ups>",
  "/rpy off",
  "/rpy on <*filename> <*recording length> <*recorded ups>",
  "* -> optional",
  "use these commands:",
]
'''

from piqueserver.commands import command
from pyspades import contained as loaders
from piqueserver.config import config
from pyspades.bytes import ByteWriter
import struct
from time import time, strftime
from datetime import datetime
import os.path
import enet
from pyspades.mapgenerator import ProgressiveMapGenerator
from typing import Optional
from pyspades.constants import CTF_MODE, TC_MODE
from pyspades.common import make_color
import asyncio
from twisted.logger import Logger

log = Logger()

replay_help_default = [
  "/rpy ups <recorded ups>",
  "/rpy off",
  "/rpy on <*filename> <*recording length> <*recorded ups>",
  "* -> optional",
  "use these commands:",
]

replay_config = config.section('replay')
auto_replay = replay_config.option('autorecording', False).get()
rec_ups = replay_config.option('recorded_ups', 20).get()
file_name = replay_config.option('file_name', default='rpy_{server}_{time}_{map}').get()
min_rec_ups = replay_config.option('minimum_recorded_ups', 10).get()
max_rec_ups = replay_config.option('maximum_recorded_ups', 60).get()
min_length = replay_config.option('minimum_recording_length', 30).get()
max_length = replay_config.option('maximum_recording_length', 3600).get()
replay_help = replay_config.option('replay_help', default=replay_help_default).get()
gzip_compress = replay_config.option('compress_with_gzip', True).get()
auto_delete_time = replay_config.option('auto_delete_after_time', 604800).get()
auto_min_players = replay_config.option('auto_minimum_players_required', 2).get()
command_min_players = replay_config.option('command_minimum_players_required', 1).get()
auto_min_length_save = replay_config.option('auto_minimum_length_to_save', 300).get()

if gzip_compress:
	import gzip

FILE_VERSION = 1
version = 3

def get_replays_dir():
	return (os.path.join(config.config_dir, 'replays'))
	
only_once = []
def do_subvalue(self, value):
	submsg = 'invalid'
	if 1 not in only_once and value[:3].lower() == 'ups' and value[3:].isdigit():
		if (min_rec_ups <= int(value[3:]) <= max_rec_ups) or (min_rec_ups <= int(value[3:]) and max_rec_ups == 0):
			self.record_ups = int(value[3:])
			submsg = '. %.f ups' % self.record_ups
			only_once.append(1)
	elif 2 not in only_once and value.isdigit():
		if (min_length <= int(value) <= max_length) or (min_length <= int(value) and max_length == 0):
			self.record_length = int(value)
			submsg = '. %.f seconds' % self.record_length
			only_once.append(2)
	elif 3 not in only_once and not value.isdigit() and not value[:3].lower() == 'ups':
		self.custom_file_name = value
		submsg = '. filename: %s' % value
		only_once.append(3)
	return submsg

@command('replay', 'rpy', admin_only=True)
def replay(connection, value, subvalue_one=None, subvalue_two=None, subvalue_three=None):
	c = connection
	p = c.protocol
	value = value.lower()
	msg = 'Invalid value. for more info type: /rpy help' # we want explicit command use. 
	if value == 'help':
		c.send_replay_help()
		return
	elif value == 'on':
		msg = 'Recording is already ON'
		if not p.recording:
			msg = 'Not enough players'
			if len(p.connections) >= command_min_players:
				msg = 'Demo recording turned ON'
				if subvalue_one is not None:
					msg += do_subvalue(p, subvalue_one)
					if subvalue_two is not None:
						msg += do_subvalue(p, subvalue_two)
						if subvalue_three is not None:
							msg += do_subvalue(p, subvalue_three)
				if 'invalid' in msg:
					msg = 'Invalid value. For more info type: /rpy help'
				else:
					p.start_recording()
				only_once.clear()
	elif value == 'off':
		msg = 'Recording is already OFF'
		if p.recording:
			p.end_recording()
			msg = 'Cemo recording turned OFF'
	elif value == 'ups':
		msg = 'Invalid UPS value'
		subvalue = subvalue_one
		if subvalue is not None and subvalue.isdigit() and p.recording:
			if (min_rec_ups <= int(subvalue) <= max_rec_ups) or (min_rec_ups <= int(subvalue) and max_rec_ups == 0):
				p.record_ups = int(subvalue)
				msg = 'Recorded UPS is set to %.f' % p.record_ups
	if connection.name is not None:
		msg += '. %s' % connection.name
	p.irc_say(msg)
	return msg

def apply_script(protocol, connection, config):
	class ReplayConnection(connection):
		def on_disconnect(self):
			if len(self.protocol.connections) <= auto_min_players and self.protocol.recording:
				self.protocol.end_recording()
				self.protocol.irc_say('* Demo turned OFF. Not enough players')
				log.info('Demo turned OFF. Not enough players')
			return connection.on_disconnect(self)
		
		def _connection_ack(self):
			if self.protocol.recorder_id != 33 and len(self.protocol.connections)>31:
				self.protocol.change_recorder_id()

			return connection._connection_ack(self)

		def on_join(self):
			if auto_replay and len(self.protocol.connections) >= auto_min_players and not self.protocol.recording:
				self.protocol.start_recording()
				self.protocol.is_auto = True
				self.protocol.irc_say('* Demo turned ON. There are enough players now')
				log.info('Demo turned ON. There are enough players now')
			return connection.on_join(self)
			
		def send_replay_help(self):
			for lines in replay_help:
				self.send_chat(lines)
			  
	class ReplayProtocol(protocol):
		recording = False
		write_broadcast = False
		record_length = None
		record_loop_task = None
		last_mapdata_written = time()
		last_length_check = time()
		record_ups = rec_ups
		saved_packets = None
		custom_file_name = None
		recorder_id = 33
		is_auto = False

		async def record_loop(self):
			while True:
				if self.recording:
					if self.mapdata is not None:
						if time() - self.last_mapdata_written >= 1/4: 
							self.write_map()
							self.last_mapdata_written = time()
					if self.record_length is not None:
						if time() - self.last_length_check >= 1:
							if self.record_length <= (time() - self.start_time):
								self.irc_say('* Demo turned OFF after %.f seconds' % self.record_length)
								log.info('Demo turned OFF after %.f seconds' % self.record_length)
								self.end_recording()
							self.last_length_check = time()
					else:
						if max_length != 0:
							if time() - self.last_length_check >= 1:
								if max_length <= (time() - self.start_time):
									self.end_recording()
									self.irc_say('* Demo ended. Maximum length has been reached')
									log.info('Demo ended. Maximum length has been reached')
									if auto_replay:
										self.start_recording()
										self.is_auto = True
										self.irc_say('* Demo restarted. Autorecording after maximum length reach')
										log.info('Demo restarted. Autorecording after maximum length reach')
								self.last_length_check = time()
					if self.write_broadcast:
						self.write_ups()
				await asyncio.sleep(1/self.record_ups)
		
		def on_map_change(self, map_):
			if auto_replay and len(self.connections) >= auto_min_players and not self.recording: 
				self.start_recording()
				is_auto = True
				self.irc_say('* Demo turned ON. There are enough players on map start')
				log.info('Demo turned ON. There are enough players on map start')
			return protocol.on_map_change(self, map_)
		
		def on_map_leave(self):
			if self.recording:
				self.end_recording()
				self.delete_old_demos()
				self.irc_say('* Demo turned OFF. Map ended')
				log.info('Demo turned OFF. Map ended')
			return protocol.on_map_leave(self)
		
		def create_demo_file(self):
			if not os.path.exists(get_replays_dir()):
				os.mkdir(os.path.join(get_replays_dir()))
			fn = file_name
			if '{server}' in fn:
				fn = fn.replace('{server}', self.name)
			if '{map}' in fn:
				fn = fn.replace('{map}', self.map_info.rot_info.name)
			if '{time}' in fn:
				fn = fn.replace('{time}', datetime.now().strftime('%Y-%m-%d_%H-%M-%S_'))
			if self.custom_file_name is not None:
				fn = self.custom_file_name
				self.custom_file_name = None
			fn += '.demo'
			if gzip_compress:
				fn += '.gz'
			self.replayfile = os.path.join(get_replays_dir(), fn)
		
		def delete_old_demos(self):
			if auto_delete_time == 0:
				return
			for f in os.listdir(get_replays_dir()):
				if '.demo' in f:
					if os.stat(os.path.join(get_replays_dir(), f)).st_mtime < time() - auto_delete_time:
						os.remove(os.path.join(get_replays_dir(), f))
			
		def auto_delete_if_too_small(self):
			if auto_min_length_save == 0 or not self.is_auto:
				return
			if auto_min_length_save > (time() - self.start_time):
				os.remove(self.replayfile)
				self.irc_say('* Demo deleted. Too short')
				log.info('Demo deleted. Too short')
					
		def start_recording(self):
			if self.recording:
				return
			self.create_demo_file()
			if gzip_compress:
				self.replay_file = gzip.open(self.replayfile, 'wb')
			else:
				self.replay_file = open(self.replayfile, 'wb')
			self.replay_file.write(struct.pack('BB', FILE_VERSION, version))
			self.start_time = time()
			self.record_loop_task = asyncio.ensure_future(self.record_loop())
			self.write_state()
			self.write_map(ProgressiveMapGenerator(self.map))
			self.recording = True
		
		def end_recording(self):
			if not self.recording:
				return
			self.record_loop_task.cancel()
			self.record_loop_task = None
			self.record_ups = rec_ups
			self.write_broadcast = False
			self.recording = False
			self.replay_file.close()
			self.record_length = None
			self.auto_delete_if_too_small()
			self.is_auto = False
			if self.recorder_id < 32:    
				self.player_ids.put_back(self.recorder_id)
		
		def write_pack(self, contained):
			data = ByteWriter()
			contained.write(data)
			data = bytes(data)
			self.replay_file.write(struct.pack('fH', time() - self.start_time, len(data)))
			self.replay_file.write(data)
		
		def broadcast_contained(self, contained, unsequenced=False, sender=None, team=None, save=False, rule=None):
			if self.write_broadcast and contained.id != 2:
				self.write_pack(contained)
			if self.saved_packets is not None and save:
				self.saved_packets.append(contained)
			return protocol.broadcast_contained(self, contained, unsequenced, sender, team, save, rule)
			
		def write_ups(self):
			if not len(self.players):
				return
			items = []
			highest_player_id = max(self.players)
			for i in range(highest_player_id + 1):
				position = orientation = None
				try:
					player = self.players[i]
					if (not player.filter_visibility_data and
							not player.team.spectator):
						world_object = player.world_object
						position = world_object.position.get()
						orientation = world_object.orientation.get()
				except (KeyError, TypeError, AttributeError):
					pass
				if position is None:
					position = (0.0, 0.0, 0.0)
					orientation = (0.0, 0.0, 0.0)
				items.append((position, orientation))
			world_update = loaders.WorldUpdate()
			world_update.items = items[:highest_player_id+1]
			self.write_pack(world_update)
				
		def write_map(self, data: Optional[ProgressiveMapGenerator] = None) -> None:
			if data is not None:
				self.mapdata = data
				map_start = loaders.MapStart()
				map_start.size = data.get_size()
				self.write_pack(map_start)
			elif self.mapdata is None:
				return
			if not self.mapdata.data_left():
				self.mapdata = None
				for saved_contained in self.saved_packets:
					self.write_pack(saved_contained)
				self.saved_packets = None
				self.write_broadcast = True
				self.sig_vier()
				return
			for _ in range(10):
				if not self.mapdata.data_left():
					break
				mapdata = loaders.MapChunk()
				mapdata.data = self.mapdata.read(8192)
				self.write_pack(mapdata)
		
		def write_state(self):
			self.saved_packets = []
			for player in self.players.values():
				if player.name is None:
					continue
				existing_player = loaders.ExistingPlayer()
				existing_player.name = player.name
				existing_player.player_id = player.player_id
				existing_player.tool = player.tool or 0
				existing_player.weapon = player.weapon
				existing_player.kills = player.kills
				existing_player.team = player.team.id
				existing_player.color = make_color(*player.color)
				self.saved_packets.append(existing_player)
			
			# reserve a player id and change it later
			if len(self.connections) > 31:
				self.recorder_id = 33
			else:
				self.recorder_id = self.player_ids.pop()
			
			blue = self.blue_team
			green = self.green_team
	
			state_data = loaders.StateData()
			state_data.player_id = self.recorder_id
			state_data.fog_color = self.fog_color
			state_data.team1_color = blue.color
			state_data.team1_name = blue.name
			state_data.team2_color = green.color
			state_data.team2_name = green.name
	
			game_mode = self.game_mode
	
			if game_mode == CTF_MODE:
				blue_base = blue.base
				blue_flag = blue.flag
				green_base = green.base
				green_flag = green.flag
				ctf_data = loaders.CTFState()
				ctf_data.cap_limit = self.max_score
				ctf_data.team1_score = blue.score
				ctf_data.team2_score = green.score
	
				ctf_data.team1_base_x = blue_base.x
				ctf_data.team1_base_y = blue_base.y
				ctf_data.team1_base_z = blue_base.z
	
				ctf_data.team2_base_x = green_base.x
				ctf_data.team2_base_y = green_base.y
				ctf_data.team2_base_z = green_base.z
	
				if green_flag.player is None:
					ctf_data.team1_has_intel = 0
					ctf_data.team2_flag_x = green_flag.x
					ctf_data.team2_flag_y = green_flag.y
					ctf_data.team2_flag_z = green_flag.z
				else:
					ctf_data.team1_has_intel = 1
					ctf_data.team2_carrier = green_flag.player.player_id
	
				if blue_flag.player is None:
					ctf_data.team2_has_intel = 0
					ctf_data.team1_flag_x = blue_flag.x
					ctf_data.team1_flag_y = blue_flag.y
					ctf_data.team1_flag_z = blue_flag.z
				else:
					ctf_data.team2_has_intel = 1
					ctf_data.team1_carrier = blue_flag.player.player_id
	
				state_data.state = ctf_data
	
			elif game_mode == TC_MODE:
				tc_data = loaders.TCState()
				tc_data.set_entities(self.entities)
				state_data.state = tc_data
			
			self.saved_packets.append(state_data)
			
		def sig_vier(self): # yes i just had to do this lol
			chat_message = loaders.ChatMessage()
			chat_message.chat_type = 2
			chat_message.player_id = 33
			chat_message.value = 'Recorded with replay.py by VierEck.'
			self.write_pack(chat_message)

		def change_recorder_id(self):
			if self.recorder_id == 33:
				return

			chat_message = loaders.ChatMessage()
			chat_message.chat_type = 2
			chat_message.player_id = 33
			chat_message.value = 'Your ID is going to change to 33, if your client doesnt support it please use https://github.com/VierEck/openspades'
			self.write_pack(chat_message)

			self.player_ids.put_back(self.recorder_id)
			self.write_state()
			self.write_map(ProgressiveMapGenerator(self.map))

	
	return ReplayProtocol, ReplayConnection