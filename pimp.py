import playground
import hashlib
import random, datetime
import sys, time, os, logging, asyncio
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocol, StackingProtocolFactory, StackingTransport
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT16,UINT32,STRING,BUFFER,BOOL



class Timer:                                        #Timer to check for timeouts
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self.job())

    async def job(self):                           
        await asyncio.sleep(self._timeout)
        await self._callback()

class PIMPPacket(PacketType):                       #Packet Definitions
    DEFINITION_IDENTIFIER = "roastmyprofessor.pimp.PIMPPacket"
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

    def cal_checksum(self):
        self.checkSum = b"0"
        GNByte = self.__serialize__()
        hash_value = hashlib.md5()
        hash_value.update(GNByte)
        return hash_value.digest()
    
    def updateChecksum(self):
        self.checkSum = self.cal_checksum()

    def verifyChecksum(self):
        oldChksum = self.checkSum
        newChksum = self.cal_checksum()
        if oldChksum == newChksum:
            return True
        else:
            return False

    @classmethod
    def SynPacket(cls, seq):
        pkt = cls()
        pkt.ACK = False
        pkt.SYN = True
        pkt.FIN = False
        pkt.RTR = False
        pkt.RST = False
        pkt.seqNum = seq
        pkt.data = b'0'
        pkt.ackNum = b'0'
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        print("!!!!!!!!!!!!!!!!!!!!!!!!SENT SYN with Seq Num=" + str(pkt.seqNum))
        return pkt
        
    @classmethod
    def AckPacket(cls, syn, ack):
        pkt = cls()
        pkt.ACK = True
        pkt.SYN = False
        pkt.FIN = False
        pkt.RTR = False
        pkt.RST = False
        pkt.seqNum = syn
        pkt.ackNum = ack
        pkt.data = b'0'
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        print("!!!!!!!!!!!!!!!!!!!!!!!!SENT Ack !!!!!!!!!!!!!!!!" + "Seq="+str(pkt.seqNum) + "Ack="+str(pkt.ackNum))
        return pkt

    @classmethod
    def SynAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.ACK = True
        pkt.SYN = True
        pkt.FIN = False
        pkt.RTR = False
        pkt.RST = False
        pkt.seqNum = seq
        pkt.ackNum = ack
        pkt.data = b'0'
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        print("!!!!!!!!!!!!!!!!!!!!!!!!SENT SYNACK!!!!!!!!!!!!!!!!!!!!!!!!!" + "Seq="+str(pkt.seqNum) + "Ack="+str(pkt.ackNum))
        return pkt

    @classmethod
    def DataPacket(cls, seq, ack, data):
        pkt = cls()
        pkt.ACK = False
        pkt.SYN = False
        pkt.FIN = False
        pkt.RTR = False
        pkt.RST = False
        pkt.seqNum = seq
        pkt.ackNum = ack
        pkt.data = data
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        print("!!!!!!!!!!!!!!!!!!!!!!!!SENT DATA PACKET !!!!!!!!!!!!!!!!!!!!!!!!!" + "Seq="+str(pkt.seqNum) + "Ack="+str(pkt.ackNum))
        return pkt

    @classmethod
    def RtrPacket(cls, seq, ack, data):
        pkt = cls()
        pkt.ACK = False
        pkt.SYN = False
        pkt.FIN = False
        pkt.RTR = True
        pkt.RST = False
        pkt.seqNum = seq
        pkt.ackNum = ack
        pkt.data = b'0'
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        print("!!!!!!!!!!!!!!!!!!!!!!!!SENT RTR PACKET !!!!!!!!!!!!!!!!!!!!!!!!!" + "Seq="+str(pkt.seqNum) + "Ack="+str(pkt.ackNum))
        return pkt

    @classmethod
    def FinPacket(cls, seq, ack):
        pkt = cls()
        pkt.ACK = False
        pkt.SYN = False
        pkt.FIN = True
        pkt.RTR = False
        pkt.RST = False
        pkt.seqNum = seq
        pkt.ackNum = ack
        pkt.data = b'0'
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        return pkt

    @classmethod
    def RstPacket(cls, seq, ack):
        pkt = cls()
        pkt.ACK = False
        pkt.SYN = False
        pkt.FIN = False
        pkt.RTR = False
        pkt.RST = True
        pkt.seqNum = seq
        pkt.ackNum = ack
        pkt.data = b'0'
        pkt.checkSum = b'0'
        pkt.updateChecksum()
        print("!!!!!!!!!!!!!!!!!!!!!!!!SENT RST PACKET !!!!!!!!!!!!!!!!!!!!!!!!!" + "Seq="+str(pkt.seqNum) + "Ack="+str(pkt.ackNum))
        return pkt

