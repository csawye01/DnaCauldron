from copy import deepcopy

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from Bio import Restriction
from dna_features_viewer import (BiopythonTranslator, CircularGraphicRecord,
                                 GraphicRecord)

from dnacauldron.tools import annotate_record
try:
    import pygraphviz
    from networkx.drawing.nx_agraph import graphviz_layout
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

class AssemblyTranslator(BiopythonTranslator):
    """Custom theme for plotting GENBANK assemblies w. Dna Features Viewer."""

    @staticmethod
    def is_source(feature):
        return ((feature.type == 'misc_feature') and
                feature.qualifiers.get('source', False))

    @staticmethod
    def compute_feature_color(feature):
        if feature:
            if AssemblyTranslator.is_source(feature):
                return '#ff4c4c'
            else:
                return '#f9edbb'

    @staticmethod
    def compute_feature_label(feature):
        if AssemblyTranslator.is_source(feature):
            return feature.qualifiers['source']
        elif abs(feature.location.end - feature.location.start) > 100:
            label = BiopythonTranslator.compute_feature_label(feature)
            return abreviate_string(label, 30)
        else:
            return None

def abreviate_string(string, max_length=30):
    """Truncate and add '...' if the string is too long"""
    return string[:max_length] + ('' if len(string) < max_length else '...')

def plot_cuts(record, enzyme_name, linear=True, figure_width=5, ax=None):
    """Plot a construct and highlight where an enzyme cuts.

    Parameters
    ----------

    record
      The biopython record to be plotted

    enzyme_name
      Name of the enzyme, e.g. "EcoRI"

    linear
      True for a linear construct, False for a circular construct

    figure_width
      Width of the figure in inches.

    ax
      Matplotlib ax on which to plot the construct. If None is provided, one
      will be created an returned.


    """
    enzyme = Restriction.__dict__[enzyme_name]
    record = deepcopy(record)
    cuts = enzyme.search(record.seq, linear=linear)
    for cut in cuts:
        annotate_record(record, (cut, cut+1),
                        feature_type='misc_feature',
                        enzyme=enzyme_name)
    class MyTranslator(BiopythonTranslator):

        @staticmethod
        def compute_feature_label(feature):
            if abs(feature.location.end - feature.location.start) > 100:
                label = BiopythonTranslator.compute_feature_label(feature)
                return abreviate_string(label, 10)
            else:
                return feature.qualifiers.get("enzyme", None)

        @staticmethod
        def compute_feature_color(feature):
            if (feature.qualifiers.get("enzyme", False) and
                (feature.type == 'misc_feature')):
                return '#f5eaff'
            else:
                return '#fefefe'
    translator = MyTranslator()
    grecord_class = GraphicRecord if linear else CircularGraphicRecord
    graphic_record = translator.translate_record(record,
                                                 grecord_class=grecord_class)
    return graphic_record.plot(ax=ax, figure_width=figure_width)

def plot_slots_graph(mix, ax=None, with_overhangs=False, show_missing=True):
    """Plot a map of the different assemblies.

    Parameters
    ----------
    mix
      A DnaCauldron AssemblyMix object.

    ax
      A matplotlib ax on which to plot. If none is provided, one is created.

    with_overhangs
      If true, the overhangs appear in the graph
    """
    slots = mix.compute_slots()
    graph = mix.slots_graph(with_overhangs=with_overhangs)

    # Positioning - a bit complex to deal with multi-components graphs
    pos = {}
    components = list(nx.components.connected_component_subgraphs(graph))
    max_len = 1.0 * max(len(c) for c in components)
    for i, g in enumerate(components):
        pos.update(nx.layout.kamada_kawai_layout(g, center=(0, -i),
                                                 scale=len(g) / max_len))

    parts = [n for n in graph.nodes() if n in slots]
    def polar(xy):
        x, y = xy - np.array([0.05, 0.05])
        return (np.arctan2(x, -y), -np.sqrt(x**2 + y**2))
    sorted_pos = sorted(pos.items(), key=lambda c: polar(c[1]))
    fig, ax = plt.subplots(1, figsize=(13, 0.4*len(parts)))
    nx.draw(graph, pos=pos, node_color='w', node_size=100, ax=ax,
            edge_color='#eeeeee')
    legend = []
    for i, (n, (x, y)) in enumerate(sorted_pos):
        if n in parts:
            slot_parts = list(slots[n])
            legend.append("\n     ".join(sorted(slot_parts)))
            fontdict = {'weight': 'bold'} if len(slot_parts) > 1 else {}
            ax.text(x, y, len(legend), ha='center', va='center',
                    color='#3a3aad', fontdict=fontdict)
        else:
            ax.text(x, y, n, ha='center', va='center', color='#333333',
                    size=9, fontdict=dict(family='Inconsolata'))
    text = "\n".join(['Parts:'] + [
        "%2s - %s" % (str(i + 1), name)
        for i, name in enumerate(legend)
    ])
    if show_missing:
        all_mix_parts = set([f.id for f in mix.constructs])
        all_slots_parts = set([p for plist in slots.values() for p in plist])
        missing_parts = all_mix_parts.difference(all_slots_parts)
        if len(missing_parts):
            text += "\n!!! Missing parts: " + ", ".join(missing_parts)

    ax.text(1.1, 0.5, text, va='center', transform=ax.transAxes,
            fontdict=dict(size=12, family='Inconsolata'))
    ax.set_aspect('equal')
    return ax
