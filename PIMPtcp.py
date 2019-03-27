from playground.network.common import PlaygroundAddress
from playground.network.packet.fieldtypes import UINT16, STRING, UINT8, UINT32, BUFFER, BOOL
from playground.network.common import StackingProtocol, StackingProtocolFactory, StackingTransport
import hashlib

# MessageDefinition is the base class of all automatically serializable messages
from playground.network.packet import PacketType
import playground

import sys, time, os, logging, asyncio
#logger = logging.getLogger(__name__)

class PIMPPacket(PacketType):
    TYPE_SYN = "SYN"
    TYPE_ACK = "ACK"
    TYPE_FIN = "FIN"
    TYPE_DATA = "DATA"
    DEFINITION_IDENTIFIER = "PIMP.Packet"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("seqNum", UINT32),
        ("ackNum", UINT32),
        ("ACK", BOOL),
        ("RST", BOOL),
        ("SYN", BOOL),
        ("FIN", BOOL),
        ("RTR", BOOL),
        ("checkSum", BUFFER),
        ("data", BUFFER)
        ]

    def Cal_checksum(self):
        self.Checksum = b"0"
        GNByte = self.__serialize__()
        hash_value = hashlib.sha256()
        hash_value.update(GNByte)
        return hash_value.digest()
    
    def verfiyChecksum(self):
      oldChksum = self.Checksum
      newChksum = self.Cal_checksum()
      self.Checksum = newChksum
      if oldChksum == newChksum:
        return True
      else:
        return False

    @classmethod
    def SynPacket(cls, seq):
        pkt = cls()
        pkt.Type = cls.TYPE_SYN
        pkt.seqNum = seq    #seq = x
        pkt.Cal_checksum()
        return pkt

    @classmethod
    def SynAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_SYN + cls.TYPE_ACK
        pkt.seqNum = seq    #seq = y
        pkt.ackNum = ack    #ack = seq(received) + 1
        pkt.Cal_checksum()
        return pkt                                                                                                                                                                                                                                                                                                                                                                                                                                                         

    @classmethod
    def AckPacket(cls, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_ACK
        pkt.ackNum = ack     #ack = y + 1
        pkt.Cal_checksum()
        return pkt

    @classmethod
    def DataPacket(cls, seq, data):
        pkt = cls()
        pkt.Type = cls.TYPE_DATA
        pkt.seqNum = seq
        pkt.data = data
        pkt.Cal_checksum()
        return pkt

class PIMPTransport(StackingTransport):   #inherit the stackingtransport class
    CHUNK_SIZE = 1500    #each packet is

    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol   #the protocol instance are put in from client or server protocol

    def write(self, data):    #mimic the stackingtransport class
        if self.protocol:
            if not self.protocol.isClosing():

                i = 0
                index = 0
                sentData = None
                while (i < len(data)):   #the serialized http packet is split into several chunks
                    if (i + self.CHUNK_SIZE < len(data)):
                        sentData = data[i: i + self.CHUNK_SIZE]
                    else:
                        sentData = data[i:]
                    i += len(sentData)   #the length of sentData is always 38, why is it???
                    #whether to change the seqNum, depends on the PIMP's definition
                    pkt = PIMPPacket.DataPacket(self.protocol.seqNum, sentData)   #make a data packet with one chunk bytes
                    index += 1
                    ackNumber = self.protocol.seqNum + len(sentData)  #the next ack_num we should get for our last sent data packet

                    #we create a sentdata_cache to contain those data packets sent without receiving corresponding ack packets
                    if len(self.protocol.sentDataCache) <= self.protocol.WINDOW_SIZE:   #there is window space for packet to send immediately
                        print("PIMPTransport: Sending packet {!r}, sequence number: {!r}".format(index, pkt.seqNum))
                        self.protocol.transport.write(pkt.__serialize__())
                        self.protocol.sentDataCache[ackNumber] = (pkt)  #Removed the Timestamp

                    else:
                        print("PIMPTransport: Buffering packet {!r}, sequence number: {!r}".format(index, pkt.seqNum))
                        #if the window is fully used, then we need to put packets waiting to send into sending buffer
                        self.protocol.sendingDataBuffer.append((ackNumber, pkt))
                        # self.protocol.sendNextDataPacket()

                    self.protocol.seqNum += len(sentData)
                print("PIMPTransport: Batch transmission finished, number of packets sent: {!r}".format(index))
            else:
                print("PIMPTransport: protocol is closing, unable to write anymore.")

        else:
            print("PIMPTransport: Undefined protocol, writing anyway...")
            print("PIMPTransport: Write got {} bytes of data to pass to lower layer".format(len(data)))
            super().write(data)
        # self.protocol.sendNextDataPacket()

    def close(self):
        if not self.protocol.isClosing():
            print("Prepare to close...")
            self.protocol.prepareForFin()
        else:
            print("PIMPTransport: Protocol is already closing.")


class PIMPServerProtocol(StackingProtocol):
  #state definitions
  State_definition = {
    0:"DEFAULT",
    100:"CLOSED",
    101:"LISTEN",
    102:"SERVER_SYN-RECEIVED" ,
    103:"SERVER_TRANSMISSION",
    
    301:"CLIENT_INITIAL_SYN",
    302:"Client_SYN_SENT",
    303:"CLIENT_TRANSMISSION",
    304:"CLIENT_FIN_WAIT",
  }
  
  DEFAULT = 0
  CLOSED = 100
  LISTEN = 101
  SERVER_SYN_RECEIVED = 102
  SERVER_TRANSMISSION =103

  def __init__(self):
    super().__init__()
    self.seqNo = int.from_bytes(os.urandom(4), byteorder='big')
    self.client_seqNo = None
    self.state = self.DEFAULT
    self.sentDataCache = {}
    self.receivedDataBuffer = {}   #receive the packet which is out of order
    # create logger with 'spam_application'
    self.logger = logging.getLogger('transport_log')
    self.logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fd = logging.FileHandler('transport.log')
    fd.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fd.setFormatter(formatter)
    ch.setFormatter(formatter)
    self.logger.addHandler(fd)
    self.logger.addHandler(ch)
    
  def sendSyn(self,transport):
    synPacket = PIMPPacket.SynPacket(self.seqNo)
    #logging
    self.logger.info('Sending SYN packet with Seq Number' + str(self.seqNo))
    transport.write(synPacket.__serialize__())
    
  def sendSynAck(self, transport,SynAck_seqNo):
    synAckPacket = PIMPPacket.SynAckPacket(SynAck_seqNo, self.client_ackNo)
    #logging
    self.logger.info('Sending SYN_ACK packet with Seq Number ' + str(SynAck_seqNo) + ' Ack Number ' +  str(self.client_ackNo))
    transport.write(synAckPacket.__serialize__())
  
  def sendAck(self, transport):
    AckPacket = PIMPPacket.AckPacket(self.client_seqNo)
    self.logger.info('Sending ACK packet with Ack Number' + str(self.client_seqNo))
    transport.write(AckPacket.__serialize__())
    
  #def sendFin(self, transport):
    #function not defined 
  def connection_made(self, transport):
    self.transport = transport
  
  def processAckPkt(self,pkt):
        latestAckNumber = pkt.ackNum  #the ackNum of the last ack packet we get
        while latestAckNumber in list(self.sentDataCache):  #when there is an ackNum stacked in the sent_buffer
            print ("Received ACK for dataSeq: {!r}, removing".format(self.sentDataCache[latestAckNumber][0].seqNum))
            del self.sentDataCache[latestAckNumber]    #delete the data packet from the sent buffer
            break
            
  def processDataPkt(self, pkt):
    if self.state == self.CLOSED:
        self.logging.info("Connection closed")
    else:
      if pkt.seqNum == self.client_seqNo:  # the data with the seq_num is exactly what we want
        self.client_seqNo = pkt.seqNum + len(pkt.Data)  # update the ack_num for next packet, y + len(data) -> ack_num
        self.sendAck(self.transport)  #send the corresponding ack packet
        self.higherProtocol().data_received(pkt.Data)  # upload the data to higher level
        while self.client_seqNo in self.receivedDataBuffer:# transmit the packet with higher seq_num than expectation we get before to higher layer
              (nextPkt, receive_time) = self.receivedDataBuffer.pop(self.client_seqNo)
              self.client_seqNo = nextPkt.seqNum + len(nextPkt.Data) # update the ack_num for next packet, y + len(data) -> ack_num
              self.sendAck(self.transport)  # send the corresponding ack packet
              self.higherProtocol().data_received(nextPkt.Data)  # upload the data to higher level--http
      elif pkt.seqNum > self.client_seqNum:
          self.logging.info()
          self.receiveDataBuffer[pkt.seqNum] = (pkt.time.time())

      else:
          self.logging.info("")
          ackNum = pkt.seqNum + len(pkt.Data)
          self.sendAck(self.transport) 

  
  def data_received(self,data):
    self.deserializer.update(data)
    for pkt in self.deserializer.nextPackets():
          if isinstance(pkt, PIMPPacket):
              if pkt.verfiyChecksum():   #check whether there is error appeared in any one tcp packet
                  if  pkt.Type == "SYN" and self.state == self.LISTEN:
                    self.state = self.Server_SYN_RECEIVED
                    self.client_seqNo = pkt.seqNum + 1
                    SynAck_seqNo  = self.seqNo
                    self.sendSynAck(self.transport,SynAck_seqNo)
                    self.seqNo += 1
                  elif pkt.Type == "ACK" and self.state == self.Server_SYN_RECEIVED:
                    if pkt.ackNum == self.seqNo:
                      self.state = self.SERVER_TRANSMISSION
                      higherTransport = PIMPTransport(self.transport,self)
                      self.higherProtocol().connection_made(higherTransport)
                      
                    else:
                      print("Server: Wrong ACK packet: ACK number: {!r}, expected: {!r}".format(
                                    pkt.ackNum, self.seqNo))
                  elif (pkt.Type == "DATA") and (self.state == self.SERVER_TRANSMISSION):
                        self.processDataPkt(pkt)
                                    
                  elif (pkt.Type == "ACK") and (self.state == self.SERVER_TRANSMISSION):
                        self.processAckPkt(pkt)
                  else:
                    self.logging.info("Server: Wrong packet: seq num " + pkt.seqNum + ", type" + pkt.Type)
              else:
                  self.logging.info("Error in packet, checksum mismatch"+ str(pkt.Checksum))
          else:
               self.logging.info("Wrong packet class type "+ str(type(pkt)))

        
class PIMPClientProtocol(StackingProtocol):
  #state definitions
  State_definition = {
    0:"DEFAULT",
    100:"CLOSED",
    101:"LISTEN",
    102:"Server_SYN-RECEIVED" ,
    103:"SERVER_TRANSMISSION",
    
    301:"CLIENT_INITIAL_SYN",
    302:"Client_SYN_SENT",
    303:"CLIENT_TRANSMISSION",
    304:"CLIENT_FIN_WAIT",
  }
  DEFAULT = 0
  CLOSED = 100
  LISTEN = 101
  CLIENT_INITIAL_SYN = 301
  Client_SYN_SENT = 302
  CLIENT_TRANSMISSION = 303
  CLIENT_FIN_WAIT = 304
  CLIENT_CLOSED = 305
  
  def __init__(self):
    super().__init__()
    self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
    self.client_seqNo = None
    self.state = DEFAULT
    self.client_state = self.CLIENT_INITIAL_SYN
    self.receivedDataBuffer = {}

  def logging_initialize(self):
      self.logger = logging.getLogger('transport_log')
      self.logger.setLevel(logging.DEBUG)
      # create file handler which logs even debug messages
      fd = logging.FileHandler('transport.log')
      fd.setLevel(logging.DEBUG)        
      # create console handler with a higher log level
      ch = logging.StreamHandler()
      ch.setLevel(logging.ERROR)
      formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
      fh.setFormatter(formatter)
      ch.setFormatter(formatter)
      self.logger.addHandler(fh)
      self.logger.addHandler(ch)
        
  def sendSyn(self,transport):
    synPacket = PIMPPacket.SynPacket(self.seqNum)
    #logging
    self.logger.info('Sending SYN packet with Seq Number' + str(self.seqNum))
    transport.write(synPacket.__serialize__())
  
  def sendAck(self, transport):
    AckPacket = PIMPPacket.AckPacket(self.client_seqNum)
    self.logger.info('Sending ACK packet with Ack Number' + str(self.client_seqNum))
    transport.write(AckPacket.__serialize__())
  
  #def sendFinAck(self, transport):
    #function not defined 
  def processDatapkt(self, pkt):
    if self.state == self.CLIENT_CLOSED:
          self.logging.info("Connection closed")
    else:
          if pkt.seqNum == self.client_seqNum:
              self.logging.info("")
              self.client_seqNum = pkt.seqNum + len(pkt.Data)
              self.sendAck(self.transport)
              self.higherProtocol().data_received(pkt.Data)
              while self.client_seqNum in self.receivedDataBuffer:
                  (nxtPkt, receive_time) = self.receiveDataBuffer.pop(self.partnerSeqNumber)
                  self.client_seqNum = nxtPkt.SequenceNumber + len(nxtPkt.Data)
                  self.sendAck(self.transport)
                  self.higherProtocol().data_received(pkt.Data)
          elif pkt.seqNum > self.client_seqNum:
              self.logging.info()
              self.receiveDataBuffer[pkt.seqNum] = (pkt.time.time())
          else:
              self.logging.info("")
              ackNum = pkt.seqNum + len(pkt.Data)
              self.sendAck(self.transport)  
  
  def processAckPkt(self, pkt):
    self.logging.info("")
    latestAckNumber = pkt.ackNum
    
    
  def connection_made(self, transport):
      self.transport = transport
      if self.state == self.CLIENT_INTIAL_SYN:
          self.sendSyn(self.transport)
          self.seqNum += 1
          self.state = self.CLIENT_SYN_SENT
    
    
  def data_received(self,data):
     self.deserializer.update(data)
     for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PIMPPacket):   #check if this packet is an instance of PIMPPacket
                if pkt.verfiyChecksum():
                    if ("SYN" in pkt.Type) and ("ACK" in pkt.Type) and (self.state == self.CLIENT_SYN_SENT):
                            # check ack num
                        if(pkt.ackNum == self.seqNum):
                          self.logging.info("SYN-ACK with sequence number" + str(pkt.seqNum) + ", ack number" + str(pkt.ackNum))
                          self.state = self.CLIENT_TRANSMISSION
                          self.client_seqNum = pkt.seqNum + 1
                          self.sendAck(self.transport)
                          higherTransport = PIMPTransport(self.transport, self)
                          
                        else:
                          self.logging.info()
                      
                    elif(pkt.Type == "ACK") and (self.state == self.CLIENT_TRANSMISSION):
                       self.processAckpkt(pkt)
                    
                    elif(pkt.Type == "DATA") and (self.state == self.CLIENT_TRANSMISSION):
                       self.processDatapkt(pkt)  
                    else:
                      self.logging.info("Client: Wrong packet: seq num " + pkt.seqNum + ", type" + pkt.Type)
                else:
                  self.logging.info("Error in packet, checksum mismatch"+ str(pkt.Checksum))
            else:
               self.logging.info("Wrong packet class type "+ str(type(pkt)))
  
  def connection_lost(self, error):
    self.higherProtocol().connection_lost(error)
    self.logging.info()
    self.transport = None

