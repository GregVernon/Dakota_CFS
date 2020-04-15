function GenEigProb(filename)
K = load("stiffness.mat");
K = K.K;

M = load("mass.mat");
M = M.M;

sol = eigs(K,M,1,"smallestabs","maxit",1e4);

writeFloatToFile(filename, sol);
end

function writeFloatToFile(filename, floatValue)
f = fopen(filename, "w+");
fprintf(f, num2str(floatValue));
fclose(f);
end

