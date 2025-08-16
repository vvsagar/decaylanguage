==================
Usage with Topoana
==================

DecFiles
--------

When all possible decays are not well known/understood/measured, instead of explicitly writing the decays in the DecFiles, `pythia`_ is called to perform hadronization like this:

In the case of B mesons or even heavier particles, this is often the case and studyinf DecFiles only provides a partial information. In order to study all the possible/happening decays in the simulation, one has to produce a few events first and extract the decay information using additional tools. One popular generic tool for this purpose is `topoana`_. See `tutorial in Belle II`_ for how to use it and produce the `.txt` files. These files can then be read by `DecayLanguage` and queries just like DecFiles.

.. pythia: https://pythia.org/ 
.. topoana: https://github.com/buaazhouxingyu/topoana
.. tutorial in Belle II: https://software.belle2.org/development/sphinx/analysis/doc/MCMatching.html#topology-analysis
