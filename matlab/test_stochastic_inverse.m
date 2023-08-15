N = 50; % dimensionality
M = 1:10:500; % simulation range
eps_range = [0.1];

% Strictly diagonally dominant random L-matrix generation
c = 0.5;
A = diag((1+2*c)*ones(1,N));
A = A + diag(-c*ones(1,N-1),+1);
A = A + diag(-c*ones(1,N-1),-1);

inv_A = inv(A);
E = [];

tic
for eps=eps_range
    E_eps = [];
    for m=M
        pseudo_inv_A = stochastic_inverse(A, eps, m);
        % Considering error as the Frobenius norm of the differences
        %E_eps = [ E_eps sum(sum( (eye(N) - pseudo_inv_A * A) .^ 2 )) ];
        E_eps = [ E_eps sqrt(sum(sum( (inv_A - pseudo_inv_A) .^ 2 ))) ];
    end
    E = [E; E_eps];
end
toc

figure
labels = [];
hold on
for i=1:length(eps_range)
    plot(M, E(i,:), '.-');
    labels = [labels "eps=" + eps_range(i)];
end
legend(labels);
title('Frobenius norm of the error matrix');
hold off


