from sonzo.telnet import TelnetServer, SonzoClient
import logging

LMAGENTA           = chr(27) + "[1;35m"
WHITE              = chr(27) + "[37m"
LOGIN = "\n\r\n\r\n\r                             {}Welcome to Sonzo Chat!\n\r\n\r{}"
class ChatServer(TelnetServer):
    """
    Custom chat server that inherits from sonzo.TelnetServer
    """

    def __init__(self, address='', port=23, timeout=0.1):
        # Overridden medthod  
        TelnetServer.__init__(self, address='', port=23, timeout=0.1)
        logging.info(" Sonzo Chat Server starting up...")
        
    def run(self):
        # Overridden medthod    
        while True:
            self.poll()
            self.processClients()
            
            
    def newConnection(self, sock, addr):
        # Overridden medthod    
        return ChatClient(sock, addr)

        
    def onConnect(self, client):
        # Overridden medthod    
        logging.info(" {} has connected.".format(client.addrport()))
        for user in self._clients.values():
            if user is not client:
                user.systemMessage("{} has joined the chat!\n\r".format(client.addrport()))
                
        client.systemMessage(LOGIN.format(LMAGENTA, WHITE))
    
    def onDisconnect(self, client):
        # Over-ridden medthod 
        logging.info(" {} disconnecting.".format(client.addrport()))        
        for user in self._clients.values():
            if user is not client:
                user.systemMessage("{} logged off.\n\r".format(client.addrport()))
        
        
    def processClients(self):
        # Overridden medthod    
        self.chat()        
        
 
    # This method is specific to the ChatServer class and not a part
    # of the sonzo.TelnetServer class.
    def chat(self):
        for client in self._clients.values():
            if client.commandReady():
                if len(client._cmd_list) > 0:
                    msg = client._cmd_list.pop()
                    
                    #Check to see if someone issues a command.
                    if msg.startswith("=a".lower()):
                        client.setANSIMode()
                        client.systemMessage("ANSI: {}\n\r".format(client._ansi))
                        logging.info(" {} changing ANSI to: {}.".format(client.addrport(), client._ansi))
                        continue
                    if msg.startswith("/quit".lower()):
                        client.disconnect()
                        continue
                    if msg.startswith("~".lower()):
                        logging.info(" {} changing character mode to: {}.".format(client.addrport(), client._character_mode))
                        client.setCharacterMode()
                        client.systemMessage("Character Mode is now: {}\n\r".format(client._character_mode))
                        continue
                        
                    # If no command, say it in the chat room.
                    for c in self._clients.values():
                        c.sendMessage(client, msg)


class ChatClient(SonzoClient):
    """
    Custom server side client object inherited from sonzo.SonzoClient.
    
    This client IS NOT an actual client side telnet client.
    """
    def _init_(self, sock, addr):
        # Overridden medthod    
        SonzoClient.__init__(self, sock, addr)
        self.name = addr


    # None of the methods below are a part of the
    # sonzo.SonzoClient class.    
    def sendMessage(self, client, message):
        message = "{} says, {}".format(client.addrport(), message)
        self.send(message)

    def systemMessage(self, message):
        self.send(message)

    def disconnect(self):
        """
        Disconnect user.
        """
        self.systemMessage("Goodbye!")
        self._new_messages = False
        self._connected = False


        
if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    chatsrvr = ChatServer(address='', port=23)
    chatsrvr.run()