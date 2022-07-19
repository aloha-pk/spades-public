# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

import string
import urllib2
import datetime
import threading
from pyspades.common import *
from pyspades.constants import *
from twisted.internet import task
from pyspades import contained as loaders
from pyspades.packet import load_client_packet
from pyspades.bytes import ByteReader, ByteWriter
 
SERVER_CHAR_ID = 0x1  # Used by the DLL to check if the message is from VoxelAuth
SERVER_PLAYER_ID = 37
chat_message = loaders.ChatMessage()
 
 
def update(port):
    req = urllib2.Request('http://voxelauth.com/api/serverlist')
    req.add_data("update=" + port)
    urllib2.urlopen(req)
 
 
class LoginThread(threading.Thread):
    connection = None
    msg = None
 
    def __init__(self, connection, msg):
        self.connection = connection
        self.msg = msg
        threading.Thread.__init__(self)
 
    def run(self):
        if string.split(self.msg, " ")[0] == "/voxelauth":
            self.connection.VoxelAuthed = self.connection.CheckAuth(self.msg)
            if self.connection.VoxelAuthed:
                print "VoxelAuth: " + self.connection.VoxelName + " has logged in."
            else:
                print "VoxelAuth: %s failed to log in as %s." % (
                    self.connection.address[0], self.connection.VoxelName
                )
 
 
def apply_script(protocol, connection, config):
    updateLoop = task.LoopingCall(update, str(config.get('port', 32887)))
    updateLoop.start(7 * 60)
 
    class VoxelAuth(connection):
        VoxelAuthed = False
        VoxelName = None
        VoxelDisplay = None
        VoxelServerID = None
 
        def AuthPlayer(self, name, serverID):  # Check with server
            req = urllib2.Request('http://voxelauth.com/api/auth')
            req.add_data("username=" + name + "&serverid=" + serverID)
            resp = urllib2.urlopen(req)
            auth = resp.read()
            split = auth.split(":")
            if len(split) == 0:
                return False, None
            authed = (split[0] == "SUCCESS")
            if authed:
                authname = split[1]
            else:
                authname = None
            return authed, authname
 
        def CheckAuth(self, msg):  # Check message is for VoxelAuth
            split = string.split(msg, " ")
            if len(split) > 1 and split[0] == "/voxelauth":
                self.VoxelName = split[1]
                authed, name = self.AuthPlayer(self.VoxelName, self.VoxelServerID)
                if authed is False:
                    return False
                self.VoxelDisplay = name[:15]
                return authed
            return False
 
        def GenerateServerID(self):
            import hashlib
            hash = hashlib.md5(self.address[0])
            hash.update(datetime.datetime.now().ctime())
            return hash.hexdigest()
 
        def on_login(self, name):
            if self.VoxelDisplay is not None:
                self.name = self.VoxelDisplay
                name = self.VoxelDisplay
            if not self.VoxelAuthed:
                self.disconnect()
                return False
            return connection.on_login(self, name)
 
        def on_join(self):
            self.VoxelServerID = self.GenerateServerID()
            if self.VoxelServerID is not None:
                chat_message.player_id = SERVER_PLAYER_ID
                chat_message.chat_type = 0
                chat_message.value = chr(SERVER_CHAR_ID) + self.VoxelServerID
                self.send_contained(chat_message)
            return connection.on_join(self)
 
        def loader_received(self, loader):  # Hooks packet
            if self.VoxelAuthed or self.VoxelServerID is None:  # Already logged in or Server ID not sent
                return connection.loader_received(self, loader)
            if self.player_id is not None:
                contained = load_client_packet(ByteReader(loader.data))
                if contained.id == loaders.ChatMessage.id:
                    value = contained.value
                    thread = LoginThread(self, value)
                    thread.start()
            return connection.loader_received(self, loader)
 
    return protocol, VoxelAuth