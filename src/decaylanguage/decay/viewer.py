# Copyright (c) 2018-2022, Eduardo Rodrigues and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/decaylanguage for details.

"""
Submodule with classes and utilities to visualize decay chains.
Decay chains are typically provided by the parser of .dec decay files,
see the `DecFileParser` class.
"""

import itertools

import graphviz
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps

import pandas

counter = iter(itertools.count())


_EvtGen2LatexNameMap, _Latex2EvtGenNameMap = DirectionalMaps("EvtGenName", "LaTexName")


class GraphNotBuiltError(RuntimeError):
    pass


class DecayChainViewer:
    """
    The class to visualize a decay chain.

    Examples
    --------
    >>> dfp = DecFileParser('my-Dst-decay-file.dec')
    >>> dfp.parse()
    >>> chain = dfp.build_decay_chains('D*+')
    >>> dcv = DecayChainViewer(chain)
    >>> dcv  # display the SVG figure in a notebook

    When not in notebooks the graph can easily be visualized with the
    `graphviz.dot.Digraph.render` or `graphviz.dot.Digraph.view` functions, e.g.:
    >>> dcv.graph.render(filename="test", format="pdf", view=True, cleanup=True)
    """

    __slots__ = ("_chain", "_graph", "_graph_attributes")

    def __init__(self, decaychain, **attrs):
        """
        Default constructor.

        Parameters
        ----------
        decaychain: dict
            Input decay chain in dict format, typically created from `decaylanguage.DecFileParser.build_decay_chains`
            after parsing a .dec decay file, or from building a decay chain representation with `decaylanguage.DecayChain.to_dict`.
        attrs: optional
            User input `graphviz.dot.Digraph` class attributes.

        See also
        --------
        decaylanguage.DecFileParser.build_decay_chains for creating a decay chain dict from parsing a .dec file.
        decaylanguage.DecFileParser: class for creating an input decay chain.
        """
        # Store the input decay chain
        self._chain = decaychain

        # Instantiate the digraph with defaults possibly overridden by user attributes
        self._graph = self._instantiate_graph(**attrs)

        # Build the actual graph from the input decay chain structure
        self._build_decay_graph()

    def _build_decay_graph(self):
        """
        Recursively navigate the decay chain tree and produce a Digraph
        in the DOT language.
        """

        def safe_html_name(name):
            """
            Get a safe HTML name from the EvtGen name.

            Note
            ----
            The match is done using a conversion map rather than via
            `Particle.from_evtgen_name(name).html_name` for 2 reasons:
            - Some decay-file-specific "particle" names (e.g. cs_0)
              are not in the PDG table.
            - No need to load all particle information if all that's needed
              is a match EvtGen - HTML name.
            """
            try:
                return latex_to_html_name(_EvtGen2LatexNameMap[name])
            except Exception:
                return name

        def html_table_label(names, add_tags=False, bgcolor="#9abad6"):
            if add_tags:
                label = (
                    '<<TABLE BORDER="0" CELLSPACING="0" BGCOLOR="{bgcolor}">'.format(
                        bgcolor=bgcolor
                    )
                )
            else:
                label = '<<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="0" BGCOLOR="{bgcolor}"><TR>'.format(
                    bgcolor=bgcolor
                )
            for i, n in enumerate(names):
                if add_tags:
                    label += '<TR><TD BORDER="1" CELLPADDING="5" PORT="p{tag}">{name}</TD></TR>'.format(
                        tag=i, name=safe_html_name(n)
                    )
                else:
                    label += '<TD BORDER="0" CELLPADDING="2">{name}</TD>'.format(
                        name=safe_html_name(n)
                    )
            label += "{tr}</TABLE>>".format(tr="" if add_tags else "</TR>")
            return label

        def new_node_no_subchain(list_parts, _eff_bf, _show_eff=True):
            label = html_table_label(list_parts, bgcolor="#eef3f8")
            r = f"dec{next(counter)}"
            r_bf = f"bf{next(counter)}"
            self.graph.node(r, label=label, style="filled", fillcolor="#eef3f8")
            if _show_eff:
                self.graph.node(
                    r_bf,
                    label=f"  {_eff_bf:.2E}",
                    shape="plain",
                    fontcolor="#ff6000",
                    fontsize="12",
                )
                self.graph.edge(r, r_bf, arrowhead="none", style="dotted", color="#ff6000")
            return r

        def new_node_with_subchain(list_parts):
            list_parts = [
                list(p.keys())[0] if isinstance(p, dict) else p for p in list_parts
            ]
            label = html_table_label(list_parts, add_tags=True)
            r = f"dec{next(counter)}"
            self.graph.node(r, shape="none", label=label)
            return r

        def iterate_chain(
            subchain, top_node=None, link_pos=None, _eff_bf=1.0, _total_eff_bf=0.0,
            _show_eff=True
        ):
            if not top_node:
                top_node = "mother"
                self.graph.node("mother", shape="none", label=label)
            n_decaymodes = len(subchain)
            for idm in range(n_decaymodes):
                _list_parts = subchain[idm]["fs"]
                if not has_subdecay(_list_parts):
                    _bf = subchain[idm]["bf"]
                    _ref = new_node_no_subchain(_list_parts, _eff_bf=_eff_bf * _bf,
                                                _show_eff=_show_eff)
                    _total_eff_bf += _eff_bf * _bf
                    if link_pos is None:
                        self.graph.edge(top_node, _ref, label=f"{_bf*100:.2f} %")
                    else:
                        self.graph.edge(f"{top_node}:p{link_pos}", _ref, label=f"{_bf*100:.2f} %")
                else:
                    _ref_1 = new_node_with_subchain(_list_parts)
                    _bf_1 = subchain[idm]["bf"]
                    if link_pos is None:
                        self.graph.edge(top_node, _ref_1, label=f"{_bf_1*100:.2f} %")
                    else:
                        self.graph.edge(
                            f"{top_node}:p{link_pos}",
                            _ref_1,
                            label=f"{_bf_1*100:.2f} %",
                        )
                    _iter_eff_bf = 1.0
                    _c = 0
                    max_l = len([_p for _p in _list_parts if not isinstance(_p, str)])
                    for i, _p in enumerate(_list_parts):
                        if not isinstance(_p, str):
                            _k = list(_p.keys())[0]
                            if _c == max_l-1:
                                _total_eff_bf = iterate_chain(
                                    _p[_k],
                                    top_node=_ref_1,
                                    link_pos=i,
                                    _eff_bf=_iter_eff_bf * _eff_bf * _bf_1,
                                    _total_eff_bf=_total_eff_bf,
                                )
                            else:
                                _iter_eff_bf = iterate_chain(
                                    _p[_k],
                                    top_node=_ref_1,
                                    link_pos=i,
                                    _eff_bf=_iter_eff_bf * _eff_bf,
                                    _total_eff_bf=0,
                                    _show_eff=False
                                )
                            _c += 1

            return _total_eff_bf

        def has_subdecay(ds):
            return not all(isinstance(p, str) for p in ds)

        k = list(self._chain.keys())[0]
        label = html_table_label([k], add_tags=True, bgcolor="#568dba")
        sc = self._chain[k]

        # Actually build the whole decay chain, iteratively
        _total_eff_bf = iterate_chain(sc)
        print(f'Total BF shown: {_total_eff_bf*100:.2f}%')
        self.graph.node(
            "Total Effective BF",
            label=f"Total: {_total_eff_bf:.2E}\n = {_total_eff_bf*100:.2f} %",
            shape="diamond",
            fontcolor="#ff6000",
            fontsize="12",
        )

    @property
    def graph(self):
        """
        Get the actual `graphviz.dot.Digraph` object.
        The user now has full control ...
        """
        return self._graph

    def to_string(self):
        """
        Return a string representation of the built graph in the DOT language.
        The function is a trivial shortcut for ``graphviz.dot.Digraph.source`.
        """
        return self.graph.source

    def _instantiate_graph(self, **attrs):
        """
        Return a ``graphviz.dot.Digraph` class instance using the default attributes
        specified in this class:
        - Default graph attributes are overridden by input by the user.
        - Class and node and edge defaults.
        """
        graph_attr = self._get_graph_defaults()
        node_attr = self._get_node_defaults()
        edge_attr = self._get_edge_defaults()
        if "graph_attr" in attrs:
            graph_attr.update(**attrs["graph_attr"])
            attrs.pop("graph_attr")
        if "node_attr" in attrs:
            node_attr.update(**attrs["node_attr"])
            attrs.pop("node_attr")
        if "edge_attr" in attrs:
            edge_attr.update(**attrs["edge_attr"])
            attrs.pop("edge_attr")

        arguments = self._get_default_arguments()
        arguments.update(**attrs)

        return graphviz.Digraph(
            graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr, **arguments
        )

    def _get_default_arguments(self):
        """
        `graphviz.dot.Digraph` default arguments.
        """
        return dict(
            name="DecayChainGraph",
            comment="Created by https://github.com/scikit-hep/decaylanguage",
            engine="dot",
            format="png",
        )

    def _get_graph_defaults(self):
        d = self._get_default_arguments()
        d.update(rankdir="LR")
        return d

    def _get_node_defaults(self):
        return dict(fontname="Helvetica", fontsize="11", shape="oval")

    def _get_edge_defaults(self):
        return dict(fontcolor="#4c4c4c", fontname="Helvetica", fontsize="11")

    def _repr_svg_(self):
        """
        IPython display in SVG format.
        """
        return self._graph._repr_image_svg_xml()


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
        self._df = pandas.DataFrame()

        # Build the actual graph from the input decay chain structure
        self._build_decay_graph()

    def _build_decay_graph(self):
        """
        Recursively navigate the decay chain tree and append to a pandas DataFrame.
        """
        def get_decay_str(prefix, mother, list_parts):
            # print(mother)
            if prefix is None:
                decay_str = mother + ' --> ' + ' '.join(list_parts)
            else:
                decay_str = prefix + ' ; ' + mother + ' --> ' + ' '.join(list_parts)

            return decay_str

        def iterate_chain(
            subchain, _eff_bf=1.0, _total_eff_bf=0.0, prefix = None, mother=None, _append=True):
            n_decaymodes = len(subchain)
            for idm in range(n_decaymodes):
                _list_parts = subchain[idm]["fs"]
                if not has_subdecay(_list_parts):
                    _bf = subchain[idm]["bf"]
                    _decay_str = get_decay_str(prefix, mother, _list_parts)
                    if _append:
                        new_row = {'Decay': _decay_str,
                                    'BF': _eff_bf * _bf}
                        self._df = self._df.append(new_row, ignore_index=True)
                    _total_eff_bf += _eff_bf * _bf
                else:
                    _bf_1 = subchain[idm]["bf"]
                    _iter_eff_bf = 1.0
                    _c = 0
                    max_l = len([_p for _p in _list_parts if not isinstance(_p, str)])
                    daughters = [_p if isinstance(_p, str) else list(_p.keys())[0] for _p in _list_parts]
                    _decay_str = get_decay_str(prefix, mother, daughters)
                    for i, _p in enumerate(_list_parts):
                        if not isinstance(_p, str):
                            _k = list(_p.keys())[0]
                            if _c == max_l-1:
                                _total_eff_bf, _decay_str = iterate_chain(
                                    _p[_k],
                                    _eff_bf=_iter_eff_bf * _eff_bf * _bf_1,
                                    _total_eff_bf=_total_eff_bf,
                                    mother=_k,
                                    prefix= _decay_str
                                )
                            else:
                                _iter_eff_bf, _decay_str = iterate_chain(
                                    _p[_k],
                                    _eff_bf=_iter_eff_bf * _eff_bf,
                                    _total_eff_bf=0,
                                    mother=_k,
                                    prefix=_decay_str,
                                    _append=False
                                )
                            _c += 1

            return _total_eff_bf, _decay_str

        def has_subdecay(ds):
            return not all(isinstance(p, str) for p in ds)

        k = list(self._chain.keys())[0]
        sc = self._chain[k]

        # Actually build the whole decay chain, iteratively
        _total_eff_bf, _decay_str = iterate_chain(sc, mother=k)
        print(f'Total BF tabulated: {_total_eff_bf*100:.2f}%')

    @property
    def table(self):
        """
        Get the actual `pandas.DataFrame` object.
        The user now has full control ...
        """
        return self._df
