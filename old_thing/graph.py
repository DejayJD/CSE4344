import csv
import sys

def open_file(filename):
    network = []
    nodes = set()
    with open(filename) as input_file:
        reader = csv.reader(input_file)
        for n1, n2, weight in reader:
            nodes.add(n1)
            nodes.add(n2)
            network.append((n1, n2, weight))
    return list(nodes), network

filename = sys.argv[1]
node_list, network = open_file(filename)

import networkx as nx

G=nx.Graph()
for link in network:
    n1, n2, weight = link
    G.add_edge(n1, n2)

import matplotlib.pyplot as plt

nx.draw(G)
plt.show()
