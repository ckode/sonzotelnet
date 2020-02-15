from sonzo.telnet import TelnetServer, TelnetProtocol
import logging
import time

LMAGENTA = chr(27) + "[1;35m"
WHITE    = chr(27) + "[37m"
LGREEN   = chr(27) + "[1;32m"
LOGIN    = "\n\r\n\r\n\r                             {}Welcome to Sonzo Chat!\n\r\n\r{}"


class ChatClient(TelnetProtocol):
    """
    Custom server side client object inherited from sonzo.SonzoClient.
    
    This client IS NOT an actual client side telnet client.
    """
    def _init_(self, sock, addr):
        # Overridden medthod    
#        SonzoClient.__init__(self, sock, addr)
        self.name = addr
        
    def onConnect(self):
        # Overridden medthod    
        logging.info(" {} has connected.".format(self.addrport()))

        for user in USERLIST:
            systemMessage(user, "{} has joined the chat!\n\r".format(self.addrport()))
        USERLIST.append(self)        
        systemMessage(self, LOGIN.format(LMAGENTA, WHITE))
    
    
    def onDisconnect(self):
        # Over-ridden medthod 
        logging.info(" {} disconnecting.".format(self.addrport()))     
        USERLIST.remove(self)
        for user in USERLIST:
            if user is not self:
                systemMessage(user, "{} logged off.\n\r".format(self.addrport()))

    def dataRecieved(self, data):
        """
        Overriden function.  Called when data is recieved from client.
        """
        chat(self, data)
        

    def disconnect(self):
        """
        Disconnect user.
        """
        systemMessage(self, "Goodbye!\n\r")
        self._new_messages = False
        self._connected = False


def color(c, color):
    if c._ansi:
        return color
    else:
        return ""
        

def chat(client, msg):
    #Check to see if someone issues a command.
    if msg.startswith("=a".lower()):
        client.setANSIMode()
        systemMessage(client, "ANSI: {}\n\r".format(client._ansi))
        logging.info(" {} changing ANSI to: {}.".format(client.addrport(), client._ansi))
        return
    if msg.startswith("/quit".lower()):
        client.disconnect()
        return
    if msg.startswith("~".lower()):
        logging.info(" {} changing character mode to: {}.".format(client.addrport(), client._character_mode))
        client.setCharacterMode()
        client.systemMessage("Character Mode is now: {}\n\r".format(client._character_mode))
        return
    if msg.startswith("/runlater".lower()):
        chatsrvr.callLater("Ran 2 seconds later.", func=print, runtime=2)   
    if msg.startswith("/install".lower()):
        chatsrvr.install("Fart!", func=print)
    # If no command, say it in the chat room.
    for c in USERLIST:
        sendMessage(client, c, msg)

  
def sendMessage(sender, client, message):
    message = "{}{} says, {}{}".format(color(sender, LGREEN), sender.addrport(), color(client, WHITE), message)
    client.send(message)

def systemMessage(client, message):
    client.send(message)
    
    
    
if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    USERLIST = []
    chatclient = ChatClient
    chatsrvr = TelnetServer(clientclass=chatclient, address='', port=23)
    logging.info(" Sonzo Chat Server starting up...")
    # Example of adding a looping call.
    tensecondloop = chatsrvr.loopingCall("Looping at 10 seconds", func=print)
    tensecondloop.start(10)
     
    
    chatsrvr.run()