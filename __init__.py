##====================================================================
# Assignment: Lab 1 Milestone 1 - Handshake - init file
# Team: GoldenNugget
# Date: 03-25-2019
#====================================================================

import playground
from .protocol import StackingProtocolFactory

pimpConnector = playground.Connector(protocolStack=(PIMPServerProtocol(),PIMPClientProtocol()))
playground.setConnector("pimp", pimpConnector)
playground.setConnector("lab1_GoldenNuggetNetSec2019", pimpConnector)
