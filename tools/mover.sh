#!/bin/bash

# Monaco SUMO Traffic (MoST) Scenario
# Author: Lara CODECA

cp -v out/most.net.xml      ../scenario/in/.
cp -v out/*stops*           ../scenario/in/add/.
cp -v out/*parking*         ../scenario/in/add/.
cp -v out/most.poly.xml     ../scenario/in/add/.
cp -v out/*.flows.xml       ../scenario/in/rou/.
cp -v out/*.rou.xml         ../scenario/in/rou/.
