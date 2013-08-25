import logging
import socket
import select
import sys
import re
import time


#--[ Global Constants ]--------------------------------------------------------

UNKNOWN = -1
## Cap sockets to 512 on Windows because winsock can only process 512 at time
## Cap sockets to 1000 on Linux because you can only have 1024 file descriptors
MAX_CONNECTIONS = 512 if sys.platform == 'win32' else 1000
PARA_BREAK = re.compile(r"(\n\s*\n)", re.MULTILINE)
AUTOSENSE_TIMEOUT = 15

#--[ Telnet Commands ]---------------------------------------------------------

SE      = chr(240)      # End of subnegotiation parameters
NOP     = chr(241)      # No operation
DATMK   = chr(242)      # Data stream portion of a sync.
BREAK   = chr(243)      # NVT Character BRK
IP      = chr(244)      # Interrupt Process
AO      = chr(245)      # Abort Output
AYT     = chr(246)      # Are you there
EC      = chr(247)      # Erase Character
EL      = chr(248)      # Erase Line
GA      = chr(249)      # The Go Ahead Signal
SB      = chr(250)      # Sub-option to follow
WILL    = chr(251)      # Will; request or confirm option begin
WONT    = chr(252)      # Wont; deny option request
DO      = chr(253)      # Do = Request or confirm remote option
DONT    = chr(254)      # Don't = Demand or confirm option halt
IAC     = chr(255)      # Interpret as Command
SEND    = chr(  1)      # Sub-process negotiation SEND command
IS      = chr(  0)      # Sub-process negotiation IS command

#--[ Telnet Options ]----------------------------------------------------------

BINARY  = chr(  0)      # Transmit Binary
ECHO    = chr(  1)      # Echo characters back to sender
RECON   = chr(  2)      # Reconnection
SGA     = chr(  3)      # Suppress Go-Ahead
STATUS  = chr(  5)      # Status of Telnet Options
TTYPE   = chr( 24)      # Terminal Type
NAWS    = chr( 31)      # Negotiate About Window Size
TSPEED  = chr( 32)      # Terminal Speed
LINEMO  = chr( 34)      # Line Mode


Telopts = {
    chr(0): "Binary representation",
    chr(1): "Server Echo",
    chr(2): "Reconnection",
    chr(3): "Supress Go Ahead (SGA)",
    chr(24): "Terminal Type",
    chr(31): "Negotiate About Window Size (NAWS)",
    chr(32): "Terminal Speed",
    chr(34): "Line Mode"
    }


#--[ Connection Lost ]---------------------------------------------------------

class ConnectionLost(Exception):
    """
    Custom exception to signal a lost connection to the Telnet Server.
    """
    
    
    
