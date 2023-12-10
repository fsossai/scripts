import matplotlib.pyplot as plt
import graph_powerlaw
import networkx
import argparse

def generate_random_graph(n, p):
    G = networkx.gnp_random_graph(n, p)
    return G

def gap(G, v):
    count = 0
    d = G.degree(v)
    if d == 0:
        return 0
    for n in G.adj[v]:
        count += G.degree(n)
    avg = count / d
    return avg - d

def gaps(G):
    g = []
    for n in G.nodes():
        g.append(gap(G, n))
    return g

def plot(g):
    fig, axs = plt.subplots(1, 2, figsize=(12, 8))
    N = len(G.nodes)
    M = len(G.edges)
    fig.suptitle("The Friendship Paradox\n"
                 f"Powerlaw graph: Nodes = {N}, Edges = {M}")

    axs[0].set_title("Degree distribution")
    axs[0].plot(sorted([d for _, d in G.degree()], reverse=True))
    axs[0].set_xscale("log")
    axs[0].set_yscale("log")
    axs[0].set_xlabel("Degree")
    axs[0].set_ylabel("Count")

    avg = sum(g)/len(g)
    axs[1].set_title("Gap distribution")
    axs[1].hist(g, bins=30, alpha=0.7)
    axs[1].axvline(x=avg, linestyle="--", label=f"Average gap = {avg:.2f}")
    expression = r"$\left(\frac{1}{|n^+|} \cdot \sum_{v\in n^+}{|v^+|}\right) - |n^+|$"
    axs[1].set_xlabel(expression)
    axs[1].legend()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", metavar="NODES", type=int, default=1000)

    args = parser.parse_args()
    G = graph_powerlaw.preferential_attachment(None, N=args.n)
    g = gaps(G)
    plot(g)



