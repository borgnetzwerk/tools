import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import math
from graphviz import Source
import os


def sample():
    # Build a dataframe with 4 connections
    df = pd.DataFrame(
        {'from': ['A', 'B', 'C', 'A'], 'to': ['D', 'A', 'E', 'C']})

    # Build your graph
    G = nx.from_pandas_edgelist(df, 'from', 'to')

    # Plot it
    nx.draw(G, with_labels=True, node_color='None', edge_color='lightblue')
    plt.show()


def graph_from_list(data):
    df = pd.DataFrame(data, columns=['from', 'to'])

    # Build your graph
    G = nx.from_pandas_edgelist(df, 'from', 'to', create_using=nx.DiGraph())
    pos = nx.spring_layout(G, k=15/math.sqrt(G.order()))
    # nx.draw_networkx(G.subgraph('root'), pos=pos, node_color='black')

    # Plot it
    # nx.draw(G, with_labels=True, node_size=1500, alpha=0.3, arrows=True)
    nx.draw(G, with_labels=True, arrows=True, node_size=1500,
            node_color='None', edge_color='lightblue')
    nx.nx_pydot.write_dot(G, 'file.dot')
    dot_plot()
    # plt.show()


def dot_plot(filename="file.dot", directory="output/"):
    engines = ["dot", "fdp"]
    all_engines = ["dot", "neato", "fdp", "sfdp", "circo",
                   "twopi", "osage", "patchwork"]
    # s = Source.from_file(filename, directory=directory, encoding="utf8")
    s = Source.from_file(filename, directory=directory,
                         encoding="utf8", format='svg')
    s = s.unflatten(stagger=5)
    for engine in engines:
        try:
            s.engine = engine
            new_filename= f"{filename}_{engine}"
            s.render(filename=new_filename, directory=directory)
            if os.path.exists(directory + new_filename):
                # remove the non-pdf file
                os.remove(directory + new_filename)
        except Exception as e:
            print(e)
    # s.view()

# dot_plot()
# sample()