class EchoControl:
    def __init__(self):
        self.txProtocol = None
        
    def buildProtocol(self):
        return PIMPClientProtocol(self.callback)
        
    def connect(self, txProtocol):
        self.txProtocol = txProtocol
        print("Echo Connection to Server Established!")
        self.txProtocol = txProtocol
        sys.stdout.write("Enter Message: ")
        sys.stdout.flush()
        asyncio.get_event_loop().add_reader(sys.stdin, self.stdinAlert)
        
    def callback(self, message):
        print("Server Response: {}".format(message))
        sys.stdout.write("\nEnter Message: ")
        sys.stdout.flush()
        
    def stdinAlert(self):
        data = sys.stdin.readline()
        if data and data[-1] == "\n":
            data = data[:-1] # strip off \n
        self.txProtocol.send(data)

        

USAGE = """usage: echotest <mode> [-stack=<stack_name>]
  mode is either 'server' or a server's address (client mode)"""

if __name__=="__main__":
    echoArgs = {}
    
    stack = "default"
    
    args= sys.argv[1:]
    i = 0
    for arg in args:
        if arg.startswith("-"):
            k,v = arg.split("=")
            echoArgs[k]=v
        else:
            echoArgs[i] = arg
            i+=1
            
    if "-stack" in echoArgs:
        stack = echoArgs["-stack"]
    
    if not 0 in echoArgs:
        sys.exit(USAGE)

    mode = echoArgs[0]
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    from playground.common.logging import EnablePresetLogging, PRESET_DEBUG
    EnablePresetLogging(PRESET_DEBUG)
    
    if mode.lower() == "server":
        coro = playground.create_server(lambda: PIMPServerProtocol(), port=101, family=stack)
        server = loop.run_until_complete(coro)
        print("Echo Server Started at {}".format(server.sockets[0].gethostname()))
        loop.run_forever()
        loop.close()
        
        
    else:
        remoteAddress = mode
        control = EchoControl()
        coro = playground.create_connection(control.buildProtocol, 
            host=remoteAddress, 
            port=101,
            family=stack)
        transport, protocol = loop.run_until_complete(coro)
        print("Echo Client Connected. Starting UI t:{}. p:{}".format(transport, protocol))
        control.connect(protocol)
        loop.run_forever()
        loop.close()
        
