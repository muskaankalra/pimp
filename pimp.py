##====================================================================
# Assignment: Lab 1 Milestone 1 - Handshake - pimp file
# Team: GoldenNugget
# Date: 03-25-2019
#====================================================================

import playground
import hashlib
import sys, time, os, logging, asyncio
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocol, StackingProtocolFactory, StackingTransport
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16,UINT32,STRING,BUFFER,BOOL
from playground.network.packet.fieldtypes.attributes import Optional

class PIMPPacket(PacketType):

    DEFINITION_IDENTIFIER = "PIMP.Packet"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("seqNum", UINT32({Optional: True})),
        ("ackNum", UINT32({Optional: True})),
        ("ACK", BOOL({Optional: True})),
        ("RST", BOOL({Optional: True})),
        ("SYN", BOOL({Optional: True})),
        ("FIN", BOOL({Optional: True})),
        ("RTR", BOOL({Optional: True})),
        ("checkSum", BUFFER({Optional: True})),
        ("data", BUFFER({Optional: True}))
        ]

    def Cal_checksum(self):
        self.checkSum = b"0"
        GNByte = self.__serialize__()
        hash_value = hashlib.md5()
        hash_value.update(GNByte)
        return hash_value.digest()

    def updateChecksum(self):
    	self.checkSum = self.Cal_checksum()
    
    def verfiyChecksum(self):
      oldChksum = self.checkSum
      newChksum = self.Cal_checksum()
      self.checkSum = newChksum
      if oldChksum == newChksum:
        return True
      else:
        return False

    @classmethod
    def SynPacket(cls, seq):
        pkt = cls()
        pkt.ACK = False
        pkt.RST = False
        pkt.SYN = True
        pkt.FIN = False
        pkt.RTR = False
        pkt.seqNum = seq    
        pkt.updateChecksum() 
        return pkt

    @classmethod
    def SynAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.ACK = True
        pkt.RST = False
        pkt.SYN = True
        pkt.FIN = False
        pkt.RTR = False
        pkt.seqNum = seq    
        pkt.ackNum = ack    
        pkt.updateChecksum() 
        return pkt                                                                                                                                                                                                                                                                                                                                                                                                                                                         

    @classmethod
    def AckPacket(cls, ack):
        pkt = cls()
        pkt.ACK = True
        pkt.RST = False
        pkt.SYN = False
        pkt.FIN = False
        pkt.RTR = False
        pkt.ackNum = ack     
        pkt.updateChecksum() 
        return pkt

    @classmethod
    def DataPacket(cls, seq, data):
        pkt = cls()
        pkt.seqNum = seq
        pkt.data = data
        pkt.updateChecksum() 
        return pkt
      

class PIMPTransport(StackingTransport):
    CHUNK_SIZE = 1500    

    def __init__(self, transport, protocol=None):
        super().__init__(transport)
        self.protocol = protocol   

    def write(self, data):    
        if self.protocol:
            if not self.protocol.isClosing():

                i = 0
                index = 0
                sentData = None
                while (i < len(data)):   
                    if (i + self.CHUNK_SIZE < len(data)):
                        sentData = data[i: i + self.CHUNK_SIZE]
                    else:
                        sentData = data[i:]
                    i += len(sentData)  
                   
                    pkt = PIMPPacket.DataPacket(self.protocol.seqNum, sentData)   
                    index += 1
                    ackNumber = self.protocol.seqNum + len(sentData)  #the next ack_num we should get for our last sent data packet

                    #we create a sentdata_cache to contain those data packets sent without receiving corresponding ack packets
                    if len(self.protocol.sentDataCache) <= self.protocol.WINDOW_SIZE:   #there is window space for packet to send immediately
                        print("PIMPTransport: Sending packet {!r}, sequence number: {!r}".format(index, pkt.seqNum))
                        self.protocol.transport.write(pkt.__serialize__())
                        self.protocol.sentDataCache[ackNumber] = (pkt)  

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


