# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Query support.
Copyright (c) 2013 learn_more
See the file license.txt or http://opensource.org/licenses/MIT for copying permission.

Allows server browsers and management tools to query the server for info.
The protocol used is the warsow version of the quake query protocol.
"""

from re import sub

STATUS_REQUEST = '\xff\xff\xff\xffgetstatus'
STATUS_REPLY = '\xff\xff\xff\xffstatusResponse'
INFO_KEYVALUE = '\\{key}\\{value}'
PLAYER_STRING = '{score} {ping} "{name}" {team}\n'


def make_valid(key: str) -> str:
    k1 = sub(r'[\\;"]', '', key)
    if len(k1) >= 64:
        return k1[:64]
    return k1


def get_team_id(id_: int) -> int:  # warsow: spec = 0, no team = 1, alpha = 2, beta = 3
    if id_ == 0:
        return 2
    elif id_ == 1:
        return 3
    return 0


def apply_script(protocol, connection, config):
    class QueryProtocol(protocol):
        def handle_query(self, challenge) -> [dict, list]:
            options = {'gamename': 'Ace of Spades', 'fs_game': 'pysnip'}
            chall = make_valid(challenge)
            if len(chall) > 0:
                options['challenge'] = chall
            options['sv_hostname'] = make_valid(self.name)
            options['version'] = make_valid(self.server_version)
            options['mapname'] = make_valid(self.map_info.name)
            options['gametype'] = make_valid(self.get_mode_name())
            options['sv_maxclients'] = self.max_players
            players = []
            for p in self.players.values():
                players.append(
                    {'score': p.kills, 'ping': p.latency, 'name': make_valid(p.name), 'team': get_team_id(p.team.id)})
            options['clients'] = len(players)
            return options, players

        def receive_callback(self, address, data):
            if data and data.startswith(STATUS_REQUEST):
                data = data[len(STATUS_REQUEST):].strip()
                options, players = self.handle_query(data)
                msg = ''
                for k in options:
                    msg += INFO_KEYVALUE.format(key=k, value=options[k])
                plr = ''
                for p in players:
                    plr += PLAYER_STRING.format(**p)
                binmsg = '\n'.join([STATUS_REPLY, msg.encode('ascii', 'ignore'), plr.encode('ascii', 'ignore')])
                self.host.socket.send(address, binmsg)
            else:
                protocol.receive_callback(self, address, data)

    return QueryProtocol, connection
