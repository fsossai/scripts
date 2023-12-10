import matplotlib.pyplot as plt
import networkx
import random
import numpy

def init_graph(directed=False):
    G = networkx.Graph(directed=False)
    G.add_node(0)
    G.add_node(1)
    G.add_edge(0, 1)
    return G

def preferential_attachment(G, N, m=1):
    G = G or init_graph()
    for i in range(2, N):
        degs = numpy.array([d for _, d in G.degree()])
        cdf = numpy.cumsum(degs)
        for _ in range(m):
            n = numpy.argmax(cdf > random.randint(0, (i-1)*2-1))
            G.add_edge(i, n)
    return G

def random_attachment(G, N, m=1):
    G = G or init_graph()
    for i in range(2, N):
        for _ in range(m):
            n = numpy.random.randint(0, i-1)
            G.add_edge(i, n)
    return G

def erdos_renyi(G, N, m=1):
    G = G or init_graph()
    p = m * (2/(N-1))
    G.add_nodes_from(range(N))
    for i in range(N):
        for j in range(i+1, N):
            if numpy.random.rand() < p:
                G.add_edge(i, j)
    return G

def plot(G):
    fig, axs = plt.subplots(1,2)
    fig.suptitle("Preferential Attachment")

    axs[0].set_title("Degree distribution")
    axs[0].plot(sorted([d for _, d in G.degree()], reverse=True))
    axs[0].set_xscale("log")
    axs[0].set_yscale("log")
    axs[0].set_xlabel("Degree")
    axs[0].set_ylabel("Count")

    N = len(G.nodes)
    M = len(G.edges)
    axs[1].set_title("Nodes = {}, Edges = {}".format(N, M))
    networkx.draw(G, with_labels=False, node_size=1e4/N, width=0.5, ax=axs[1])

    plt.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", metavar="NODES", type=int, default=500)
    args = parser.parse_args()
    G = init_graph()
    G = preferential_attachment(G, args.n, 1)
    #G = erdos_renyi(G, args.n, 1)
    #G = random_attachment(G, args.n, 1)
    plot(G)