class PIMPTransport(StackingTransport):

    PACKET_BUFF = []

    def pack(length, data): #Method to make packets and return it in a buffer
        PacketSize = 1500
        leed = 0
        end = PacketSize
        TEMP_BUFF = []
        while(length > 0):
            push = data[leed : end]
            length = length - PacketSize
            leed = end
            end = end + PacketSize
            TEMP_BUFF.append(push)
        return(TEMP_BUFF)
        
    def write(self, data):
        pkt = PIMPPacket()
        length = len(pkt.data)
        BUFF = []
        TxWindow = 4000
        notempty = True
    
        if len(data) <= 1500:  #Where to get the Seq and the Ack Number???
            pkt.data = data
            self.lowerTransport().write(pkt.__serialize__())
                
        else:
            BUFF = (pack(length, data))
            notempty = False
            pkt.data = data
            self.lowerTransport().write(pkt.__serialize__())

    #Data Packet stuff

class PIMPServerProtocol(StackingProtocol):
        LISTEN= 100
        SER_SENT_SYNACK= 102
        SER_ESTABLISHED= 103

        def __init__(self):
            print("!!!!!!!!!!IN SERVER!!!!!!!!!!!")
            super().__init__()
            
            self.PIMPServer1 = PIMPPacket()
            self.deserializer = self.PIMPServer1.Deserializer()
            self.seqNum = random.getrandbits(32)
            self.Client_seqNum = 0
            self.Server_state = self.LISTEN
            self.resend_flag = True
            
        def logging_initialize(self):
            self.logger = logging.getLogger('transport_log')
            self.logger.setLevel(logging.DEBUG)
            fd = logging.FileHandler('Server.log')
            fd.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.ERROR)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fd.setFormatter(formatter)
            ch.setFormatter(formatter)
            self.logger.addHandler(fd)
            self.logger.addHandler(ch)
        
        def connection_made(self, transport):
            self.transport = transport

        def sendSynAck(self, transport, seq, ack):
            synackpacket = self.PIMPServer1.SynAckPacket(seq, ack)   
            transport.write(synackpacket.__serialize__())

        def send_rst(self, transport, seq, ack):
            rstpacket = self.PIMPPacket1.RstPacket(self.seq, self.ack)
            transport.write(rstpacket.__serialize__())
            
        def check_timeout(self):
            if self.resend_flag == True and self.Server_state == self.SER_SENT_SYNACK:
                self.sendSynAck(self.transport, self.seqNum -1, self.Client_seqNum)
                self.resend_flag = False
            elif self.resend_flag == True and self.SER_ESTABLISHED:
                self.resend_flag = False
                #retransmission
                pass
            else:
                pass
            
        def data_received(self, data):
            #print(data)
            self.deserializer.update(data)
            for pkt in self.deserializer.nextPackets():
                if pkt.verifyChecksum():
                    if pkt.SYN == True and pkt.ACK == False and self.Server_state == self.LISTEN:
                        print("!!!!!!!!!!!!Packet Received with Syn Number!!!!!!" + str(pkt.seqNum))
                        self.Client_seqNum = pkt.seqNum + 1
                        self.sendSynAck(self.transport, self.seqNum, self.Client_seqNum)
                        self.resend_flag = True
                        timer = Timer(3, self.check_timeout)
                        self.seqNum += 1
                        self.Server_state = self.SER_SENT_SYNACK

                    elif pkt.SYN == False and pkt.ACK == True and self.Server_state == self.SER_SENT_SYNACK:
                        if self.seqNum == pkt.ackNum and self.Client_seqNum == pkt.seqNum:
                            print("!!!!!!!!!!!!!!!!Ack Packet Received !!!!!!!!!!!!!!!!!!!!!")
                            self.resend_flag = False
                            self.Server_state = self.SER_ESTABLISHED
                            print("!!!!!!!!!!!Connection Established!!!!!!!!!!!!!!!!!!!")

                    elif (pkt.SYN == False) and (pkt.ACK == True) and (self.Server_state != self.SER_SENT_SYNACK) and (self.Server_state != self.SER_ESTABLISHED):
                        print("DROPPING PACKET 'ACK SENT BEFORE SYNACK'")

                    elif pkt.SYN == False and pkt.ACK == False and self.Server_state == self.SER_ESTABLISHED and pkt.data != 0:
                        #Process the data Packets Recieved
                        pass

                    else:
                        print("SOMETHING!!!")

                else:
                    print("SOMETHING!!!")
                                                    
