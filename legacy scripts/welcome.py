# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Greets specified people entering with messages

Maintainer: mat^2
"""

def apply_script(protocol, connection, config):
    welcomes = config.get('welcomes', {})
    class EnterConnection(connection):
        def on_login(self, name):
            if name in welcomes:
                self.protocol.send_chat(welcomes[name])
            connection.on_login(self, name)
    return protocol, EnterConnection