import numpy
import networkx
import random
import matplotlib.pyplot as plt

N = 500

G = networkx.Graph(directed=False)
G.add_node(0)
G.add_node(1)
G.add_edge(0, 1)

for i in range(2, N):
    degs = numpy.array([d for _, d in G.degree()])
    cdf = numpy.cumsum(degs)
    n = numpy.argmax(cdf > random.randint(0, (i-1)*2-1))
    G.add_edge(i, n)
    
N = len(G.nodes)
M = len(G.edges)

fig, axs = plt.subplots(1,2)
fig.suptitle("Preferential Attachment")

axs[0].set_title("Degree distribution")
axs[0].plot(sorted([d for _, d in G.degree()], reverse=True))
axs[0].set_xscale("log")
axs[0].set_yscale("log")
axs[0].set_xlabel("Degree")
axs[0].set_ylabel("Count")

axs[1].set_title("Nodes = {}, Edges = {}".format(N, M))
networkx.draw(G, with_labels=False, node_size=1e4/N, width=0.5, ax=axs[1])

plt.show()
