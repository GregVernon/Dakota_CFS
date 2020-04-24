# Dakota_CFS
This repository supports the open- access article available here [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3753509.svg)](https://doi.org/10.5281/zenodo.3753509)

## Requirements
1) Unfortunately, to run the code contained within this repository will require the user to acquire a license of Coreform's Flex (*aka* Trelis) and Crunch software.  However all the files that these codes would run are ASCII text based inputs, so if you don't have access to Coreform packages - or if future updates to these packages breaks usage - you should be able to easily translate this functionality to tools you have can access.

2) Installation of DAKOTA

3) Python v3.6.8
   1) numpy

4) Julia v1.0+
   1) Use Julia to solve eigenvalue problem
      1) [AlgebraicMultigrid](https://github.com/JuliaLinearAlgebra/AlgebraicMultigrid.jl)
   
      2) [IterativeSolvers](https://github.com/JuliaMath/IterativeSolvers.jl)
   
   2) Use MATLAB to solve eigenvalue problem
      1) [MAT](https://github.com/JuliaIO/MAT.jl)

5) MATLAB (recommended to solve eigenvalue problem)
   1) Compiler Toolbox (optional)

##  Replication usage
1) Navigate to either problem directory
2) Run DAKOTA
   1) Interactive mode
      1) `dakota -i <YourSolver.in>`
   2) Background mode
      1) `dakota -i <YourSolver.in> > dakota.log 2>&1 &`

##  Usage on your own problem
1) Copy & rename the `src/TEMPLATE` directory to `path/to/your/ProjectName`.
2) Navigate to your project
3) Create a Trelis file that is comprised of two surfaces representing your planar geometry in the `z=0` plane
   1) Domain
   2) Feasible Domain
4) Modify `DakotaTemplate.in` to suit your specific optimization
5) Update `freqInput.py` to capture your problem-specific settings
   1) Geometric Properties
      1) Thickness
      2) Search radius for applying nodal BC around support location
   2) Material Properties
      1) Young's modulus
      2) Poisson ratio
      3) Density
   3) Mesh Properties
      1) Number of elements through thickness
      2) Polynomial degree of elements in the thickness dimension
6) Use `MakeInput.py` to create your custom project scripts and input files:
   1) `python3 MakeInput DakotaTemplate.in <YourSolver.in> <#-supports> <xmin> <xmax> <ymin> <ymax>`
7) Run DAKOTA
   1) Interactive mode
      1) `dakota -i <YourSolver.in>`
   2) Background mode
      1) `dakota -i <YourSolver.in> > dakota.log 2>&1 &`
