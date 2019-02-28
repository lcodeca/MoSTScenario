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
 Duration: 20270920ms
 Real time factor: 1.77594
 UPS: 62401.266839
Vehicles:
 Inserted: 47385
 Running: 30
 Waiting: 0
Teleports: 1919 (Collisions: 403, Jam: 428, Yield: 761, Wrong Lane: 327)
Emergency Stops: 25
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 1722
Statistics (avg):
 RouteLength: 8951.66
 Duration: 6677.38
 WaitingTime: 272.85
 TimeLoss: 520.93
 DepartDelay: 1.36
Pedestrian Statistics (avg of 29900 walks):
 RouteLength: 330.77
 Duration: 282.98
 TimeLoss: 41.66
Ride Statistics (avg of 45515 rides):
 WaitingTime: 53.46
 RouteLength: 8061.96
 Duration: 1144.00
 Bus: 5707
 Train: 3
 Bike: 3863
 Aborted: 0
 ```

 #### Eclipse SUMO Version 1.0.1
(Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG

```
Performance:
 Duration: 16993971ms
 Real time factor: 2.1184
 UPS: 71937.263751
Vehicles:
 Inserted: 47385
 Running: 29
 Waiting: 0
Teleports: 711 (Collisions: 395, Jam: 85, Yield: 117, Wrong Lane: 114)
Emergency Stops: 14
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 340
Statistics (avg):
 RouteLength: 7642.50
 Duration: 6453.27
 WaitingTime: 106.68
 TimeLoss: 267.06
 DepartDelay: 0.61
Pedestrian Statistics (avg of 29900 walks):
 RouteLength: 432.42
 Duration: 365.38
 TimeLoss: 50.29
Ride Statistics (avg of 45515 rides):
 WaitingTime: 43.71
 RouteLength: 6858.67
 Duration: 802.66
 Bus: 5707
 Train: 3
 Bike: 3863
 Aborted: 0
 ```