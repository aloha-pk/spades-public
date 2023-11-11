# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

'''
Script by Rakete, modified by FerrariFlunker

Detect if a player is spamming a PM, mute them, and alert the staff.
'''

from piqueserver.commands import command, get_player
from twisted.internet.reactor import callLater

def reset_timer(self):
    self.message_count = 0
    self.timer = False

def apply_script(protocol, connection, config):
    class MuteConnection(connection):
        last_message = ""
        repeated_message_count = 0
        message_count = 0
        timer = False
        spammer = False
        
        def on_command(self, command, args):
            if command == "pm":
                try:
                    pm_recipient = get_player(self.protocol, args[0])                    
                except:
                    pm_recipient = None

                self.message_count +=1

                if self.message_count > 15:
                    self.mute = True
                    self.spammer = True
                    self.protocol.irc_say(f"{self.name} has been muted due to PM abuse targeted towards {pm_recipient}.")

                if not self.timer:
                    callLater(60, reset_timer, self)
                    self.timer = True

                if self.last_message == ' '.join(args[1:]):
                    self.repeated_message_count += 1
                else:
                    self.repeated_message_count = 0
                    
                if self.repeated_message_count > 5:
                    self.mute = True
                    self.spammer = True
                    self.protocol.irc_say(f"{self.name} has been muted due to PM abuse targeted towards {pm_recipient}.")

                if self.mute:
                    self.send_chat("You are muted"+(self.spammer)*(" due to abuse of the PM command")+". To be able to send /PM's, write us with /ADMIN")
                    return False
                
                if pm_recipient is not None:
                    self.last_message = ' '.join(args[1:])

            return connection.on_command(self, command, args)
    return protocol, MuteConnection