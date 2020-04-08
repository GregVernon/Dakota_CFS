import AlgebraicMultigrid
import IterativeSolvers
import SparseArrays

classids = Dict("Vec"=>1211214, "Mat"=>1211216)
ids_to_class = Dict(zip(values(classids), keys(classids)))

function solve_GEP(K,M, doPreconditioning)
    if doPreconditioning == true
        t0 = time()
        print("Computing AMG Scheme. . . ")
        SA = AlgebraicMultigrid.smoothed_aggregation(K)
        print("FINISHED in ", string(time()-t0), " Seconds", "\n")

        t0 = time()
        print("Converting AMG into Preconditioner. . . ")
        PC = AlgebraicMultigrid.aspreconditioner(SA)
        print("FINISHED in ", string(time()-t0), " Seconds", "\n")

        t0 = time()
        print("Solving for Lowest Eigenvalue using AMG-LOBPCG Solver. . . ")
        sol = IterativeSolvers.lobpcg(K,M,false,1,maxiter=1e5, tol=1e-5, P=PC)
        print("FINISHED in ", string(time()-t0), " Seconds", "\n")
    else
        t0 = time()
        print("Solving for Lowest Eigenvalue using LOBPCG Solver. . . ")
        sol = IterativeSolvers.lobpcg(K,M,false,1,maxiter=1e5, tol=1e-9)
        print("FINISHED in ", string(time()-t0), " Seconds", "\n")
    end
    return sol.λ  
end

function load_KM(kFile, mFile)
    K = readPETSc(kFile)
    M = readPETSc(mFile)
    return K, M
end

function writeFloatToFile(filename, fValue)
    f = open(filename, "w+")
    write(f, string(fValue))
    close(f)
end

function readPETSc(filename; int_type = Int32, scalar_type = Float64) :: Union{SparseArrays.SparseMatrixCSC, Vector}
    open(filename) do io
        class_id = ntoh(read(io, int_type))
        if !in(class_id, keys(ids_to_class))
            throw("Invalid PETSc binary file $class_id")
        end
        if ids_to_class[class_id] == "Vec"
            read_vec(io, int_type, scalar_type)
        elseif ids_to_class[class_id] == "Mat"
            read_mat(io, int_type, scalar_type)
        end
    end
end

function read_mat(io, int_type, scalar_type)
    rows = ntoh(read(io, int_type))
    cols = ntoh(read(io, int_type))
    nnz = ntoh(read(io, int_type))

    row_ptr = Array{int_type}(undef, rows+1)
    row_ptr[1] = 1

    # read row lengths
    row_ptr[2:end] = map(ntoh, read!(io, Array{ int_type }( undef, rows ) ) )
    cumsum!(row_ptr, row_ptr)

    # write column indices
    colvals = map(ntoh, read!(io, Array{ int_type }( undef, nnz ) )) .+ int_type(1)

    # write nonzero values
    vals = map(ntoh, read!(io, Array{ scalar_type }( undef, nnz ) ))

    mat = SparseArrays.SparseMatrixCSC(cols, rows, row_ptr, colvals, vals)
    T = transpose(mat)
    copy( T )
end

######### SOLVE THE GENERAL EIGENVALUE PROBLEM #########

# Load the matrices
t0 = time()
print("\n","Loading the matrices. . . ")
kFile = "stiffness.m"
mFile = "mass.m"
K,M = load_KM(kFile, mFile)
print("FINISHED in ", string(time()-t0) ," Seconds", "\n")

# Solve the General Eigenvalue Problem for the minimum eigenvalue
eigValue = solve_GEP(K,M,true)

# Store the result in a text file
writeFloatToFile("EigenValue.txt", eigValue[1])
