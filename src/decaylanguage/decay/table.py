# Copyright (c) 2018-2026, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Submodule with classes and utilities to tabulate decay chains.
Decay chains are typically provided by the parser of .dec decay files,
see the ``DecFileParser`` class.
"""

from __future__ import annotations

import itertools

import pandas as pd
from particle.converters.bimap import DirectionalMaps

counter = iter(itertools.count())

_EvtGen2LatexNameMap, _Latex2EvtGenNameMap = DirectionalMaps("EvtGenName", "LaTexName")


class DecayChainToTable:
    """
    The class to tabulate a decay chain.

    Examples
    --------
    >>> dfp = DecFileParser('my-Dst-decay-file.dec')
    >>> dfp.parse()
    >>> chain = dfp.build_decay_chains('D*+')
    >>> df = DecayChainToTable(chain).table
    >>> df  # display the pandas in a notebook
    """

    __slots__ = ("_chain", "_df")

    def __init__(self, decaychain):
        """
        Default constructor.

        Parameters
        ----------
        decaychain: dict
            Input decay chain in dict format, typically created from `decaylanguage.DecFileParser.build_decay_chains`
            after parsing a .dec decay file, or from building a decay chain representation with `decaylanguage.DecayChain.to_dict`.

        See also
        --------
        decaylanguage.DecFileParser.build_decay_chains for creating a decay chain dict from parsing a .dec file.
        decaylanguage.DecFileParser: class for creating an input decay chain.
        """
        # Store the input decay chain
        self._chain = decaychain

        # Instantiate the digraph with defaults possibly overridden by user attributes
        self._df = pd.DataFrame(columns=["Decay", "BF"])

        # Build the actual graph from the input decay chain structure
        self._build_decay_graph()

    def _build_decay_graph(self):
        """
        Recursively navigate the decay chain tree and append to a pandas DataFrame.
        """

        def get_decay_str(prefix, mother, list_parts):
            # print(mother)
            if prefix is None:
                decay_str = mother + " --> " + " ".join(list_parts)
            else:
                decay_str = prefix + " ; " + mother + " --> " + " ".join(list_parts)

            return decay_str

        def iterate_chain(
            subchain,
            _eff_bf=1.0,
            _total_eff_bf=0.0,
            prefix=None,
            mother=None,
            _append=True,
        ):
            n_decaymodes = len(subchain)
            for idm in range(n_decaymodes):
                _list_parts = subchain[idm]["fs"]
                if not has_subdecay(_list_parts):
                    _bf = subchain[idm]["bf"]
                    _decay_str = get_decay_str(prefix, mother, _list_parts)
                    if _append:
                        new_row = {"Decay": _decay_str, "BF": _eff_bf * _bf}
                        self._df = pd.concat(
                            [self._df, pd.DataFrame([new_row])], ignore_index=True
                        )
                    _total_eff_bf += _eff_bf * _bf
                else:
                    _bf_1 = subchain[idm]["bf"]
                    _iter_eff_bf = 1.0
                    _c = 0
                    max_l = len([_p for _p in _list_parts if not isinstance(_p, str)])
                    daughters = [
                        _p if isinstance(_p, str) else next(iter(_p.keys()))
                        for _p in _list_parts
                    ]
                    _decay_str = get_decay_str(prefix, mother, daughters)
                    for _i, _p in enumerate(_list_parts):
                        if not isinstance(_p, str):
                            _k = next(iter(_p.keys()))
                            if _c == max_l - 1:
                                _total_eff_bf, _decay_str = iterate_chain(
                                    _p[_k],
                                    _eff_bf=_iter_eff_bf * _eff_bf * _bf_1,
                                    _total_eff_bf=_total_eff_bf,
                                    mother=_k,
                                    prefix=_decay_str,
                                )
                            else:
                                _iter_eff_bf, _decay_str = iterate_chain(
                                    _p[_k],
                                    _eff_bf=_iter_eff_bf * _eff_bf * _bf_1,
                                    _total_eff_bf=0,
                                    mother=_k,
                                    prefix=_decay_str,
                                    _append=False,
                                )
                            _c += 1

            return _total_eff_bf, _decay_str

        def has_subdecay(ds):
            return not all(isinstance(p, str) for p in ds)

        k = next(iter(self._chain.keys()))
        sc = self._chain[k]

        # Actually build the whole decay chain, iteratively
        _total_eff_bf, _decay_str = iterate_chain(sc, mother=k)

    @property
    def table(self):
        """
        Get the actual `pandas.DataFrame` object.
        The user now has full control ...
        """
        return self._df
