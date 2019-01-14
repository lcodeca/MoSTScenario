## Monaco SUMO Traffic (MoST) Scenario

Contacts: Lara CODECA [codeca@eurecom.fr], A-Team [a-team@eurecom.fr]
This project is licensed under the terms of the GPLv3 license.

MoST Scenario is meant to be used with SUMO (Simulator of Urban MObility).
* It has been tested with [SUMO 1.0.1](https://github.com/eclipse/sumo/tree/v1_0_1) and [SUMO 1.1.0](https://github.com/eclipse/sumo/tree/v1_1_0).
* In case there are problems with multi-threading, check that [Issue #4518](https://github.com/eclipse/sumo/issues/4518) has been solved in your target version.

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
* Tianshu Chu, Civil and Environmental Engineering, Stanford University

If you are using MoST Scenario, or its tools to generate a new one, we would gladly add you to the list.
You can send an e-mail to codeca@eurecom.fr with your name and affiliation (if any).

### Tested with:

#### Eclipse SUMO Version 1.1.0
(Build features: Linux-4.18.0-3-amd64 x86_64 GNU 8.2.0 Release Proj GUI GDAL FFmpeg OSG GL2PS SWIG)

```
Performance:
 Duration: 9258106ms
 Real time factor: 3.88848
 UPS: 128964.872837
Vehicles:
 Inserted: 47242
 Running: 21
 Waiting: 0
Teleports: 1039 (Collisions: 255, Jam: 403, Yield: 287, Wrong Lane: 94)
Emergency Stops: 7
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 1089
Statistics (avg):
 RouteLength: 7555.05
 Duration: 6320.84
 WaitingTime: 115.05
 TimeLoss: 258.16
 DepartDelay: 0.71
Pedestrian Statistics (avg of 29831 walks):
 RouteLength: 360.16
 Duration: 306.80
 TimeLoss: 43.57
Ride Statistics (avg of 45005 rides):
 WaitingTime: 51.35
 RouteLength: 6857.66
 Duration: 800.87
 Bus: 5091
 Train: 12
 Bike: 4256
 Aborted: 0
 ```

 #### Eclipse SUMO Version 1.0.1
(Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG

```
Performance:
 Duration: 9946949ms
 Real time factor: 3.6192
 UPS: 119804.583999
Vehicles:
 Inserted: 47242
 Running: 21
 Waiting: 0
Teleports: 744 (Collisions: 163, Jam: 303, Yield: 188, Wrong Lane: 90)
Emergency Stops: 6
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 562
Statistics (avg):
 RouteLength: 7622.53
 Duration: 6308.76
 WaitingTime: 118.44
 TimeLoss: 274.66
 DepartDelay: 0.57
Pedestrian Statistics (avg of 29831 walks):
 RouteLength: 460.78
 Duration: 390.55
 TimeLoss: 54.01
Ride Statistics (avg of 45005 rides):
 WaitingTime: 49.10
 RouteLength: 6926.28
 Duration: 823.98
 Bus: 5091
 Train: 12
 Bike: 4256
 Aborted: 0

 ```