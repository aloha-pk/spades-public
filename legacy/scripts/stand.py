# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
 LAST STAND SCRIPT V1.21 BY INFLUX
 ONE TEAM IS ASSIGNED TO DEFEND A LOCATION. THE  OTHER TEAM MUST KILL ALL THE DEFENDERS.
 ONCE THE TIME RUNS OUT OR ALL THE DEFENDERS ARE DEAD, THE ROLES ARE REVERSED. 
 THE TEAM WHICH KILLS ALL THE DEFENDERS QUICKEST WINS A POINT.

 To install, save this file (stand.py) to your pyspades/scripts folder, then open your config.txt and change the game_mode to "stand".

 DO NOT ADD TO THE SCRIPT LIST.

 For mapping, you must include several things in the 'extensions' dictionary in your map metadata.
 These are the following: 
 'attspawn': (xyz co-ordinates of the attacker's spawn)
 'defspawn': (xyz co-ordinates of the defender's spawn)
 'north': ([Optional] xyz co-ordinates of the north spawn point)*
 'east': ([Optional] xyz co-ordinates of the east spawn point)*
 'south': ([Optional] xyz co-ordinates of the south spawn point)*
 'west': ([Optional] xyz co-ordinates of the west spawn point)*
 'time_limit': ([Optional] time limit in seconds. Defaults to 300 if this is not included or left blank)

 * These are optional but there must be at least one directional spawn point otherwise you will get an error.
"""

import random
from commands import add, get_player
from pyspades.server import create_player, player_left, intel_capture
from pyspades.constants import *
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater
from commands import alias, name, add

class CustomException(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)


class DummyPlayer():
    protocol = None
    team = None
    player_id = None
   
    def __init__(self, protocol, team):
        self.protocol = protocol
        self.team = team
        self.acquire_player_id()
   
    def acquire_player_id(self):
        max_players = min(32, self.protocol.max_players)
        if len(self.protocol.connections) >= max_players:
            try:
                self.player_id = next(self.team.get_players()).player_id
            except StopIteration:
                self.player_id = None
            return self.player_id is not None
        self.player_id = self.protocol.player_ids.pop()
        self.protocol.player_ids.put_back(self.player_id)
        create_player.x = 0
        create_player.y = 0
        create_player.z = 63
        create_player.weapon = RIFLE_WEAPON
        create_player.player_id = self.player_id
        create_player.name = self.team.name
        create_player.team = self.team.id
        self.protocol.send_contained(create_player, save = True)
        return True
   
    def score(self):
        if self.protocol.game_mode != CTF_MODE:
            return
        if self.player_id in self.protocol.players:
            self.acquire_player_id()
        if self.player_id is None and not self.acquire_player_id():
            return
        winning = (self.protocol.max_score not in (0, None) and
            self.team.score + 1 >= self.protocol.max_score)
        self.team.score += 1
        intel_capture.player_id = self.player_id
        intel_capture.winning = winning
        self.protocol.send_contained(intel_capture, save = True)
        if winning:
            self.team.initialize()
            self.team.other.initialize()
            for entity in self.protocol.entities:
                entity.update()
            for player in self.protocol.players.values():
                player.hp = None
                if player.team is not None:
                    player.spawn()
            self.protocol.on_game_end()
        else:
            flag = self.team.other.set_flag()
            flag.update()
   
    def __del__(self):
        if self.player_id is None or self.player_id in self.protocol.players:
            return
        player_left.player_id = self.player_id
        self.protocol.send_contained(player_left, save = True)

@alias('n')        
def north(connection):
    lsd = connection.protocol.last_stand_dict[connection]
    if lsd['side'] == 'att':
        if connection.protocol.last_stand_start == False:
            connection.send_chat('The round has not started, you cannot spawn yet.')
        else:
            if not connection.protocol.north == None:
                if lsd['spawned']:
                    connection.send_chat('You have already spawned and must wait until you respawn to be able to again.')
                else:
                    connection.set_location_safe(connection.protocol.north)
                    connection.send_chat('You have spawned NORTH.')
                    lsd['spawned'] = True
            else:
                connection.send_chat('No north spawn exists. Try another spawn.')
    else:
        connection.send_chat('You are on the defending team and cannot select a spawn.')
        
@alias('e')        
def east(connection):
    lsd = connection.protocol.last_stand_dict[connection]
    if lsd['side'] == 'att':
        if connection.protocol.last_stand_start == False:
            connection.send_chat('The round has not started, you cannot spawn yet.')
        else:
            if not connection.protocol.east == None:
                if lsd['spawned']:
                    connection.send_chat('You have already spawned and must wait until you respawn to be able to again.')
                else:
                    connection.set_location_safe(connection.protocol.east)
                    connection.send_chat('You have spawned EAST.')
                    lsd['spawned'] = True
            else:
                connection.send_chat('No east spawn exists. Try another spawn.')
    else:
        connection.send_chat('You are on the defending team and cannot select a spawn.')

@alias('s')        
def south(connection):
    lsd = connection.protocol.last_stand_dict[connection]
    if lsd['side'] == 'att':
        if connection.protocol.last_stand_start == False:
            connection.send_chat('The round has not started, you cannot spawn yet.')
        else:
            if not connection.protocol.south == None:
                if lsd['spawned']:
                    connection.send_chat('You have already spawned and must wait until you respawn to be able to again.')
                else:
                    connection.set_location_safe(connection.protocol.south)
                    connection.send_chat('You have spawned SOUTH.')
                    lsd['spawned'] = True
            else:
                connection.send_chat('No south spawn exists. Try another spawn.')
    else:
        connection.send_chat('You are on the defending team and cannot select a spawn.')

@alias('w')        
def west(connection):
    lsd = connection.protocol.last_stand_dict[connection]
    if lsd['side'] == 'att':
        if connection.protocol.last_stand_start == False:
            connection.send_chat('The round has not started, you cannot spawn yet.')
        else:
            if not connection.protocol.west == None:
                if lsd['spawned']:
                    connection.send_chat('You have already spawned and must wait until you respawn to be able to again.')
                else:
                    connection.set_location_safe(connection.protocol.west)
                    connection.send_chat('You have spawned WEST.')
                    lsd['spawned'] = True
            else:
                connection.send_chat('No west spawn exists. Try another spawn.')
    else:
        connection.send_chat('You are on the defending team and cannot select a spawn.')

add(north)
add(east)
add(south)
add(west)

def apply_script(protocol, connection, config):

    class laststandConnection(connection):


        def attacker_force_spawn(self):
            if self.name is None or self not in self.protocol.players:
                return
            lsd = self.protocol.last_stand_dict[self]
            if lsd['side'] == 'att':
                if not lsd['spawned'] and self.protocol.last_stand_start:
                    spawnlist = self.protocol.spawnlist
                    force_spawn_pos = random.choice(spawnlist)
                    if force_spawn_pos == '/n':
                        self.set_location_safe(self.protocol.north)
                        location = 'NORTH'
                    elif force_spawn_pos == '/e':
                        self.set_location_safe(self.protocol.east)
                        location = 'EAST'
                    elif force_spawn_pos == '/s':
                        self.set_location_safe(self.protocol.south)
                        location = 'SOUTH'
                    elif force_spawn_pos == '/w':
                        self.set_location_safe(self.protocol.west)
                        location = 'WEST'
                    self.send_chat("The server has spawned you %s. Try typing '/n', '/e', '/s' or '/w' to spawn yourself next time."% location)
                    lsd['spawned'] = True


        def on_spawn(self, pos):
            lsd = self.protocol.last_stand_dict[self]
            if self.team == self.protocol.attackteam:
                self.send_chat('You are on the attacking team')
                lsd['side'] = 'att'
            else:
                self.send_chat('You are on the defending team')
                lsd['side'] = 'def'
            print lsd['late']
            if lsd['side'] == 'def':
                lsd['spawned'] = True
                if self.protocol.last_stand_start:
                    print 'START'
                    self.kill()
                    self.send_chat('You have been prevented from respawning because the round has started.')
                    self.send_chat('You will be able to join the next round.')
            elif lsd['side'] == 'att':
                if lsd['late'] and self.protocol.last_stand_start:
                    self.kill()
                    self.send_chat('You have been prevented from spawning because the round has started.')
                    self.send_chat('You will be able to join the next round.')
                else: 
                    lsd['spawned'] = False
                    if self.protocol.last_stand_start:
                        lsd['timer'] = callLater(10.0, self.attacker_force_spawn)
            return connection.on_spawn(self, pos)

        def on_kill(self, killer, type, grenade):
            lsd = self.protocol.last_stand_dict[self]
            defendalive = 0
            if lsd['side'] == 'def':
                if self.protocol.last_stand_start:
                    for player in self.protocol.defendteam.get_players():
                        if not player.world_object.dead:
                            defendalive += 1
                    defendalive -= 1
                    if defendalive > 0:
                        self.protocol.send_chat('%i players remaining on the defending team' % defendalive)
                else:
                    self.respawn_time = 0
            elif lsd['side'] == 'att':
                if not self.protocol.last_stand_start:
                    self.respawn_time = 0
                else:
                    self.respawn_time = self.protocol.respawn_time
            if lsd['timer'] != None:
                if lsd['timer'].active():
                    lsd['timer'].cancel()
                lsd['timer'] = None
            if lsd['capture']:
                lsd['capture'] = False
            return connection.on_kill(self, killer, type, grenade)

        def respawn(self):
            lsd = self.protocol.last_stand_dict[self]
            if lsd['side'] == 'def':
                if self.protocol.last_stand_start:
                    return False
            elif lsd['side'] == 'att':
                if self.protocol.last_stand_start and lsd['late']:
                    return False
                else:
                    lsd['late'] = False
            return connection.respawn(self)

        def on_position_update(self):
            playerpos = self.world_object.position
            if self.team == self.protocol.attackteam:
                if not self.protocol.last_stand_start:
                    if playerpos.x > (self.protocol.attspawn[0] + 10) or playerpos.x < (self.protocol.attspawn[0] - 10) or playerpos.y > (self.protocol.attspawn[1] + 10) or playerpos.y < (self.protocol.attspawn[1] - 10):
                        self.set_location_safe(self.protocol.attspawn)
                elif self.protocol.last_stand_start:
                    lsd = self.protocol.last_stand_dict[self]
                    if not self.world_object.dead:
                        if (self.protocol.flag_pos[0] - 10) <= playerpos.x <= (self.protocol.flag_pos[0] + 10) and (self.protocol.flag_pos[1] -10) <= playerpos.y <= (self.protocol.flag_pos[1] + 10):
                            lsd['capture'] = True
                        else:
                            lsd['capture'] = False
                    else:
                        lsd['capture'] = False
            else:
                if not self.protocol.last_stand_start:
                    if playerpos.x > (self.protocol.defspawn[0] + 10) or playerpos.x < (self.protocol.defspawn[0] - 10) or playerpos.y > (self.protocol.defspawn[1] + 10) or playerpos.y < (self.protocol.defspawn[1] - 10):
                        self.set_location_safe(self.protocol.defspawn)
            return connection.on_position_update(self)
        
        def on_join(self):
            
            self.protocol.last_stand_dict[self] = {
            'side': None,
            'spawned': None,
            'late': None,
            'timer': None,
            'capture': None,
            'switch': False
            }
            lsd = self.protocol.last_stand_dict[self]
            if self.protocol.last_stand_start:
                lsd['late'] = True
            else:
                lsd['late'] = False
            return connection.on_join(self)
        

        def on_team_join(self, team):
            lsd = self.protocol.last_stand_dict[self]
            max_players = min(32, self.protocol.max_players)
            if len(self.protocol.connections) < max_players:
                if self.protocol.defendteam.count() <= self.protocol.attackteam.count():
                    if team == self.protocol.attackteam:    
                        self.send_chat("Team is locked. Too few people on the defending side.")
                        return self.protocol.defendteam
            return connection.on_team_join(self, team)

        def on_spawn_location(self, pos):
            lsd = self.protocol.last_stand_dict[self]
            if not lsd['late']:
                if self.team == self.protocol.attackteam:
                    return self.protocol.attspawn
                else:
                    return self.protocol.defspawn
            return connection.on_spawn_location(self, pos)
        
        def on_disconnect(self):
            del self.protocol.last_stand_dict[self]
            return connection.on_disconnect(self) 


    class laststandProtocol(protocol):
        game_mode = CTF_MODE
        force_spawn = None
        attackside = None
        attackteam = None
        oldattackside = None
        defendteam = None
        north = None
        east = None
        south = None
        west = None
        last_stand_dict = {}
        last_stand_start = False
        ls_countdownlist= []
        for ls_countdown in ls_countdownlist:
            ls_countdown = None
        ls_round_timer = None
        ls_round_count = 0
        timemessage = []
        bluedefscore = 0
        greendefscore = 0
        roundtimelimit = None
        timing = None
        timevals = []
        roundgo = None
        spawnlist = []
        firstmap = True
        countdowncount = 0
        newroundwait = None
        defendersalive = None
        flag_pos = None
        capturing = False
        captured = 0


        def on_map_change(self, map):

            if self.firstmap == False:
                if self.last_stand_start:
                    if self.timing.running and not self.timing == None:
                        self.timing.stop()
                for i in xrange(0, 12, 1):
                    ls_countdown = self.ls_countdownlist[i]
                    if ls_countdown.cancelled == 0 and ls_countdown.called == 0:
                        ls_countdown.cancel()
                        ls_countdown = None
                if not self.newroundwait == None:
                    if self.newroundwait.active():
                        self.newroundwait.cancel()  
            self.attackside = None    
            self.attackteam = None
            self.oldattackside = None
            self.defendteam = None
            self.north = None
            self.east = None
            self.south = None
            self.west = None
            self.last_stand_start = False
            self.ls_round_timer = None
            self.ls_round_count = 0
            self.timemessage = None
            self.timevals = None
            self.bluedefscore = 0
            self.greendefscore = 0
            self.roundtimelimit = None
            self.timing = None
            self.roundgo = None
            self.spawnlist = []
            self.countdowncount = 0
            self.attackside = random.choice([1, 2])
            self.newroundwait = None
            self.defendersalive = None
            self.flag_pos = None
            self.capturing = False
            self.captured = 0

            if self.attackside == 1:
                self.attackteam = self.blue_team
                self.defendteam = self.green_team
            elif self.attackside == 2:
                self.attackteam = self.green_team
                self.defendteam = self.blue_team

            extensions = self.map_info.extensions
            if any([attackspawn in extensions for attackspawn in ['Attspawn', 'attspawn']]):
                self.attspawn = extensions.get(attackspawn)
            else:
                raise CustomException("Data needed for \'attspawn\' in map extensions'")

            if any([defendspawn in extensions for defendspawn in ['Defspawn', 'defspawn']]):
                self.defspawn = extensions.get(defendspawn)
            else:
                raise CustomException("Data needed for \'defspawn\' in map extensions'")

            if 'time_limit' in extensions:
                self.roundtimelimit = extensions['time_limit']
            else:
                self.roundtimelimit = 300

            if any([spawnnorth in extensions for spawnnorth in ['North', 'north']]):
                self.north = extensions[spawnnorth]
                self.spawnlist.append('/n')
            if any([spawneast in extensions for spawneast in ['East', 'east']]):
                self.east = extensions[spawneast]
                self.spawnlist.append('/e')
            if any([spawnsouth in extensions for spawnsouth in ['South', 'south']]):
                self.south = extensions[spawnsouth]
                self.spawnlist.append('/s')
            if any([spawnwest in extensions for spawnwest in ['West', 'west']]):
                self.west = extensions[spawnwest]
                self.spawnlist.append('/w')
            if all(x == None for x in [self.north, self.east, self.south, self.west]):
                raise CustomException("At least one north, south, east or west spawn is required")
            if 'flag' in extensions:
                self.flag_pos = extensions['flag']
            else:
                raise CustomException("Map extensions missing data for 'flag'.")
            self.building = False
            self.killing = False
            self.last_stand_new_round()
            return protocol.on_map_change(self, map)

        def on_flag_spawn(self, x, y, z, flag, entity_id):
            return (0, 0, 63)

        def on_base_spawn(self, x, y, z, base, entity_id):
            return (0, 0, 63)

        def last_stand_new_round(self):
            self.firstmap = False
            self.captured = 0
            if self.oldattackside == 1:
                 self.attackside = 2
            elif self.oldattackside == 2:
                 self.attackside = 1
            if self.attackside == 1:
                self.attackteam = self.blue_team
                self.defendteam = self.green_team
            elif self.attackside == 2:
                self.attackteam = self.green_team
                self.defendteam = self.blue_team
            for player in self.players.values():
                lsd = self.last_stand_dict[player]
                if lsd['late']:
                    lsd['late'] = False
                lsd['capturing'] = False
                if player.team.spectator:
                    if self.defendteam.count() >= self.attackteam.count():
                        player.set_team(self.attackteam)
                    else:
                        player.set_team(self.defendteam)
                    player.send_chat('You have been forced to join a team by the server')
                if player.team == self.attackteam:
                    player.spawn(self.attspawn)
                elif player.team == self.defendteam:
                    player.spawn(self.defspawn)
            self.last_stand_countdown_times()

        def last_stand_countdown_times(self):
            if self.countdowncount == 0:
                self.timemessage = ['60', '50', '40', '30', '20', '10', '5', '4', '3', '2', '1', 'Go!']
                self.timevals = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0]
                for i, time in zip(xrange(0, 12, 1), self.timevals):
                    self.ls_countdownlist.insert(i, reactor.callLater(time, self.last_stand_countdown))
            else:
                self.timemessage = ['20', '10', '5', '4', '3', '2', '1', 'Go!']
                self.timevals = [10.0, 20.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0]
                for i, time in zip(xrange(0, 8, 1), self.timevals):
                    self.ls_countdownlist.insert(i, reactor.callLater(time, self.last_stand_countdown))
            self.countdowncount += 1


        def last_stand_countdown(self):
            while self.defendteam.count() <= (self.attackteam.count()) and not self.attackteam.count() <= 2:
                balancelist = []
                avail = 0
                for player in self.attackteam.get_players():
                    lsd = self.last_stand_dict[player]
                    if not lsd['switch']:
                        avail += 1
                        playerbalance = balancelist.append(player)
                if avail == 0:
                    for player in self.attackteam.get_players():
                        lsd = self.last_stand_dict[player]
                        if lsd['switch']:
                            lsd['switch'] = False
                else:
                    luckywinner = random.choice(balancelist)
                    lsdlw = self.last_stand_dict[luckywinner]
                    luckywinner.respawn_time = 0
                    luckywinner.set_team(self.defendteam)
                    luckywinner.send_chat('You have been autobalanced to the defending team')
                    lsdlw['switch'] = True
            for player in self.players.values():
                if player.team.spectator:
                    if self.defendteam.count() >= self.attackteam.count() + 3:
                        player.set_team(self.attackteam)
                    else:
                        player.set_team(self.defendteam)
                    player.send_chat('You have been forced to join a team by the server')
            if self.timemessage[0] == 'Go!':
                for team in (self.green_team, self.blue_team):
                    if team.count() == 0:
                        self.send_chat('Not enough players on the %s team to begin.' % team.name)
                        self.last_stand_start = False
                        self.last_stand_countdown_times()
                        self.roundgo = False
                        return
                    else:
                        self.roundgo = True
                if self.roundgo:
                        self.send_chat(self.timemessage[0])
                        self.ls_roundstart()
            elif self.timemessage[0] in ['1', '2', '3', '4', '5']:
                self.send_chat(self.timemessage.pop(0))
            else:
                self.send_chat('%s seconds before round starts' % self.timemessage.pop(0))


        def ls_roundstart(self):
            print 'Last Stand round started'
            self.oldattackside = self.attackside
            self.last_stand_start = True   
            self.killing = True
            for player in self.players.values():
                player.refill()
            self.timing = LoopingCall(self.defenderscore)
            self.timing.start(1.0)
            availspawn = ', '.join(self.spawnlist)
            for player in self.attackteam.get_players():
                lsd = self.last_stand_dict[player]
                lsd['timer'] = callLater(10.0, player.attacker_force_spawn)
                player.send_chat('Type one of the following to spawn: %s' % availspawn)




        def defenderscore(self):
            defendercount = 0
            attackercap = 0
            if self.last_stand_start:
                for player in self.defendteam.get_players():
                    if not player == None:
                        if not player.world_object.dead:
                            defendercount += 1
                for attacker in self.attackteam.get_players():
                    lsd = self.last_stand_dict[attacker]
                    if lsd['capture']:
                        self.capturing = True
                        attackercap += 1
                        if self.captured > 0:
                            if self.captured % 10 == 0:
                                attacker.send_chat('The flag is %i%% captured' % self.captured)
                    elif attackercap == 0:
                        self.capturing = False
                if self.capturing:
                    self.captured += 5
                    if self.captured == 5:
                        self.send_chat('Attackers are capturing the flag!')
                elif not self.capturing:
                    if self.captured > 0:
                        self.captured -= 5
                        if self.captured == 5:
                            self.send_chat('Attackers are no longer capturing the flag.')
                if self.attackside == 1:
                    self.greendefscore += 1
                    if self.greendefscore == self.roundtimelimit:
                        self.send_chat ('Time limit reached!')
                        print 'Time limit reached'
                        self.timing.stop()
                        self.last_stand_start = False
                        self.ls_round_end()
                else:
                    self.bluedefscore += 1
                    if self.bluedefscore == self.roundtimelimit:
                        print 'Time limit reached'
                        self.send_chat ('Time limit reached!')
                        self.timing.stop()
                        self.last_stand_start = False
                        self.ls_round_end()
                if defendercount == 0:
                    print 'All defenders dead'
                    self.send_chat('All defenders have been killed!')
                    self.last_stand_start = False
                    self.timing.stop()
                    self.ls_round_end()
                elif self.captured == 100:
                    print 'Flag captured'
                    self.send_chat('Attackers have captured the flag!')
                    self.last_stand_start = False
                    self.timing.stop()
                    self.ls_round_end()


        def ls_round_end(self):
            print 'Last Stand round ended'
            self.roundgo = False
            self.newroundwait = callLater(5, self.last_stand_new_round)
            self.ls_round_count += 1
            if self.ls_round_count % 2 == 1:
                if self.defendteam == self.green_team:
                    self.send_chat('Green team\'s score for that round: %i' % self.greendefscore)
                elif self.defendteam == self.blue_team:
                    self.send_chat('Blue team\'s score for that round: %i' % self.bluedefscore)
            elif self.ls_round_count % 2 == 0:
                if self.greendefscore > self.bluedefscore:
                    self.send_chat('Green team wins the round with a score of %i to Blue\'s score of %i.' % (self.greendefscore, self.bluedefscore))
                    dummy = DummyPlayer(self, self.green_team)
                    dummy.score()
                    self.greendefscore = 0
                    self.bluedefscore = 0
                elif self.greendefscore < self.bluedefscore:
                    self.send_chat('Blue team wins the round with a score of %i to Green\'s score of %i.' % (self.bluedefscore, self.greendefscore))
                    dummy = DummyPlayer(self, self.blue_team)
                    dummy.score()
                    self.greendefscore = 0
                    self.bluedefscore = 0
                elif self.greendefscore == self.bluedefscore:
                    self.send_chat('Both teams scored %i and the round is tied!' % self.greendefscore)
                    self.greendefscore = 0
                    self.bluedefscore = 0



    return laststandProtocol, laststandConnection