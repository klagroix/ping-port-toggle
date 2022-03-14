import json
import sys
import os
import platform
import subprocess
import time
from loguru import logger
from pprint import pprint
from pyunifi.controller import Controller
from prometheus_client import start_http_server, Counter

# Setup logging
DEBUG=os.getenv("DEBUG", default='False').lower() in ('true', '1', 't')
logging_level = "INFO"
if DEBUG:
    logging_level = "DEBUG"
logger.remove()
logger.add(sys.stderr, colorize=True, format="<green>{time}</green> - {name}:{function}:{line} - <level>{message}</level>", level=logging_level)

# Static
TOOL_NAME = "ping-port-toggle"

# Required env vars...
MONITOR_IP=os.getenv("MONITOR_IP") # This is the IP to ping. If we don't have conectiity to this, we need to restart the switch port
UDM_IP=os.getenv("UDM_IP")
UDM_SWITCH_PORT=int(os.getenv("UDM_SWITCH_PORT"))
UDM_USERNAME=os.getenv("UDM_USERNAME")
UDM_PASSWORD=os.getenv("UDM_PASSWORD")
UDM_ENABLED_PORT_CONF_ID=os.getenv("UDM_ENABLED_PORT_CONF_ID") #60d91905f99d8d06938cdce6
UDM_DISABLED_PORT_CONF_ID=os.getenv("UDM_DISABLED_PORT_CONF_ID") #60d91905f99d8d06938cdce7

# Optional env vars...
UDM_SSL_VERIFY=os.getenv("UDM_SSL_VERIFY", default='True').lower() in ('true', '1', 't')
CHECK_INTERVAL_SEC=int(os.getenv("CHECK_INTERVAL_SEC", default=5))
CHECK_ATTEMPTS=int(os.getenv("CHECK_INTERVAL_SEC", default=3)) # (CHECK_INTERVAL_SEC * CHECK_ATTEMPTS) = how long we'll wait before deeming the device to be offline
ENABLE_DELAY_SEC=int(os.getenv("CHECK_INTERVAL_SEC", default=2)) # How long to wait between disabling the port and re-enalble
BACKOFF_AFTER_TOGGLE_SEC=int(os.getenv("BACKOFF_AFTER_TOGGLE_SEC", default=30)) # How long to sleep after a toggle before checking for activity again
SHOW_ACTIVITY=os.getenv("DEBUG", default='True').lower() in ('true', '1', 't') # Whether to show if a device is online or offline between sleeps
PROMETHEUS_PORT=int(os.getenv("PROMETHEUS_PORT", default=9000)) # Port to listen on for Prometheus metrics

# Verify args
if MONITOR_IP is None:
    logger.error("MONITOR_IP env var not found")
    sys.exit(1)
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
if UDM_ENABLED_PORT_CONF_ID is None:
    logger.error("UDM_ENABLED_PORT_CONF_ID env var not found")
    sys.exit(1)
if UDM_DISABLED_PORT_CONF_ID is None:
    logger.error("UDM_DISABLED_PORT_CONF_ID env var not found")
    sys.exit(1)



def ping(host):
    """Pings a host

    :param host: Host/IP to ping
    :type host: str

    :returns: True if we can ping the host, false if not
    :rtype: bool
    """
    parameter = '-n' if platform.system().lower()=='windows' else '-c'

    command = ['ping', parameter, '1', host]
    response = subprocess.call(command, stdout=subprocess.DEVNULL)

    if response == 0:
        return True
    else:
        return False

def init_udm_controller():
    """Inits the UDM controller object

    :returns: controller object
    :rtype: Controller
    """
    c = Controller(UDM_IP, UDM_USERNAME, UDM_PASSWORD, version='UDMP-unifiOS', ssl_verify=UDM_SSL_VERIFY)
    c.log = logger
    return c

def toggle_switch_port(enable):
    """Enables or disables a switch port on the UDM Pro

    :param enable: Whether to enable or disable the port. True = Enable, False = Disable
    :type enable: bool

    :returns: None
    :rtype: None
    """
    c = init_udm_controller()

    udm_mac = c.get_device_mac_by_ip(UDM_IP)

    if udm_mac is None:
        logger.error("Unable to find device with IP {ip}".format(ip=UDM_IP))
        sys.exit(1)

    logger.info('Found UDM Pro with MAC {mac} and IP {ip}'.format(mac=udm_mac, ip=UDM_IP))

    logger.debug("Switch port profile dump...")
    logger.debug(c.dump_switch_port_profile(udm_mac, UDM_SWITCH_PORT))

    if enable:
        logger.info("Attempting to enable the port...")
        logger.info(c.set_port_conf(udm_mac, UDM_SWITCH_PORT, UDM_ENABLED_PORT_CONF_ID))
    else:
        logger.info("Attempting to disable the port...")
        logger.info(c.set_port_conf(udm_mac, UDM_SWITCH_PORT, UDM_DISABLED_PORT_CONF_ID))

    logger.info("Done")



def main():
    logger.info("Starting {tool_name}".format(tool_name=TOOL_NAME))

    # Init the prometheus metrics
    restart_counter = Counter('udm_port_restarts', 'Number of times the UDM Pro switch port has been disabled and re-enabled due to connectivity loss')
    start_http_server(PROMETHEUS_PORT)

    # Quick sanity test to confirm we can contact and login to the UDM
    c = init_udm_controller()
    udm_mac = c.get_device_mac_by_ip(UDM_IP)

    logger.info("Found UDM Pro MAC address: {mac}".format(mac=udm_mac))



    # Ping continuously
    attempts = 0
    online = True
    port_enabled = True
    try:
        while True:
            time.sleep(CHECK_INTERVAL_SEC)
            
            try:
                if not ping(MONITOR_IP):

                    if not ping(UDM_IP):
                        logger.error("It appears we're offline or the network is down as we cannot ping {ip} and {udm_ip}".format(ip=MONITOR_IP, udm_ip=UDM_IP))
                        continue

                    # We cannot ping the IP
                    online = False
                    attempts += 1
                    logger.info("IP {ip} IS OFFLINE!!! Attempt {attempt}/{max_attempts}".format(ip=MONITOR_IP, attempt=attempts, max_attempts=CHECK_ATTEMPTS))
                    
                else:
                    # The device is online
                    online = True
                    attempts = 0

                if SHOW_ACTIVITY:
                    logger.info("{ip} is {status}".format(ip=MONITOR_IP, status="online" if online else "offline"))
                
                # If the IP we're watching is offline and we've reached out max attempts, we should stop the port
                if not online and attempts >= CHECK_ATTEMPTS:
                    logger.info("We've reached our max attempts. Attempting to disable port")
                    toggle_switch_port(False)

                    logger.info("Waiting {delay}s before re-enabling".format(delay=ENABLE_DELAY_SEC))
                    time.sleep(ENABLE_DELAY_SEC)

                    logger.info("Enabling port")
                    toggle_switch_port(True)

                    logger.info("Toggle complete. Setting attempts back to 0 and entering wait time of {wait_sec}s before checking again".format(wait_sec=BACKOFF_AFTER_TOGGLE_SEC))
                    restart_counter.inc()
                    online = True
                    attempts = 0
                    time.sleep(BACKOFF_AFTER_TOGGLE_SEC)
                
            except OSError:
                logger.error("Caught OSError exception. Likely due to OS networking going offline")



    except KeyboardInterrupt:
        logger.warning('Caught Keyboard Intterrupt')

    logger.info("Exiting (graceful)")

if __name__ == "__main__":
    main()