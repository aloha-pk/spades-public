# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
localizer.py

Author: mile

Provides "connection.language" attribute based on geo IP.

"""

from piqueserver.commands import command, get_player
import pygeoip

DATABASE = pygeoip.GeoIP('./data/GeoLiteCity.dat')
FRENCH_COUNTRIES = ('fr', 'mq', 'gf', 'ht', 'ca', 'be', 'ch', 'tn')
SPANISH_COUNTRIES = ('mx', 'es', 'gt', 'ar', 'bo', 'cl', 've', 'pe', 'py', 'uy', 'ec', 'sr', 'gy', 'co', 'dr',
                     'hn', 'ni', 'sv', 'cr', 'pa', 'do')
PORTUGUESE_COUNTRIES = ('br', 'pt')
ARAB_COUNTRIES = ('il', 'dz', 'ma', 'af', 'eg', 'bh', 'iq', 'sa', 'lb')


@command()
def native(connection, *args):
    if not args:
        if connection not in connection.protocol.players:
            raise ValueError()
        return f"We believe you speak {connection.language}!"
    else:
        him = get_player(connection.protocol, ' '.join(args))
        return f"We believe {him.name} speaks {him.language}!"


def apply_script(protocol, connection, config):
    class LocalizeConnection(connection):

        def __init__(self, *args, **kwargs):
            connection.__init__(self, *args, **kwargs)
            # anglocentrism for countries unaccounted for
            self.language = 'English'
            self.localized = False

        def on_join(self):
            if not self.localized:
                country = DATABASE.country_code_by_addr(self.address[0])
                country = str(country).lower()
                if country in FRENCH_COUNTRIES:
                    self.language = 'French'
                elif country in SPANISH_COUNTRIES:
                    self.language = 'Spanish'
                elif country in PORTUGUESE_COUNTRIES:
                    self.language = 'Portuguese'
                elif country in 'dk':
                    self.language = 'Danish'
                elif country in 'se':
                    self.language = 'Swedish'
                elif country in 'no':
                    self.language = 'Norwegian'
                elif country in 'fi':
                    self.language = 'Finnish'
                elif country in 'de':
                    self.language = 'German'
                elif country in ('sr', 'nl'):
                    self.language = 'Dutch'
                elif country in 'gr':
                    self.language = 'Greek'
                elif country in 'it':
                    self.language = 'Italian'
                elif country in 'po':
                    self.language = 'Polish'
                elif country in 'ru':
                    self.language = 'Russian'
                elif country in 'sk':
                    self.language = 'Slovak'
                elif country in 'ua':
                    self.language = 'Ukrainian'
                elif country in 'in':
                    self.language = 'Hindi'
                elif country in 'kr':
                    self.language = 'Korean'
                elif country in 'kp':  # north korea
                    self.language = 'Korean, but with vpn'
                elif country in 'jp':
                    self.language = 'Japanese'
                elif country in ('cn', 'tw'):
                    self.language = 'Mandarin/Cantonese'
                elif country in ARAB_COUNTRIES:
                    self.language = 'Arab'
                elif country in 'va':  # vatican city
                    self.language = 'the Holy Tongue of God'
                self.localized = True
            return connection.on_join(self)

    return protocol, LocalizeConnection
