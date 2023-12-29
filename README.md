# ping-port-toggle
Continuously pings a device on the network. When connectivity is lost to the device, a switch port on the UDM Pro will be disabled and re-enabled

*This has only been tested with the UDM Pro.*

> **_NOTE:_** If you recently upgraded to the Unifi OS, you may need to reconfigure your port profiles. When I updated my OS version, `portconf_id` no longer existed in the API responses. I had to re-create my port profiles and re-assign them to the ports. I'm not sure if this is a bug or not, but it's worth noting. Profiles can be added here: https://IP/network/default/settings/profiles/ethernet-ports/form. After setting the profiles, follow the 'Get the port profile configuration IDs for enabled and disabled ports' section below

## Why?

I have an aging system that EoL which keeping on life support. There's some issue with the NIC/Drivers/OS which causes network connectivity to stop working. The easiest fix I have is to just unplug the network cable and re-plug it back in to get it working again. This tool (`ping-port-toggle`) automates this.

## How it works

It's pretty simple - look at `ping-port-toggle.py` and you'll see what it does. In short, it...
* Checks a target ip/hostname periodically using ping. If the target cannot be reached, a secondary ping to the UDM Pro is done as a sanity check to confirm we have *some* networking (i.e. to confirm the whole network isn't down or the device running ping-port-toggle isn't having issues).
* After a determined number of attempts, API calls are made to the UDM Pro to disable the switch port and re-enable it
* A backoff sleep time is triggered after a port toggle so we don't constantly flap the interface

## Setup

### Create a UDM Pro local user
In order to toggle the switch port, we need a user on the UDM Pro that has permissions to administer the device. To create the user, follow these instructions:
1. Navigate to https://unifi.ui.com/
2. Click on the UDM Pro
3. Click 'Users' on the left
4. Click 'Add Users' at the top right
5. Select 'Local Access Only' in the Account Type dropdown and 'Limited Admin' as the Role
6. Enter any First/Last Name, Username, and Password. The username and passwod will be provided to ping-port-toggle later.
8. Under Application Permissions, select 'Administrator' under the Unifi Network application. Choose 'None' for all other applications.
9. Click the 'Add' button. Note the username and password for later use.

### Get the port profile configuration IDs for enabled and disabled ports

In order toggle the port between a disabled and enabled state, we need to know the port configuration ID that's used for each state. It's recommended you perform the following steps in a Python virtualenv.

1. On a shell that supports python3, set the environment variables `UDM_IP`, `UDM_SWITCH_PORT`, `UDM_USERNAME`, and `UDM_PASSWORD`. Definitions for these are below.
2. Run `pip install -r requirements.txt` to install the requirements
3. With the desired `UDM_SWITCH_PORT` enabled, run `python3 utilities/get-port-configuration-id.py`. Note the ouput 'Port Configuration ID'. This will be used for the `UDM_ENABLED_PORT_CONF_ID` environment variable
4. Disable the UDM switch port (in the Unifi console, find your UDM Pro, click Settings, click the port, select 'Disabled' as the port profile)
5. Run `python3 utilities/get-port-configuration-id.py` again. Note the ouput 'Port Configuration ID'. This will be used for the `UDM_DISABLED_PORT_CONF_ID` environment variable

## Usage

```
docker run -d \
 --name=ping-port-toggle \
 -p 9000:9000 \
 -e MONITOR_IP=<MONITOR_IP> \
 -e UDM_IP=<UDM_IP> \
 -e UDM_SWITCH_PORT=<UDM_SWITCH_PORT> \
 -e UDM_USERNAME=<UDM_USERNAME> \
 -e UDM_PASSWORD=<UDM_PASSWORD> \
 -e UDM_ENABLED_PORT_CONF_ID=<UDM_ENABLED_PORT_CONF_ID> \
 -e UDM_DISABLED_PORT_CONF_ID=<UDM_DISABLED_PORT_CONF_ID> \
 lagroix/ping-port-toggle
 ```

### Environment variables

* `MONITOR_IP` - The IP to continuously ping
* `UDM_IP` - The IP/Hostname of the UDM Pro
* `UDM_SWITCH_PORT` - The Port to enable/disable this is the same port number that shows in the UniFi UI
* `UDM_USERNAME` - The username created in the 'Setup' step above
* `UDM_PASSWORD` - The password created in the 'Setup' step above
* `UDM_ENABLED_PORT_CONF_ID` - The configuration ID for the port profile that's normally in use. To get this, see the 'Setup' step above.
* `UDM_DISABLED_PORT_CONF_ID` - The configuration ID for the port profile that's used to disable the port. To get this, see the 'Setup' step above.
* (optional) `UDM_SSL_VERIFY` - Default: True. Set to False if you want to skip SSL verification when attempting to access the UDM Pro API. You should set this to `False` if you're using a self-signed cert
* (optional) `DEBUG` - Default: False. Set to True to enable debug logging
* (optional) `CHECK_INTERVAL_SEC` - Default: 5. This is the numbe of seconds to sleep between pings
* (optional) `CHECK_ATTEMPTS` - Default: 3. (CHECK_INTERVAL_SEC * CHECK_ATTEMPTS) = how long we'll wait before deeming the device to be offline
* (optional) `ENABLE_DELAY_SEC` - Default: 2. How long to wait between disabling the port and re-enable
* (optional) `BACKOFF_AFTER_TOGGLE_SEC` - Default: 30. How long to sleep after a toggle before checking for activity again
* (optional) `SHOW_ACTIVITY` - Default: True. Whether to show ping results every CHECK_INTERVAL_SEC. Set to False if we're too chatty
* (optional) `PROMETHEUS_PORT` - Default: 9000. Port to listen on for Prometheus metric requests


## Metrics

Prometheus metrics are exposed to the `PROMETHEUS_PORT`. Metrics exposed are as follows:
* `udm_port_restarts` - Counter showing the number of times the UDM Pro switch port has been restarted


##  Build

Build is automated through GitHub Actions upon a release being made. Simply create a release and wait for the actions to publish to Docker Hub: [lagroix/ping-port-toggle](https://hub.docker.com/repository/docker/lagroix/ping-port-toggle)

To build this manually, run `docker build -t ping-port-toggle .`


## Libraries
Third Party libraries required are documented in `requirements.txt`
