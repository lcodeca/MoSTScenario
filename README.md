## Monaco SUMO Traffic (MoST) Scenario

Contacts: Lara CODECA [codeca@eurecom.fr], A-Team [a-team@eurecom.fr]
This project is licensed under the terms of the GPLv3 license.

MoST Scenario is meant to be used with SUMO (Simulator of Urban MObility).
* Version 0.3 has been tested with [SUMO 1.0](https://github.com/eclipse/sumo/tree/v1_0_0).
* Due to [Issue #4518](https://github.com/eclipse/sumo/issues/4518) it requires the development
  version of [SUMO](https://github.com/eclipse/sumo.git) in order to use multi-threading.

Please refer to the [SUMO wiki](http://sumo.dlr.de/wiki/Simulation_of_Urban_MObility_-_Wiki) for further information on the simulator itself.

#### How to cite it: [BibTeX](https://github.com/lcodeca/MoSTScenario/blob/master/cite.bib)
L. Codeca, J. Härri,
*"Towards Multimodal Mobility Simulation of C-ITS: The Monaco SUMO Traffic Scenario"*
VNC 2017, IEEE Vehicular Networking Conference
November 27-29, 2017, Torino, Italy.

or

L. Codeca, J. Härri,
*"Monaco SUMO Traffic (MoST) Scenario: A 3D Mobility Scenario for Cooperative ITS"*
SUMO 2018, SUMO User Conference, Simulating Autonomous and Intermodal Transport Systems
May 14-16, 2018, Berlin, Germany

### How To:
MoST Scenario can be lunched directly with its configuration file.
* `sumo -c most.sumocfg` or `run.sh` from the _scenario_ folder.

To use the scrips in the `tools` directory it's necessary to exec `source setenv.sh`.
#### See [Scenario re-genration](https://github.com/lcodeca/MoSTScenario/wiki/How-to-rebuild-the-scenario.)

#### Files:
* `scenario` is the ready-to-use scenario
* `tools/mobility` contains the files required to generate various traffic demands.
* `tools/parkings` contains the an example of parking mornitoring done with [PyPML](https://github.com/lcodeca/PyPML).
* `tools/static` contains the raw OSM-like file, scripts, and configuration files to regenerate the scenario from the beginning.

Note: the configuration files contained in `tools/static/typemap` are a slightly modified version of a subset of the SUMO files available at https://github.com/eclipse/sumo/tree/master/data/typemap.

#### Mobility Example
[![Mobility Example](https://img.youtube.com/vi/nFVhodnJKws/0.jpg)](https://www.youtube.com/watch?v=nFVhodnJKws)
(click on the image for the video)

#### Traffic Light Example
[![Traffic Light Example](https://img.youtube.com/vi/Wwp_riSsLAs/0.jpg)](https://www.youtube.com/watch?v=Wwp_riSsLAs)
(click on the image for the video)

#### Public Transportation Example
[![Public Transportation Example](https://img.youtube.com/vi/r7iE3LRiSNA/0.jpg)](https://www.youtube.com/watch?v=r7iE3LRiSNA)
(click on the image for the video)

### Users:
* Vincent Terrier, Aerospace System Design Laboratory, Georgia Institute of Technology, Atlanta, GA 30332-0105

If you are using MoST Scenario, or its tools to generate a new one, we would gladly add you to the list.
You can send an e-mail to codeca@eurecom.fr with your name and affiliation (if any).

### Tested with:

#### Eclipse SUMO Version 5345f89a38 (Build features: Linux-4.17.0-1-amd64 x86_64 GNU 8.2.0 Release Proj GUI GDAL FFmpeg OSG GL2PS SWIG)
```
Performance:
 Duration: 8872758ms
 Real time factor: 4.05736
 UPS: 133877.978978
Vehicles:
 Inserted: 47283
 Running: 22
 Waiting: 0
Teleports: 835 (Collisions: 384, Jam: 142, Yield: 187, Wrong Lane: 122)
Emergency Stops: 1
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 492
Statistics (avg):
 RouteLength: 7622.57
 Duration: 6283.18
 WaitingTime: 120.51
 TimeLoss: 278.01
 DepartDelay: 0.61
Pedestrian Statistics (avg of 29541 walks):
 RouteLength: 472.38
 Duration: 398.49
 TimeLoss: 54.52
Ride Statistics (avg of 45181 rides):
 WaitingTime: 51.21
 RouteLength: 6916.92
 Duration: 832.03
 Bus: 5223
 Train: 15
 Bike: 4409
 Aborted: 0
 ```

#### Eclipse SUMO Version 1.0.1 (Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)
```
Performance:
 Duration: 11921949ms
 Real time factor: 3.01964
 UPS: 99541.035027
Vehicles:
 Inserted: 47283
 Running: 22
 Waiting: 0
Teleports: 679 (Collisions: 271, Jam: 132, Yield: 140, Wrong Lane: 136)
Emergency Stops: 1
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 580
Statistics (avg):
 RouteLength: 7673.19
 Duration: 6277.13
 WaitingTime: 122.32
 TimeLoss: 283.79
 DepartDelay: 0.59
Pedestrian Statistics (avg of 29541 walks):
 RouteLength: 472.06
 Duration: 398.11
 TimeLoss: 54.46
Ride Statistics (avg of 45181 rides):
 WaitingTime: 51.49
 RouteLength: 6961.77
 Duration: 838.20
 Bus: 5223
 Train: 15
 Bike: 4409
 Aborted: 0
 ```