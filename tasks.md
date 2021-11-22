# Possible improvements

[] Normalize BF after parsing (In DEC file you only need to give relative BF, so just parsing is not enough)
[] Allow `ModelAlias` keyword now present in Belle II DEC file
[] Fix problems parsing Belle DEC file: No modes between `Decay A` and `EndDecay` for some particles. Just skip them in parsing
[] Add feature in DecayChainViewer to show effective BF
[] Write to DEC file (it is sometimes easier to edit the python dictionary than the DEC file
[] Inclusive decays
[] Compare Belle and LHCb DEC files (they deal with \eta better than us?)
[] Build a parser for PDG Json file for easier comparision with DEC file. See a pattern in the way particle names are defined as a mother vs as a daughter
