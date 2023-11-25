# Approximating the inverse of a matrix by simulating
# the evolution of a Markov chain.
# The input matrix must be a diagonally dominant L-matrix and there must
# be at least one row whose diagonal element strictly dominates the
# off-diagonal elements.
# https://en.wikipedia.org/wiki/L-matrix
# https://en.wikipedia.org/wiki/Diagonally_dominant_matrix

import matplotlib.pyplot as plt
import numpy as np

def precondition(A):
    row_sums = np.sum(np.abs(A), axis=1)
    diag = np.abs(np.diagonal(A))
    offdiag = row_sums - diag
    result = True
    result = result and np.all(diag >= offdiag)
    result = result and np.any(diag > offdiag) 
    return result
 
def invert(A, trials=100):
    if not precondition(A):
        raise Exception("ERROR: matrix not suitable")

    N = A.shape[0]
    W = np.zeros((N,N))
    D = 1 / np.diag(A)
    D = np.diag(D)
    Q = np.eye(N,N) - D.dot(A)
    t = 1 - np.sum(Q, axis=1).reshape((N,1))
    P = np.hstack((Q, t))

    for _ in range(trials):
        for i in range(N):
            j = i
            while True:
                W[i, j] += 1
                j = np.random.choice(N+1, p=P[j,:])
                if j == N:
                    break

    W = W / trials
    W = W.dot(D)
    return W

if __name__ == "__main__":
    N = 100
    A = 4*np.eye(3) - np.eye(3, k=1) - np.eye(3, k=-1)
    A = np.kron(np.eye(N), A) - np.eye(3*N, k=3) - np.eye(3*N, k=-3)
    A = A.astype("int")

    err = []
    A_inv = np.linalg.inv(A)
    I = np.eye(A.shape[0])
    r = np.linalg.norm(A_inv)
    for trials in np.power(2, np.arange(8)):
        plt.clf()
        B = invert(A, trials)
        e = np.linalg.norm(B - A_inv, "fro") / r
        err.append(e)
        print(f"trials={trials}\terror={e:.5f}")

    x = np.power(2, np.arange(len(err)))
    plt.loglog(x, err, ".-", label=r"$||B-A^{-1}||_F$")
    plt.xlabel("Trials")
    plt.ylabel("Relative error")
    plt.legend()
    plt.grid(True, which="minor")
    plt.show()
    print("Done")