class PIMPServerProtocol( ):
  State_definition = {
    0:"DEFAULT",
    100:"CLOSED",
    101:"LISTEN",
    102:"SERVER_SYN_RECEIVED" ,
    103:"SERVER_TRANSMISSION",
    
    301:"CLIENT_INITIAL_SYN",
    302:"CLIENT_SYN_SENT",
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
    self.deserializer = PIMPPacket.Deserializer()
    self.seqNo = int.from_bytes(os.urandom(4), byteorder='big')
    self.client_seqNo = None
    self.state = self.LISTEN
    self.sentDataCache = {}
    self.receivedDataBuffer = {}  
    self.logger = logging.getLogger('transport_log')
    self.logger.setLevel(logging.DEBUG)
    fd = logging.FileHandler('transport.log')
    fd.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fd.setFormatter(formatter)
    ch.setFormatter(formatter)
    self.logger.addHandler(fd)
    self.logger.addHandler(ch)
    
  def sendSyn(self,transport):
    synPacket = PIMPPacket.SynPacket(self.seqNo)
    print('Sending SYN packet with Seq Number' + str(self.seqNo))
    transport.write(synPacket.__serialize__())
    
  def sendSynAck(self, transport,SynAck_seqNo):
    synAckPacket = PIMPPacket.SynAckPacket(SynAck_seqNo, self.client_seqNo)
    print('Sending SYN_ACK packet with Seq Number ' + str(SynAck_seqNo) + ' Ack Number ' +  str(self.client_seqNo))
    transport.write(synAckPacket.__serialize__())
  
  def sendAck(self, transport):
    AckPacket = PIMPPacket.AckPacket(self.client_seqNo)
    print('Sending ACK packet with Ack Number' + str(self.client_seqNo))
    transport.write(AckPacket.__serialize__())
    
  #def sendFin(self, transport):
    #function not defined 
  def connection_made(self, transport):
    self.transport = transport
  
  def processAckPkt(self,pkt):
        latestAckNumber = pkt.ackNum  
        while latestAckNumber in list(self.sentDataCache):  
            print ("Received ACK for dataSeq: {!r}, removing".format(self.sentDataCache[latestAckNumber][0].seqNum))
            del self.sentDataCache[latestAckNumber]    
            break
            
  def processDataPkt(self, pkt):
    if self.state == self.CLOSED:
        print("Connection closed")
    else:
      if pkt.seqNum == self.client_seqNo:  
        self.client_seqNo = pkt.seqNum + len(pkt.Data)  
        self.sendAck(self.transport)  
        self.higherProtocol().data_received(pkt.Data)  
        while self.client_seqNo in self.receivedDataBuffer:
              (nextPkt, receive_time) = self.receivedDataBuffer.pop(self.client_seqNo)
              self.client_seqNo = nextPkt.seqNum + len(nextPkt.Data) 
              self.sendAck(self.transport)  
              self.higherProtocol().data_received(nextPkt.Data) 
      elif pkt.seqNum > self.client_seqNum:
          print("")
          self.receiveDataBuffer[pkt.seqNum] = (pkt.time.time())

      else:
          print("")
          ackNum = pkt.seqNum + len(pkt.Data)
          self.sendAck(self.transport) 

  
  def data_received(self,data):
    self.deserializer.update(data)
    for pkt in self.deserializer.nextPackets():
          if isinstance(pkt, PIMPPacket):
              if pkt.verfiyChecksum():   
                  if  pkt.SYN == True and self.state == self.LISTEN:
                    self.state = self.SERVER_SYN_RECEIVED
                    self.client_seqNo = pkt.seqNum + 1
                    SynAck_seqNo  = self.seqNo
                    self.sendSynAck(self.transport,SynAck_seqNo)
                    self.seqNo += 1
                    print("!!!!!!!!!!!!!!!!!!! Receive SYN packet")
                  elif pkt.ACK == True and self.state == self.SERVER_SYN_RECEIVED:
                    if pkt.ackNum == self.seqNo:
                      self.state = self.SERVER_TRANSMISSION
                      print("!!!!!!!!!!!!!!!!!!! Receive ACK packet")
                      #higherTransport = PIMPTransport(self.transport,self)
                      #self.higherProtocol().connection_made(higherTransport)
                      # self.processDataPkt(pkt)
                      
                    else:
                      print("Server: Wrong ACK packet: ACK number:")
                  #elif (pkt == "DATA") and (self.state == self.SERVER_TRANSMISSION):
                   #     self.processDataPkt(pkt)
                                    
                  elif (pkt.ACK == True) and (self.state == self.SERVER_TRANSMISSION):
                        self.processAckPkt(pkt)
                  else:
                    print("Server: Wrong packet: seq num " + pkt.seqNum + ", type")
              else:
                  print("Error in packet, checksum mismatch"+ str(pkt.checkSum))
          else:
               print("Wrong packet class type "+ str(type(pkt)))

        
class PIMPClientProtocol(StackingProtocol):
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
  CLIENT_SYN_SENT = 302
  CLIENT_TRANSMISSION = 303
  CLIENT_FIN_WAIT = 304
  CLIENT_CLOSED = 305
  
  def __init__(self):
    super().__init__()
    self.deserializer = PIMPPacket.Deserializer()
    self.seqNum = int.from_bytes(os.urandom(4), byteorder='big')
    self.client_seqNo = None
    self.state = self.CLIENT_INITIAL_SYN
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
    #self.logger.info('Sending SYN packet with Seq Number' + str(self.seqNum))
    print('Sending SYN packet with Seq Number' + str(self.seqNo))
    transport.write(synPacket.__serialize__())
    print("Sending SYN packet with Seq Number")
  
  def sendAck(self, transport):
    AckPacket = PIMPPacket.AckPacket(self.client_seqNum)
    print('Sending ACK packet with Ack Number' + str(self.client_seqNum))
    #self.logger.info('Sending ACK packet with Ack Number' + str(self.client_seqNum))
    transport.write(AckPacket.__serialize__())
  
  #def sendFinAck(self, transport):
    #function not defined 
  def processDatapkt(self, pkt):
    if self.state == self.CLIENT_CLOSED:
          print("Connection closed")
    else:
          if pkt.seqNum == self.client_seqNum:
              print("")
              self.client_seqNum = pkt.seqNum + len(pkt.Data)
              self.sendAck(self.transport)
              self.higherProtocol().data_received(pkt.Data)
              while self.client_seqNum in self.receivedDataBuffer:
                  (nxtPkt, receive_time) = self.receiveDataBuffer.pop(self.partnerSeqNumber)
                  self.client_seqNum = nxtPkt.SequenceNumber + len(nxtPkt.Data)
                  self.sendAck(self.transport)
                  self.higherProtocol().data_received(pkt.Data)
          elif pkt.seqNum > self.client_seqNum:
              print("")
              self.receiveDataBuffer[pkt.seqNum] = (pkt.time.time())
          else:
              print("")
              ackNum = pkt.seqNum + len(pkt.Data)
              self.sendAck(self.transport)  
  
  def processAckPkt(self, pkt):
    print("")
    latestAckNumber = pkt.ackNum
    
    
  def connection_made(self, transport):
      self.transport = transport
      if self.state == self.CLIENT_INITIAL_SYN:
          self.sendSyn(self.transport)
          self.seqNum += 1
          self.state = self.CLIENT_SYN_SENT
    
    
  def data_received(self,data):
     self.deserializer.update(data)
     for pkt in self.deserializer.nextPackets():
            if isinstance(pkt, PIMPPacket):   #check if this packet is an instance of PIMPPacket
                if pkt.verfiyChecksum():
                    if (pkt.SYN == True) and (pkt.ACK == True) and (self.state == self.CLIENT_SYN_SENT):
                            # check ack num
                        if(pkt.ackNum == self.seqNum):
                          print("SYN-ACK with sequence number" + str(pkt.seqNum) + ", ack number" + str(pkt.ackNum))
                          self.state = self.CLIENT_TRANSMISSION
                          self.client_seqNum = pkt.seqNum + 1
                          self.sendAck(self.transport)
                          higherTransport = PIMPTransport(self.transport, self)
                          print("!!!!!!!!!!!!!!!!!!! Receive SYN+ACK packet")
                        else:
                          print("")
                      
                    elif(pkt.ACK == True) and (self.state == self.CLIENT_TRANSMISSION):
                       self.processAckpkt(pkt)
                    
                    #elif(pkt. == "DATA") and (self.state == self.CLIENT_TRANSMISSION):
                    #   self.processDatapkt(pkt)  
                    else:
                      print("Client: Wrong packet: seq num " + pkt.seqNum + ", type")
                else:
                  print("Error in packet, checksum mismatch"+ str(pkt.checkSum))
            else:
               print("Wrong packet class type "+ str(type(pkt)))
  
  def connection_lost(self, error):
    self.higherProtocol().connection_lost(error)
    print("")
    self.transport = None

       
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
        coro = playground.create_server(lambda: PIMPServerProtocol(), port=107, family=stack)
        server = loop.run_until_complete(coro)
        print("Pimp Server Started at {}".format(server.sockets[0].gethostname()))
        loop.run_forever()
        loop.close()
        
        
    else:
        remoteAddress = mode
        coro = playground.create_connection(lambda: PIMPClientProtocol(), 
            host=remoteAddress, 
            port=107,
            family=stack)
        transport, protocol = loop.run_until_complete(coro)
        print("Pimp Client Connected. Starting UI t:{}. p:{}".format(transport, protocol))
        loop.run_forever()
        loop.close()
    
