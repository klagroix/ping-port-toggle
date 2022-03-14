# ping-port-toggle
Continuously pings a device on the network. When connectivity is lost to the device, a switch port on the UDM Pro will be disabled and re-enabled

## Why?

I have an aging system that EoL which keeping on life support. There's some issue with the NIC/Drivers/OS which causes network connectivity to stop working. The easiest fix I have is to just unplug the network cable and re-plug it back in to get it working again. This tool (`ping-port-toggle`) automates this.

## How it works

It's pretty simple - look at `ping-port-toggle.py` and you'll see what it does. In short, it...
* Checks a target ip/hostname periodically using ping. If the target cannot be reached, a secondary ping to the UDM Pro is done as a sanity check to confirm we have *some* networking (i.e. to confirm the whole network isn't down or the device running ping-port-toggle isn't having issues).
* After a determined number of attempts, API calls are made to the UDM Pro to disable the switch port and re-enable it
* A backoff sleep time is triggered after a port toggle so we don't constantly flap the interface

## Setup

TODO:
* Instructions for setting up local UDM Pro user

## Usage

TODO:
```
docker run -d \
 --name=todoist-dedup \
 -e API_TOKEN=<APITOKEN> \
 -e PROJECT_NAME=<PROJECT> \
 jovocop/todoist-dedup
 ```

### Environment variables

TODO: 
* `API_TOKEN` - Your todoist API token. To retrieve this, open Todoist Settings -> Integrations -> API token
* `PROJECT_NAME` - The name of the project in todoist to deduplicate
* (optional) `IGNORE_CHECKED` - Default: True. Set to False if you want to deduplicate already checked items as well
* (optional) `RUN_FREQUENCY_MIN` - Default: 10. Change this to the desired check interval (in minutes)

##  Build

TODO
GitLab CI automatically deploys new containers to https://hub.docker.com/repository/docker/jovocop/todoist-dedup

To build this manually, run `docker build -t todoist-dedup .`


## Libraries
Third Party libraries required are documented in `requirements.txt`

## License
TODO