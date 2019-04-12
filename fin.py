    def send_fin(self, transport, seq, ack):
        finpacket = self.pimppacket.FinPacket(seq,ack)
        transport.write(finpacket.__serialize__())

    def send_finAck(self, transport, seq, ack):
        finpacket = self.pimppacket.FinPacket(seq,ack)
        transport.write(finpacket.__serialize__())
      


    def close(self):
        global SC_flag
        if SC_flag == "Server":
            self.protocol.send_fin(self.protocol.transport,self.protocol.SeqNum,self.protocol.Client_seqNum)

        elif SC_flag == "Client":
            self.protocol.send_fin(self.protocol.transport,self.protocol.seqNum,self.protocol.Server_seqNum)

    def processFinpacket(self,pkt):
        self.SeqNum +=1 #pkt.ackNum 
        self.Client_seqNum = pkt.seqNum + 1
        self.send_finAck(self.transport, self.SeqNum, self.Client_seqNum)
        self.Server_state = SER_CLOSING
        self.higherProtocol.connection_lost()




                    elif pkt.FIN == True and pkt.ACK == False and self.Server_state == self.SER_ESTABLISHED :
                        self.processFinpacket(pkt)

                        #timer = Timer(0.5,self.close_timeout())

                    elif pkt.FIN == True and pkt.ACK == True and self.Server_state == self.SER_ESTABLISHED:
                        pass
                        """
                        self.SeqNum = pkt.ackNum 
                        self.Client_seqNum = pkt.seqNum + len(pkt.data)
                        self.send_Ack(self.transport, self.SeqNum, self.Client_seqNum)
                        self.Server_state = LISTEN
                        self.transport.close()
                        """

                        #self.Server_state = LISTEN

                    elif pkt.ACK == True and self.Server_state == self.SER_CLOSING:
                        self.Server_state = LISTEN
                        self.transport.close()

        def processFinpacket(self, pkt):
            self.seqNum = pkt.ackNum 
            self.Server_seqNum = pkt.seqNum + 1
            self.send_finAck(self.transport, self.seqNum, self.Server_seqNum)
            self.Client_state = CLI_ClOSING
            self.higherProtocol.connection_lost()


                    elif pkt.FIN == True and pkt.ACK == False and self.Client_state == self.CLI_ESTABLISHED:
                        pass
                       #self.processFinpacket(pkt)

                    elif pkt.FIN == True and pkt.ACK == True and self.Client_state == self.CLI_ESTABLISHED:
                        self.seqNum = pkt.ackNum 
                        self.Server_seqNum = pkt.seqNum + 1
                        self.send_Ack(self.transport, self.seqNum, self.Server_seqNum)
                        self.Client_state = CLI_CLOSED
                        self.higherProtocol.connection_lost()
                        self.transport.close()

                    elif pkt.ACK == True and self.Client_state == self.CLI_ClOSING:
                        self.CLIENT = CLI_CLOSED
                        self.transport.close()
    
