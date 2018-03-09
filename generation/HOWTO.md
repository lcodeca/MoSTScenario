##### Monaco SUMO Traffic (MoST) Scenario
Contacts: Lara CODECA [codeca@eurecom.fr], A-Team [a-team@eurecom.fr]
This project is licensed under the terms of the GPLv3 license.

## Mobility Generator

#### How to use it:
1) In [mobilitygen.trips.json](https://github.com/lcodeca/MoSTScenario/blob/master/generation/mobilitygen.trips.json) change the absolute path for `baseDir` and `outputPrefix` to reflect the location of your MoSTScenario folder.
2) Run it with `python3 mobilitygen.trips.py -c mobilitygen.trips.json`

#### What you can find the configuration file:
* `duarouterError`: the surplus of vehicles that have to be generated (even if the generation uses Dijkstra to check the possible origin-destination path, it's not always possible in SUMO)  
* `population`: absolute number of wanted vehicles-persons.
* `internal`: percentage of entities to be generate from `distribution`
* `external`: percentage of entities to be generate from `gateways`
* `taz`: TAZ definition, name matching from SUMO taz and human-readable TAZ in the configuration.
* `distribution`: dictionary containing the internal traffic demand.
Example:
```
"pedestrian": {                                         <-- vType or vTypeDistribution from SUMO
    "edges": "generation/taz/most.pedestrian.taz.xml",  <-- SUMO TAZ definition file
        "percentage": 0.25,                             <-- percentage of persons we want to generate (computed from the population)
        "withDUAerror": true,                           <-- does it has to take into account the surplus or not?
        "composition": {                                <-- composition of the OD definition for this vType
            "1": {
                "withPT": false,                        <-- With or without public transport
                "from": "MonacoArea1Detailed",          <-- from wich area
                "to": "MonacoArea1Detailed",            <-- to which area
                "perc": 0.3                             <-- percentage of persons that we want generated (computed from this vType)
            },
                "2": {
                    "withPT": true,
                    "from": "MonacoArea1Detailed",
                    "to": "MonacoArea1Detailed",
                    "perc": 0.2
                }
            }
        }
```
* `gateways`: dictionary containing the external traffic demand.
    * At the moment this section is very limitd and focused on inboud traffic, I will make it more generic soon.  
Example:
```
"vTypes": {                         <-- dictionary with vType: percentage
    "passenger": 0.60, 
    "other": 0.30,
    "evehicle": 0.10
    },
    "withDUAerror": true,
    "origin": {                     <-- dictionary conaining the origin EDGES divided by priority
        "primary": {
            "edges": ["430#0", "1420", "1613", "420"],
            "perc": 0.8
        },
        "secondary": {
            "edges": ["1378", "1394#0", "-1402", "451"],
            "perc": 0.2
        }
    },
    "destinationTAZ": {             <-- the destination must be a TAZ
        "name": "MonacoArea1Generic",
        "definition" : "generation/taz/most.passenger.taz.xml",
        "withPL": true              <-- with Parkin Lots (withPL) will have a parking lot as 
                                        destination and will wait until the end of the simulation
        }
    },
```
* `interval`: defines the `begin` and the `end` of the simulation to generate the departure times.
* `peak`: defines `mean` and `std` of a normal distribution, to generate the departure times.

NOTE: this tool is in its early stages, variables names and behaviour may (will) change in the future. I promise I'll keep you up to date.