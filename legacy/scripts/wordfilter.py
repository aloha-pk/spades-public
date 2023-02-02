# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Filters messages sent by players
Word filters defined in config file

example config entry
    "filtered_words" : {
        "minecraft" : "AOS",
	"fuck" : "i love"
	
    },
"""
import re
from commands import add, admin, name

TELL_USER_MESSAGE_FILTERED = False
FILTER_ADMIN_MESSAGES = True

@name('addfilter')
@admin
def add_bad_word(connection, word, filter):
    connection.protocol.bad_words[word] = filter
    connection.protocol.irc_say ("* %s will now filter to %s. Added by %s" %(word, filter, connection.name))
    print ("* %s will now filter to %s. Added by %s" %(word, filter, connection.name))  
    if connection in connection.protocol.players:
        return ("%s will now filter to %s" %(word, filter))

@name('removefilter')
@admin
def remove_bad_word(connection, word):
    if word in connection.protocol.bad_words:
        del connection.protocol.bad_words[word]
        connection.protocol.irc_say ("* %s has been removed from the filter by %s" %(word, connection.name))
        print ("* %s has been removed from the filter by %s" %(word, connection.name))
        if connection in connection.protocol.players:
            return ("%s has been removed from the filter" %(word))
    else:
        return ("%s was not found in the filter list" %(word))

@name('printfilter')
@admin
def print_filter_list(connection):

    bad_word_list = []
    for word in connection.protocol.bad_words:
        bad_word_list.append("\"" + word + "\" to \"" + \
        connection.protocol.bad_words[word] + "\"")
    return ', '.join(bad_word_list)

    
@name('togglefilter')
@admin
def toggle_filter(connection):
    
    connection.protocol.filter_enabled = not connection.protocol.filter_enabled
    message = ("%s the word filter" % ['disabled', 'enabled'][
        int(connection.protocol.filter_enabled)])
        
    connection.protocol.irc_say("* %s " % connection.name + message)
    if connection in connection.protocol.players:
        return ("You " + message)

add(toggle_filter)
add(print_filter_list)
add(add_bad_word)
add(remove_bad_word)

def apply_script(protocol, connection, config):
    config_bad_words = config.get('filtered_words', {})
    def word_filter(self,value,global_message):
        original_message = value
        bad_words = self.protocol.bad_words
        for word in bad_words:
            value = re.sub(word,bad_words[word], value, re.IGNORECASE)
        
        if value != original_message:
            if TELL_USER_MESSAGE_FILTERED:
                self.send_chat("Message filtered to - %s" %(value))
            print ("* Message from %s filtered. Original message: %s" %(self.name, original_message)) 
            self.protocol.irc_say ("* Message from %s filtered. Original message: %s" %(self.name, original_message))
        return value
    
    class WordFilterConnection(connection):
        def on_chat(self, value, global_message):
            if self.protocol.filter_enabled:
                if not self.admin or FILTER_ADMIN_MESSAGES: 
                    value = word_filter(self, value, global_message)
            return connection.on_chat (self, value, global_message)
    
    class WordFilterProtocol(protocol):
        bad_words = config_bad_words
        filter_enabled = True;

    
    return WordFilterProtocol, WordFilterConnection
