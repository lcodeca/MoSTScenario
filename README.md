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

#### Eclipse SUMO Version v1_1_0+0104-2560533423
(Build features: Linux-4.19.0-1-amd64 x86_64 GNU 8.2.0 Release Proj GUI GDAL FFmpeg OSG GL2PS SWIG)

```
Performance:
 Duration: 13032831ms
 Real time factor: 2.76225
 UPS: 93811.816328
Vehicles:
 Inserted: 47168 (Loaded: 47184)
 Running: 21
 Waiting: 0
Teleports: 3002 (Collisions: 460, Jam: 1139, Yield: 1041, Wrong Lane: 362)
Emergency Stops: 12
Persons:
 Inserted: 45000
 Running: 12
 Jammed: 1498
Statistics (avg):
 RouteLength: 7708.21
 Duration: 6482.75
 WaitingTime: 366.28
 TimeLoss: 606.14
 DepartDelay: 2.31
Pedestrian Statistics (avg of 29753 walks):
 RouteLength: 363.78
 Duration: 309.15
 TimeLoss: 43.77
Ride Statistics (avg of 45113 rides):
 WaitingTime: 64.07
 RouteLength: 6988.08
 Duration: 1159.79
 Bus: 5269
 Train: 12
 Bike: 4287
 Aborted: 0
 ```

#### Eclipse SUMO Version 1.1.0
(Build features: Linux-4.18.0-3-amd64 x86_64 GNU 8.2.0 Release Proj GUI GDAL FFmpeg OSG GL2PS SWIG)

```
Performance:
 Duration: 11674215ms
 Real time factor: 3.08372
 UPS: 103949.676188
Vehicles:
 Inserted: 47184
 Running: 21
 Waiting: 0
Teleports: 1674 (Collisions: 392, Jam: 601, Yield: 489, Wrong Lane: 192)
Emergency Stops: 14
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 1424
Statistics (avg):
 RouteLength: 8428.45
 Duration: 6432.30
 WaitingTime: 214.71
 TimeLoss: 423.43
 DepartDelay: 1.03
Pedestrian Statistics (avg of 29754 walks):
 RouteLength: 363.56
 Duration: 309.40
 TimeLoss: 44.19
Ride Statistics (avg of 45125 rides):
 WaitingTime: 57.35
 RouteLength: 7661.72
 Duration: 1030.23
 Bus: 5269
 Train: 12
 Bike: 4295
 Aborted: 0
 ```

 #### Eclipse SUMO Version 1.0.1
(Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG

```
Performance:
 Duration: 10603919ms
 Real time factor: 3.39497
 UPS: 112212.020197
Vehicles:
 Inserted: 47184
 Running: 22
 Waiting: 0
Teleports: 611 (Collisions: 227, Jam: 126, Yield: 151, Wrong Lane: 107)
Emergency Stops: 1
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 503
Statistics (avg):
 RouteLength: 7731.85
 Duration: 6307.08
 WaitingTime: 122.00
 TimeLoss: 285.57
 DepartDelay: 0.63
Pedestrian Statistics (avg of 29754 walks):
 RouteLength: 472.61
 Duration: 399.50
 TimeLoss: 54.48
Ride Statistics (avg of 45125 rides):
 WaitingTime: 52.24
 RouteLength: 7007.72
 Duration: 842.65
 Bus: 5269
 Train: 12
 Bike: 4295
 Aborted: 0
 ```