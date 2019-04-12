import random
import asyncio
import sys
import playground


class HomepageClientProtocol(asyncio.Protocol):
    def __init__(self, message, loop):
        self.message = message
        self.loop = loop

    def connection_made(self, transport):
        transport.write(self.message.encode())
        self.transport = transport

    def data_received(self, data):
        print(data.decode())
        input = stdinAlert()
        self.transport.write(input.encode())
        
    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')
        self.loop.stop()

def stdinAlert():
    lines = sys.stdin.readline()
    return lines

loop = asyncio.get_event_loop()

loop.add_reader(sys.stdin, stdinAlert)

message = stdinAlert()

coro = playground.create_connection(lambda: HomepageClientProtocol(message, loop),
                              '20191.157.157.157', 101)
loop.run_until_complete(coro)
loop.run_forever()
