# A Markov Chain Monte Carlo algorithm to approximate the inverse of
# a matrix with the following properties:
# The input matrix must be a diagonally dominant L-matrix.
#
# https://en.wikipedia.org/wiki/Markov_chain_Monte_Carlo
# https://en.wikipedia.org/wiki/L-matrix
# https://en.wikipedia.org/wiki/Diagonally_dominant_matrix

import matplotlib.pyplot as plt
import numpy as np

def check(A):
    row_sums = np.sum(np.abs(A), axis=1)
    diag = np.abs(np.diagonal(A))
    offdiag = row_sums - diag
    result = True
    result = result and np.all(diag >= offdiag)
    return result
 
def invert(A, samples=100):
    if not check(A):
        raise Exception(
            "ERROR: the input matrix is not a diagonally dominant L-matrix")

    N = A.shape[0]
    W = np.zeros((N,N))
    D = 1 / np.diag(A)
    D = np.diag(D)
    Q = np.eye(N,N) - D.dot(A)
    t = 1 - np.sum(Q, axis=1).reshape((N,1))
    P = np.hstack((Q, t))

    for _ in range(samples):
        for i in range(N):
            j = i
            while True:
                W[i, j] += 1
                j = np.random.choice(N+1, p=P[j,:])
                if j == N:
                    break

    W = W / samples
    W = W.dot(D)
    return W

def test(A):
    err = []
    N = A.shape[0]
    A_inv = np.linalg.inv(A)
    I = np.eye(A.shape[0])
    r = np.linalg.norm(A_inv)
    for samples in np.power(2, np.arange(8)):
        plt.clf()
        B = invert(A, samples)
        e = np.linalg.norm(B - A_inv, "fro") / r
        err.append(e)
        print(f"samples={samples}\terror={e:.5f}")

    x = np.power(2, np.arange(len(err)))
    plt.loglog(x, err, ".-", label="{}, {}".format(r"$||B-A^{-1}||_F$", f"size={N}x{N}"))
    plt.xlabel("Samples")
    plt.ylabel("Relative error")
    plt.legend()
    plt.grid(True, which="minor")
    plt.show()
    print("Done")

if __name__ == "__main__":
    # build a matrix similiar to the one arising in discrete Poisson
    # problem on a 2D grid with finite differences
    # A's shape will be 3N x 3N
    #
    # https://en.wikipedia.org/wiki/Discrete_Poisson_equation

    N = 100
    A = 4*np.eye(3) - np.eye(3, k=1) - np.eye(3, k=-1)
    A = np.kron(np.eye(N), A) - np.eye(3*N, k=3) - np.eye(3*N, k=-3)
    A = A.astype("int")
    test(A)
