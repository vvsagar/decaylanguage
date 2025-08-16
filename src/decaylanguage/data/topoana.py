#!/usr/bin/env python3

import os
import basf2
from generators import add_evtgen_generator
from modularAnalysis import variablesToNtuple
from variables.MCGenTopo import mc_gen_topo

# set random seed
basf2.set_random_seed(42)

# main path
main = basf2.create_path()

# event info setter
main.add_module("EventInfoSetter", expList=0, runList=1, evtNumList=10000)

# EvtGen
add_evtgen_generator(path=main, finalstate='charged')

# Output the variables to a ntuple
variablesToNtuple('', mc_gen_topo(200), 'MCGenTopo', 'MCGenTopo.root', path=main)

# run
main.add_module("Progress")

# generate events
basf2.process(main, calculateStatistics=True)

# show call statistics
print(basf2.statistics)

# Invoke the TopoAna program
#os.system('topoana.exe topoana.card')  # Newly added statement 2!
