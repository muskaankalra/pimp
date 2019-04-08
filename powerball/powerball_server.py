import asyncio
import playground
from Homepage import Homepage 

class HomepageServerProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))

        self.transport = transport

        self.homepage = Homepage()
        
        self.transport.write(self.homepage.welcome_narratives())
        
    def data_received(self, data):
        string = data.decode()
        string = string[:-1]
        output = self.homepage.input(string)
        self.transport.write(output.encode())


loop = asyncio.get_event_loop()

# Each client connection will create a new protocol instance
coro = playground.create_server(HomepageServerProtocol, '20191.10.20.30', 6261)

server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}')
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

loop.run_until_complete(server.wait_closed())
