##====================================================================
# Assignment: Lab 1 Milestone 1 - Handshake - init file
# Team: GoldenNugget
# Date: 03-25-2019
#====================================================================

import playground
from .pimp import PIMPServerFactory,PIMPClientFactory

pimpConnector = playground.Connector(protocolStack=(PIMPServerFactory(),PIMPClientFactory()))
playground.setConnector("pimp", pimpConnector)
playground.setConnector("lab1_GoldenNuggetNetSec2019", pimpConnector)