class TelnetServer(object):
    """
    Telnet Server
    """
    
    def __init__(self, address='', port='', timeout=0.1):
        """
        Initialize a new TelnetServer.
        
        address: IP Address to bind too.
        port: Port to bind too.
        timeout: Socket polling timeout.
        """
        self._addr = address
        self._port = port
        self._timeout = timeout
        self._clients = {}
        self._deadclients = []
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self._socket.bind((self._addr, self._port))
            self._socket.listen(5)
        except self._socket.err as err:
            logging.critical("Error: Failed to create the server socket: " + str(err))
            raise
        
        self._server_fileno = self._socket.fileno()
        

    def newConnection(self):
        """
        Used to create new client object when a user first connects.
        This function is only used to create and return a custom client.
        
        Override with your custom code returning a new client object.
        
        You must create your own class that inherits from the 
        SonzoClient class or use SonzoClient class directly. 
        
        Example:
        
        client = SonzoClient()
        return client.
        
        ============== or =================

        class MyClient(SonzoClient):
        ....
        
        client = MyClient()
        return client
        """
        pass
    
        
    def onConnect(self, client):
        """
        New connection handler
        
        Override with custom connection code.
        """
        pass

    
    def onDisconnect(self, client):
        """
        Disconnect handler
        
        Override with custom disconnect code.
        """
        pass
    
        
    def clientCount(self):
        """
        Return current connection count.
        """
        return len(self._clients)
    
    
    def rejectNewConnections(self, msg="Sorry, no new connects at this time."):
        """
        Reject new connections.
        """
        pass
    
    
    def getClientList(self):
        """
        Return list of clients.
        """
        return self._clients.values()
        
        
    def poll(self):
        """
        Poll the server for new connections and handling OI for existing
        connections.
        """
        recv_list = [self._server_fileno]
        
        for client in self._clients.values():
            if client.isConnected():
                recv_list.append(client.getSocket())
            else:
                self.onDisconnect(client)
                del self._clients[client.getSocket()]

        send_list = []
        for client in self._clients.values():
            if client.sendPending():
                send_list.append(client.getSocket())

        try:                
            rlist, slist, elist = select.select(recv_list, send_list, [], self._timeout)    
        except socket.err as err:
            logging.critical("Socket Select() error: '{}: {}'".format(err[0], err[1]))
            raise
        
        for fileno in rlist:
            # Is it the server's socket for a new connection?
            if fileno == self._server_fileno:
                try:
                    sock, addr = self._socket.accept()
                except socket.error as err:
                    logging.error("Socket error on accept(): '{}: {}'".format(err[0], err[1]))
                    sock.close()
                    continue
            
                # Reject new connects if max connections reached.    
                if self.clientCount() >= MAX_CONNECTIONS:
                    logging.warning("New connection rejected.  Maximum connection count reached.")
                    self.rejectNewConnection()
                    sock.close()
                    continue

                new_client = self.newConnection()
                self._clients[new_client.getSocket()] = new_client
                self.onConnect(client)
                continue
             
            try: 
                self._clients[fileno].recv()
            except ConnectionLost{}:
                self.onDisconnect(self._clients[fileno])
        
        # Send pending buffers to client        
        for fileno in slist:
            self._clients[fileno].send()
            
            
   
   
                
class TelnetOption(object):
    """
    Simple class used to track the status of an extended Telnet option.
    """
    def __init__(self):
        self.local_option = UNKNOWN     # Local state of an option
        self.remote_option = UNKNOWN    # Remote state of an option
        self.reply_pending = False      # Are we expecting a reply?
        self.option_text = "Unknown"    # Friendly text for debug or display
    
        
        
        
        
