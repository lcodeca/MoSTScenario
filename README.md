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
 Duration: 18089164ms
 Real time factor: 1.99014
 UPS: 67928.112764
Vehicles:
 Inserted: 46713
 Running: 31
 Waiting: 0
Teleports: 1131 (Collisions: 326, Jam: 300, Yield: 340, Wrong Lane: 165)
Emergency Stops: 13
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 1188
Statistics (avg):
 RouteLength: 8029.64
 Duration: 6579.93
 WaitingTime: 160.17
 TimeLoss: 339.46
 DepartDelay: 0.82
Pedestrian Statistics (avg of 31532 walks):
 RouteLength: 341.99
 Duration: 291.11
 TimeLoss: 42.01
Ride Statistics (avg of 45252 rides):
 WaitingTime: 53.22
 RouteLength: 7150.60
 Duration: 894.30
 Bus: 6117
 Train: 2
 Bike: 3320
 Aborted: 0
 ```

 #### Eclipse SUMO Version 1.0.1
(Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)

```
Performance:
 Duration: 17122703ms
 Real time factor: 2.10247
 UPS: 70908.259695
Vehicles:
 Inserted: 46713
 Running: 31
 Waiting: 0
Teleports: 544 (Collisions: 315, Jam: 69, Yield: 87, Wrong Lane: 73)
Emergency Stops: 4
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 388
Statistics (avg):
 RouteLength: 7604.06
 Duration: 6501.62
 WaitingTime: 98.86
 TimeLoss: 250.29
 DepartDelay: 0.57
Pedestrian Statistics (avg of 31532 walks):
 RouteLength: 448.22
 Duration: 379.37
 TimeLoss: 52.56
Ride Statistics (avg of 45252 rides):
 WaitingTime: 48.32
 RouteLength: 6757.15
 Duration: 776.86
 Bus: 6117
 Train: 2
 Bike: 3320
 Aborted: 0

 ```

#### Eclipse SUMO Version 1.0.0
(Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)
 ```
 Performance:
 Duration: 17893508ms
 Real time factor: 2.0119
 UPS: 68134.365156
Vehicles:
 Inserted: 46713
 Running: 31
 Waiting: 0
Teleports: 961 (Collisions: 612, Jam: 90, Yield: 141, Wrong Lane: 118)
Emergency Stops: 6
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 404
Statistics (avg):
 RouteLength: 7781.16
 Duration: 6528.52
 WaitingTime: 124.25
 TimeLoss: 291.34
 DepartDelay: 0.63
Pedestrian Statistics (avg of 31532 walks):
 RouteLength: 448.62
 Duration: 379.78
 TimeLoss: 52.83
Ride Statistics (avg of 45252 rides):
 WaitingTime: 50.11
 RouteLength: 6924.03
 Duration: 832.12
 Bus: 6117
 Train: 2
 Bike: 3320
 Aborted: 0

 ```