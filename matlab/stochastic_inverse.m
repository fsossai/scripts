% Approximating the inverse of a matrix by simulating
% the evolution of a Markov chain. 
% The input matrix must be a strictly diagonally dominant L-matrix.
% Strictness can be relaxed in some cases.

function B = stochastic_inverse(A, eps, rounds)
N = length(A);
D = diag(eps ./ sum(A,2));
%D = diag(1 ./ diag(A));
Q = eye(N) - D*A;
CDF = cumsum(Q,2);
CDF = [CDF ones(N,1)];
W = zeros(N,N);

for m=1:rounds
    % simulating the evolution starting at state 'i'
    for i=1:N
        next = i;
        while next ~= N+1
            W(i,next) = W(i,next) + 1;
            r = rand();
            next = find(r < CDF(next,:),1);
        end
    end
end

W = W / rounds;
B = W*D;

end








