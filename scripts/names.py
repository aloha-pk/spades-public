# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
License: GPL-3
Authors: Piqueserver random guys + Rakete
Purpose: Remove that votekick bug but don't kick innocents
"""
import re

I_SIMILARITY_PATTERN = re.compile(r'[il!1|]', re.I)
AE_PATTERN = re.compile(r'[ae]', re.I)
SPACE_PATTERN = re.compile(r'\s+')
#TEST

def tell_irc_about_it(self, name, other_name, originalname):
    irc_relay = self.irc_relay
    msg = f"[Anti-impersonation script] {originalname} has been modified to {name}, " \
          f"because there is a player in-game called {other_name}"
    print(msg)
    if irc_relay.factory.bot and irc_relay.factory.bot.colors:
        msg = '\x0304' + msg + '\x0f'
    irc_relay.send(msg)


def check_impersonations(players, name) -> [float, str]:  # probability, impersonated name
    joining_name = I_SIMILARITY_PATTERN.sub('%', name.lower())
    joining_name = AE_PATTERN.sub('!', joining_name)
    joining_name = SPACE_PATTERN.sub('', joining_name)
    for player in players:
        if len(joining_name) == len(SPACE_PATTERN.sub('', player.name)):
            player_name = I_SIMILARITY_PATTERN.sub('%', player.name.lower())
            player_name = AE_PATTERN.sub('!', player_name)
            player_name = SPACE_PATTERN.sub('', player_name)
            if player_name == joining_name:
                return 1.0, player.name
    return 0.0, ""


def apply_script(protocol, connection, config):
    class AntiImpersonationProtocol(protocol):
        def get_name(self, player, name):
            """
            Sanitizes `name` and modifies it so that it doesn't collide with ot$
            Returns the fixed name.
            """
            originalname = name
            name = name.replace('\n', '')
            name = name.replace('%', '')
            variants = ['#33333333333333', '#3333333333333', '#333333333333', '#33333333333', '#3333333333',
                        '#333333333', '#33333333', '#3333333', '#333333', '#33333', '#3333', '#333', '#33', '#3', '#']
            for hashes in variants:
                name = name.replace(hashes, '')
            if name == "":
                name = "Deuce"
            new_name = name
            names = [p.name.lower() for p in self.players.values()]
            i = 0
            while new_name.lower() in names:
                i += 1
                new_name = name + str(i)
            probab, othername = check_impersonations(self.players.values(), new_name)
            if probab > 0.9:
                if othername.replace("I", "%") == new_name.replace("l", "%"):
                    tell_irc_about_it(self, new_name.replace("l", "L"), othername, originalname)
                    return new_name.replace("l", "L")
                elif othername.replace("l", "%") == new_name.replace("I", "%"):
                    tell_irc_about_it(self, new_name.replace("I", "i"), othername, originalname)
                    return new_name.replace("I", "i")
                elif othername.replace("a", "q") == new_name.replace("e", "q"):
                    tell_irc_about_it(self, new_name.replace("e", "E"), othername, originalname)
                    return new_name.replace("e", "E")
                elif othername.replace("A", "q") == new_name.replace("E", "q"):
                    tell_irc_about_it(self, new_name.replace("E", "e"), othername, originalname)
                    return new_name.replace("E", "e")
                elif othername.replace("e", "q") == new_name.replace("a", "q"):
                    tell_irc_about_it(self, new_name.replace("a", "A"), othername, originalname)
                    return new_name.replace("a", "A")
                elif othername.replace("E", "q") == new_name.replace("A", "q"):
                    tell_irc_about_it(self, new_name.replace("A", "a"), othername, originalname)
                    return new_name.replace("A", "a")
                else:
                    if len(new_name) == 15:
                        new_name = new_name[:-1]
                    new_name = new_name + "1"
                    tell_irc_about_it(self, new_name, othername, originalname)
            return new_name

    return AntiImpersonationProtocol, connection
