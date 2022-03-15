import sys
import os
import platform
import subprocess
import time
from loguru import logger
from pprint import pprint
from pyunifi.controller import Controller

# Setup logging
DEBUG=os.getenv("DEBUG", default='False').lower() in ('true', '1', 't')
logging_level = "INFO"
if DEBUG:
    logging_level = "DEBUG"
logger.remove()
logger.add(sys.stderr, colorize=True, format="<green>{time}</green> - {name}:{function}:{line} - <level>{message}</level>", level=logging_level)

# Static
TOOL_NAME = "get-port-configuration-id"

# Required env vars...
UDM_IP=os.getenv("UDM_IP")
UDM_SWITCH_PORT=int(os.getenv("UDM_SWITCH_PORT"))
UDM_USERNAME=os.getenv("UDM_USERNAME")
UDM_PASSWORD=os.getenv("UDM_PASSWORD")

# Optional env vars...
UDM_SSL_VERIFY=os.getenv("UDM_SSL_VERIFY", default='True').lower() in ('true', '1', 't')

# Verify args
if UDM_IP is None:
    logger.error("UDM_IP env var not found")
    sys.exit(1)
if UDM_SWITCH_PORT is None:
    logger.error("UDM_SWITCH_PORT env var not found")
    sys.exit(1)
if UDM_USERNAME is None:
    logger.error("UDM_USERNAME env var not found")
    sys.exit(1)
if UDM_PASSWORD is None:
    logger.error("UDM_PASSWORD env var not found")
    sys.exit(1)

def init_udm_controller():
    """Inits the UDM controller object

    :returns: controller object
    :rtype: Controller
    """
    c = Controller(UDM_IP, UDM_USERNAME, UDM_PASSWORD, version='UDMP-unifiOS', ssl_verify=UDM_SSL_VERIFY)
    c.log = logger
    return c


def main():
    logger.info("Starting {tool_name}".format(tool_name=TOOL_NAME))

    # Quick sanity test to confirm we can contact and login to the UDM
    c = init_udm_controller()
    udm_mac = c.get_device_mac_by_ip(UDM_IP)

    logger.info("Found UDM Pro MAC address: {mac}".format(mac=udm_mac))

    logger.info("Getting switch port profile...")
    c.dump_switch_port_profile(udm_mac, UDM_SWITCH_PORT)


    logger.info("Exiting")

if __name__ == "__main__":
    main()