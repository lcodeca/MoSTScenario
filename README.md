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

#### Eclipse SUMO Version 5345f89a38 (Build features: Linux-4.18.0-1-amd64 x86_64 GNU 8.2.0 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)
```
Performance:
 Duration: 14335221ms
 Real time factor: 2.5113
 UPS: 83421.788684
Vehicles:
 Inserted: 47232 (Loaded: 47233)
 Running: 23
 Waiting: 0
Teleports: 777 (Collisions: 190, Jam: 169, Yield: 270, Wrong Lane: 148)
Emergency Stops: 2
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 618
Statistics (avg):
 RouteLength: 7992.86
 Duration: 6332.43
 WaitingTime: 160.87
 TimeLoss: 345.51
 DepartDelay: 0.70
Pedestrian Statistics (avg of 29617 walks):
 RouteLength: 479.37
 Duration: 404.91
 TimeLoss: 55.53
Ride Statistics (avg of 45234 rides):
 WaitingTime: 46.57
 RouteLength: 7243.00
 Duration: 921.88
 Bus: 5331
 Train: 10
 Bike: 4335
 Aborted: 0
 ```

#### Eclipse SUMO Version 1.0.1 (Build features: Linux-4.18.0-1-amd64 Proj GUI GDAL FFmpeg OSG GL2PS SWIG)
```
Performance:
 Duration: 13923066ms
 Real time factor: 2.58564
 UPS: 85404.430245
Vehicles:
 Inserted: 47232 (Loaded: 47233)
 Running: 23
 Waiting: 0
Teleports: 727 (Collisions: 197, Jam: 130, Yield: 236, Wrong Lane: 164)
Emergency Stops: 1
Persons:
 Inserted: 45000
 Running: 0
 Jammed: 643
Statistics (avg):
 RouteLength: 7831.52
 Duration: 6296.54
 WaitingTime: 144.19
 TimeLoss: 318.86
 DepartDelay: 0.65
Pedestrian Statistics (avg of 29617 walks):
 RouteLength: 480.20
 Duration: 405.35
 TimeLoss: 55.40
Ride Statistics (avg of 45234 rides):
 WaitingTime: 46.21
 RouteLength: 7091.25
 Duration: 885.65
 Bus: 5331
 Train: 10
 Bike: 4335
 Aborted: 0
 ```