class SonzoClient(object):
    """
    Telent Client Class
    """
    
    def __init__(self, socket, addr):
        """
        Initialize a new client object.
        """
        
        self._protocol = "telnet"
        self._connected = True
        self._socket = socket
        self._fileno = self._socket.fileno()
        self._addr = addr[0]
        self._port = addr[1]
        self._terminal_type = 'UNKNOWN'
        self._terminal_speed = 'UNKNOWN'
        self._character_mode = False
        self._ansi = False
        self._columns = 80
        self._rows = 24
        self._send_pending = False
        self._echo_buffer = ''
        self._send_buffer = ''
        self._recv_buffer = ''
        self._connect_time = time.time()
        # If you want to kick for being idle too long
        self._last_message = time.time()
        # Are we kicking the client off?
        self._kicked = False
        
        
        ## State variables for interpreting incoming telnet commands
        self._telnet_got_iac = False        # Are we inside an IAC sequence?
        self._telnet_got_cmd = None         # Did we get a telnet command?
        self._telnet_got_sb = False         # Are we inside a subnegotiation?
        self._telnet_opt_dict = {}          # Mapping for up to 256 TelnetOptions
        self._telnet_echo = False           # Echo input back to the client?
        self._telnet_echo_password = False  # Echo back '*' for passwords?
        self._telnet_sb_buffer = ''         # Buffer for sub-negotiations
        self._auto_sensing_done = False     #True when all the negotiations are done    
        
    def getSocket(self):
        """
        Return client's socket id.
        """
        return self._fileno
    
    
    def isConnected(self):
        """
        Is the client connected?
        """
        if self._connected and not self._kicked:
            return True
        return False
 
     
    def sendPending(self):
        """
        Is there data waiting to send to the client?
        """
        if len(self._send_buffer):
            return True
        return False

    def inCharacterMode(self):
        """
        Is the client in character mode?
        """
        if self_character_mode:
            return True
        else:
            return False
    
    def setCharacterMode(self):
        """
        Set client in Character Mode.
        """
        self._character_mode = True
        
        
    def setLineMode(self):
        """
        Set client in LineMode
        """
        self._character_mode = False
        
        
    def send(self):
        """
        Called by TelnetServer to send data to the client.
        """
        if self._characterMode():
            try:
                sent = self._socket.send(bytes(self.send_buffer, "cp1252"))
            except socket.error as err:
                self._connected = False
                return False 
        else:
            # Is the user currently typing?
            if len(self._recv_buffer):
                # Is the users send buffer getting to large while waiting for them to finish typing? Kick them!
                if len(self._send_buffer) > 8388608: :
                    self._kicked = True
                    return
        
                else:
                    self._send_pending = False
                    try:
                        sent = self._socket.send(bytes(self.send_buffer, "cp1252"))
                    except socket.error as err:
                        self._connected = False
                        return False            
            
                    self._bytes_sent = sent
                    self._send_buffer = self._send_buffer[sent:]
            else:
                self._send_pending = True
             
               
            
    def recv(self):
        """
        Called my TelnetServer to recieve data from the client.
        """
        try:
            #Encode recieved bytes in ansi
            data = str(self.sock.recv(2048), "cp1252")
        except socket.error as err:
            logging.error("RECIEVE socket error '{}:{}' from {}".format(err[0], err[1], self.addrport()))
            raise ConnectionLost()        
        
        
        if not len(data):
            logging.debug("No data received.  Connection lost.")
            raise ConnectionLost()
        
        
        for byte in data:
            self._iac_sniffer(byte)
             
        if self.inCharacterMode():
            pass
        
        else:
            while True:
                mark = self._recv_buffer.find('\n')
                if mark == -1:
                    break
                cmd = _recv_buffer[:mark].strip()
                self._cmd_list.append(cmd)
                self._cmd_ready = True
                self._recv_buff = self._recv_buffer[mark + 1]
                
                
    
# Private telnet negotiation functions

    def _request_do_sga(self):
        """
        Request do Suppress Go-Ahead Option (SGA) RFC-858.
        """
        logging.debug("Requesting suppress go-ahead.")
        self._iac_do(SGA)
        self._note_reply_pending(SGA, True)
        
        
    def _request_will_echo(self):
        """
        Request WILL echo to echo client's text.  RFC-857
        """
        logging.debug("Requesting will echo.")
        self._iac_will(ECHO)
        self._note_reply_pending(ECHO, True)
        self._telnet_echo = True
        
        
    def _request_wont_echo(self):
        """
        Request WON'T echo to not echo client's text.  RC-857
        """
        logging.debug("Requesting won't echo.")
        self._iac_wont(ECHO)
        self._note_reply_pending(ECHO, True)
        self._telnet_echo = False        
        
        
    def password_mode_on(self):
        """
        Request disable echo for passwords protection.
        """
        logging.debug("Requesting to disable echo for passwords")
        self._iac_will(ECHO)
        self._note_reply_pending(ECHO, True)
        
        
    def password_mode_off(self):
        """
        Request echo on since we aren't entering a password at this time.
        """
        logging.debug("Request to enable echo since not entering a password at this time.".format(self.address))
        self._iac_wont(ECHO)
        self._note_reply_pending(ECHO, True)        
        

    def _request_naws(self):
        """
        Request to Negotiate About Window Size.  See RFC 1073.
        """
        self._iac_do(NAWS)
        self._note_reply_pending(NAWS, True)
        
    
    def _request_terminal_type(self):
        """
        Begins the Telnet negotiations to request the terminal type from
        the client.  See RFC 779.
        """
        self._iac_do(TTYPE)
        self._note_reply_pending(TTYPE, True)
    
        
    def _request_terminal_speed(self):
        """
        Begins the Telnet negotiations to request the terminal speed from
        the client.  See RFC 1079.
        """
        self._iac_do(TSPEED)
        self._note_reply_pending(TSPEED, True)          
    
        
