function [G] = rssg(A,v)
    D = diag(v);
    u = A*v;
    g = D^-1 * u;
    m = 1/length(A) * sum(g);
    M = A' * D^-1 - diag(D^-2 * u);
    z = g - m;
    G = M*z;
end