class PIMPClientProtocol(StackingProtocol):

        CLI_INITIAL= 200
        CLI_SENT_SYN= 201
        CLI_ESTABLISHED= 202
        
        def __init__(self):
            super().__init__()
            self.PIMPPacket1 = PIMPPacket()
            self.deserializer = self.PIMPPacket1.Deserializer()
            self.seqNum = random.getrandbits(32)
            self.Server_seqNum = 0
            self.Client_state = self.CLI_INITIAL
            self.resend_flag = True
            
           
        def logging_initialize(self):
            self.logger = logging.getLogger('transport_log')
            self.logger.setLevel(logging.DEBUG)
            fd = logging.FileHandler('Client.log')
            fd.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.ERROR)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            fd.setFormatter(formatter)
            ch.setFormatter(formatter)
            self.logger.addHandler(fd)
            self.logger.addHandler(ch)

        def connection_made(self, transport):
            self.transport = transport
            if self.Client_state == self.CLI_INITIAL:
                print("@@@@@IN CLIENT@@@@")
                self.send_syn(self.transport, self.seqNum)
                time1 = datetime.datetime.now()
                timer = Timer(3, self.check_timeout)
                self.seqNum += 1
                self.Client_state = self.CLI_SENT_SYN

        def send_syn(self, transport, seq):
            synpacket = self.PIMPPacket1.SynPacket(seq)
            transport.write(synpacket.__serialize__())

        def send_Ack(self, transport, seq, ack):
            ackpacket = self.PIMPPacket1.AckPacket(seq, ack)
            transport.write(ackpacket.__serialize__())

        def send_rst(self, transport, seq, ack):
            rstpacket = self.PIMPPacket1.RstPacket(self.seq, self.ack)
            transport.write(rstpacket.__serialize__())

        def check_timeout(self):
            if self.resend_flag == True and self.Client_state == self.CLI_SENT_SYN:
                self.send_syn(self.transport, self.seqNum-1)
                self.resend_flag = False
            elif self.resend_flag == True and self.Client_state == self.CLI_ESTABLISHED:
                self.send_Ack(self.transport, self.seqNum, self.Server_seqNum - 1)
                self.resend_flag = False
            else:
                print("TIMEOUT HAS OCCURED")
        
        def data_received(self, data):
            #print(data)
            self.deserializer.update(data)
            for pkt in self.deserializer.nextPackets():
                if pkt.verifyChecksum():
                    if pkt.SYN == True and pkt.ACK == True and self.Client_state == self.CLI_SENT_SYN:
                        if self.seqNum == pkt.ackNum:
                            print("!!!!!!!!!!!!SYNACK Packet Received with Syn Num" + str(pkt.seqNum) + "Ack Num" + str(pkt.ackNum))
                            self.Server_seqNum = pkt.seqNum + 1
                            self.resend_flag = False
                            self.send_Ack(self.transport, self.seqNum, self.Server_seqNum)
                            self.Client_state = self.CLI_ESTABLISHED
                            print("!!!!!!!!!!!Connection Established!!!!!!!!!!!!!!!!!!!")
                        elif self.seqNum != pkt.ackNum:
                            print("!!!!!!!!!SENDING RST PACKET!!!!!!!!")
                            self.Server_seqNum = pkt.seqNum + 1
                            self.send_rst(self.transport, self.seqNum, self.Server_seqNum)
                            self.Client_state = self.CLI_INITIAL

                    elif pkt.SYN == False and pkt.ACK == False and self.Client_state == self.CLI_ESTABLISHED and pkt.data != 0:
                        #Process the data packet recieved
                        pass
                    else:
                        print("SOMETHING!!!")
                else:
                    print("SOMETHING!!!")


PIMPClientFactory = StackingProtocolFactory.CreateFactoryType(lambda: PIMPClientProtocol())
PIMPServerFactory = StackingProtocolFactory.CreateFactoryType(lambda: PIMPServerProtocol())
