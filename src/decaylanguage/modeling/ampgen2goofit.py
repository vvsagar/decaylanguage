#!/usr/bin/env python
# Copyright (c) 2018-2024, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Function that takes a filename of an AmpGen options file and either prints out or returns
a string output with the converted set of decay chains and variables.
The output is either C++ code (ampgen2goofit) or a Python script (ampgen2goofitpy)
"""


from __future__ import annotations

import datetime
from functools import partial
from io import StringIO

from particle import SpinType
from plumbum import colors

from decaylanguage.modeling.goofit import GooFitChain, GooFitPyChain, SF_4Body


def ampgen2goofit(filename, ret_output=False):
    """
    Converts an AmpGen options file to GooFit C++ code.

    Parameters
    ----------
    filename: string
        Name of AmpGen options file.
    ret_output: bool
       If True, return output as string. Otherwise print it to terminal.
    """
    if ret_output:
        output = StringIO()
        printer = partial(print, file=output)
    else:
        printer = print

    lines, all_states = GooFitChain.read_ampgen(str(filename))

    printer(r"/* Autogenerated file by AmpGen2GooFit")
    printer("Generated on ", datetime.datetime.now())

    printer("\n")
    for seen_factor in {p.spindetails() for p in lines}:
        my_lines = [p for p in lines if p.spindetails() == seen_factor]
        printer(colors.bold | seen_factor, ":", *my_lines[0].spinfactors)
        for line in my_lines:
            printer(" ", colors.blue | str(line))

    printer("\n")
    for spintype in SpinType:
        ps = [
            format(str(p), "11")
            for p in sorted(GooFitChain.all_particles)
            if p.spin_type == spintype
        ]
        printer(f"{spintype.name:>12}:", *ps)

    printer("\n")
    for n, line in enumerate(lines):
        printer(
            "{n:2} {line!s:<70} spinfactors: {lensf}  L: {line.L} [{Lr[0]}-{Lr[1]}]".format(
                n=n, line=line, lensf=len(line.spinfactors), Lr=line.L_range()
            )
        )

    # We can make the GooFit Intro code:

    printer(colors.bold & colors.green | "\n\nAll discovered spin configurations:")

    for line in sorted({iline.spindetails() for iline in lines}):
        printer(colors.green | line)

    printer(colors.bold & colors.blue | "\n\nAll known spin configurations:")

    # TODO: 4 body only
    for e in SF_4Body:
        printer(colors.blue | e.name)

    printer("\n*/\n\n    // Intro")
    printer(GooFitChain.make_intro(all_states))

    printer("\n\n    // Parameters")
    printer(GooFitChain.make_pars())

    # And the lines can be turned into code, as well:

    printer("\n\n    // Lines")
    for n, line in enumerate(lines):
        printer("    // Line", n)
        printer(line.to_goofit(all_states[1:]), end="\n\n\n")

    if ret_output:
        return output.getvalue()
    return None


def ampgen2goofitpy(filename, ret_output=False):
    """
    Converts an AmpGen options file to a GooFit Python script.

    Parameters
    ----------
    filename: string
        Name of AmpGen options file.
    ret_output: bool
       If True, return output as string. Otherwise print it to terminal.
    """
    if ret_output:
        output = StringIO()
        printer = partial(print, file=output)
    else:
        printer = print

    lines, all_states = GooFitPyChain.read_ampgen(str(filename))

    printer(r"'''")
    printer("\nAutogenerated file by AmpGen2GooFit\n")
    printer("Generated on ", datetime.datetime.now())

    printer("\n")
    for seen_factor in {p.spindetails() for p in lines}:
        my_lines = [p for p in lines if p.spindetails() == seen_factor]
        printer(colors.bold | seen_factor, ":", *my_lines[0].spinfactors)
        for line in my_lines:
            printer(" ", colors.blue | str(line))

    printer("\n")
    for spintype in SpinType:
        ps = [
            format(str(p), "11")
            for p in sorted(GooFitPyChain.all_particles)
            if p.spin_type == spintype
        ]
        printer(f"{spintype.name:>12}:", *ps)

    printer("\n")
    for n, line in enumerate(lines):
        printer(
            "{n:2} {line!s:<70} spinfactors: {lensf}  L: {line.L} [{Lr[0]}-{Lr[1]}]".format(
                n=n, line=line, lensf=len(line.spinfactors), Lr=line.L_range()
            )
        )

    # We can make the GooFit Intro code:

    printer(colors.bold & colors.green | "\n\nAll discovered spin configurations:")

    for line in sorted({iline.spindetails() for iline in lines}):
        printer(colors.green | line)

    printer(colors.bold & colors.blue | "\n\nAll known spin configurations:")

    # TODO: 4 body only
    for e in SF_4Body:
        printer(colors.blue | e.name)

    print("\n")
    printer(r"'''")
    print("\n#Intro \n")
    printer(GooFitPyChain.make_intro(all_states))

    printer("\n\n# Parameters")
    printer(GooFitPyChain.make_pars())

    # And the lines can be turned into code, as well:

    printer("\n\n# Lines")
    for n, line in enumerate(lines):
        printer("# Line", n)
        printer(line.to_goofit(all_states[1:]), end="\n\n\n")
    print("DK3P_DI.amplitudes = amplitudes_list")

    if ret_output:
        return output.getvalue()
    return None
