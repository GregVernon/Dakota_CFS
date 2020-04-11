#!python
import os
import sys
import subprocess
import numpy
from math import *

pathToTrelis = "/home/christopher/trelis/cubit_build/claro/bin"
sys.path.append(pathToTrelis)

if os.name == 'nt':
  binPath = pathToTrelis #os.path.dirname(os.path.abspath(__file__))
  acisPath = r"/acis/code/bin"
  try:
    os.add_dll_directory(binPath + acisPath)
  except AttributeError:
    os.environ['path'] += ';' + binPath + acisPath


import cubit
cubit.init(['cubit','-nobanner','-nographics'])


def main(paramFile, objFile):
    x,y = readParamFile(paramFile)
    status, bc_xyz, num_elem, nlcon = makeGeometry(x,y)
    if status != False:
        error_handle(objFile, nlcon, "makeGeometry")
        return
    
    status = buildUSpline(2,1)
    if status != False:
        error_handle(objFile, nlcon, "buildUSpline")
        return
    
    status = buildSimInput(bc_xyz, num_elem)
    if status != False:
        error_handle(objFile, nlcon, "buildSimInput")
        return
    
    status = assemble_LinearSystem()
    if status != False:
        error_handle(objFile, nlcon, "assemble_LinearSystem")
        return
    
    status = compute_Eigenvalue(True)
    if status != False:
        error_handle(objFile, nlcon, "compute_Eigenvalue")
        return
    
    write_objvalue(objFile, nlcon)


def readParamFile(paramFile):
    f = open(paramFile,'r')
    fLines = f.readlines()
    x = []
    y = []
    for i in range(0,len(fLines)):
        if numpy.remainder(i,2) == 0:
            x.append(float(fLines[i].strip()))
        else:
            y.append(float(fLines[i].strip()))
        
    return x,y

def error_handle(objFile, nlcon, callingFunction):
    f = open(objFile,"w+")
    #nlcon = numpy.array(nlcon)
    if   callingFunction == "makeGeometry":
        f.write("ObjVal " + str(numpy.sum(nlcon)) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "buildUSpline":
        f.write("FAIL" + "\n")
        f.write("ObjVal " + str(1e-3 * numpy.min([0.,numpy.min(nlcon)])) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "buildSimInput":
        f.write("FAIL" + "\n")
        f.write("ObjVal " + str(1e-3 * numpy.min([0.,numpy.min(nlcon)])) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "assemble_LinearSystem":
        f.write("FAIL" + "\n")
        f.write("ObjVal " + str(1e-3 * numpy.min([0.,numpy.min(nlcon)])) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "compute_Eigenvalue":
        f.write("FAIL" + "\n")
        f.write("ObjVal 0.0" + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    f.close()


def write_objvalue(objFile, nlcon):
    # Get fundamental eigenvalue
    f = open("EigenValue.txt","r")
    eigval = float(f.readlines()[0].strip())
    f.close()
    # Calculate objective value
    freq = numpy.sqrt(eigval) / (2*numpy.pi)
    objValue = -1. * freq
    # Write objective value to text file
    f = open(objFile, "w+")
    f.write("ObjVal " + str(objValue) + "\n")
    for n in range(0,len(nlcon)):
        f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    f.close()
    return freq, objValue


def makeGeometry(x,y):
    status = 0
    cubit.cmd("reset")
    cubit.cmd('open "pcb_geom.trelis"')
    cubit.cmd("compress ids")
    
    x = numpy.array(x)
    y = numpy.array(y)
    
    sys.stdout.write("PIN-X = " + str(x) + "\n")
    sys.stdout.flush()
    
    # Test to see if the vertex is contained on the target surface
    target_surface = cubit.surface(2) # Target surface is id = 2
    vertex_on_surface = numpy.zeros(len(x),dtype=bool)
    for i in range(0,len(x)):
        vertex_on_surface[i] = target_surface.point_containment([x[i], y[i], 0.])
    X = x[vertex_on_surface]
    Y = y[vertex_on_surface]
    
    # Compute Nonlinear Constraints    
    nlcon = computeNonlinearConstraint(x,y)
    sys.stdout.write("Nonlinear Constraints: ")
    sys.stdout.write(str(nlcon))
    sys.stdout.write("\n")
    sys.stdout.flush()
    
    num_active_pins = len(X)
    sys.stdout.write("#"*10 + "NUMBER OF ACTIVE PINS = " + str(num_active_pins) + "#"*10 + "\n")
    sys.stdout.flush()
    if num_active_pins == 0:
        # No pins on board, return with nonlinear constraint values
        status = 1
        return status, [], [], nlcon
    
    # Delete the target surface -- we don't need it anymore
    cubit.cmd("delete vol 2")
    cubit.cmd("compress ids")
    
    # Imprint circles on the geometry surface
    # Get initial curve ids
    C = cubit.get_entities("curve")
    for i in range(0, num_active_pins):
        cubit.cmd("webcut volume all with cylinder radius 2.75 axis z center " + str(X[i]) + " " + str(Y[i]) + " 0.")
        #cubit.cmd("create curve arc radius 2.75 center location " + str(X[i]) + " " + str(Y[i]) + " 0 normal 0 0 1 start angle 0 stop angle 360 ")
    cubit.cmd("imprint all")
    cubit.cmd("merge all")
    cubit.cmd("stitch volume all")
    cubit.cmd("compress ids")
    #CF = cubit.get_list_of_free_ref_entities("curve")
    #for i in range(0,len(CF)):
    #    cubit.cmd("partition create surface all  curve " + str(CF[i]))
    #cubit.cmd("delete free curve all")
    cubit.cmd("compress ids")
    
    # Mesh the pin surfaces first
    S = cubit.get_entities("surface")
    for i in range(0,len(S)):
        if cubit.surface(S[i]).area() <= (1.1 * numpy.pi * (2.75**2)):
            cubit.cmd("surface " + str(S[i]) + " size 4")
            cubit.cmd("surface " + str(S[i]) + " scheme circle")
            cubit.cmd("mesh surface " + str(S[i]))
        else:
            board_surf_id = S[i]
    
    # Now mesh the board
    cubit.cmd("surface " + str(board_surf_id) + " size 10")
    cubit.cmd("mesh surface " + str(board_surf_id))
    
    # Smooth the surface mesh
    cubit.cmd("surface all smooth scheme mean ratio cpu 0.1")
    cubit.cmd("smooth surf all")
    
    # Set the BC edges to be creased to C^0
    cubit.cmd('create group "cf_crease_entities"')
    S_BC = cubit.get_entities("surface")
    for i in range(0, len(S_BC)):
        if S_BC[i] == board_surf_id:
            pass
        else:
            surf_edges = cubit.parse_cubit_list("edge", "in surface " + str(S_BC[i]))
            for e in range(0,len(surf_edges)):
                cubit.cmd("group 2 add edge " + str(surf_edges[e]))
    
    ### Prepare function return ###
    num_elem = len(cubit.get_entities("Face"))
    
    # Package the pin locations for function return
    bc_xyz = []
    for i in range(0, len(X)):
        bc_xyz.append([X[i], Y[i], 0.])
    
    # Save the cubit file
    cubit.cmd('save as "mesh.cub" overwrite')
    
    return status, bc_xyz, num_elem, nlcon


def computeNonlinearConstraint(x,y):
    nlcon = numpy.zeros(len(x))
    target_surface = cubit.surface(2) # Target surface is id = 2
    vertex_on_surface = [False for i in range(0,len(x))]
    # First, determine whether the nonlinear constraint is satisfied
    for i in range(0,len(x)):
        vertex_on_surface[i] = target_surface.point_containment([x[i], y[i], 0.])
    # Second, determine the magnitude of the nonlinear constraint value
    #         which is the distance of the point to the closest curve
    cid = cubit.parse_cubit_list("curve", "in vol 2")
    for i in range(0,len(x)):
        dist = numpy.zeros(len(cid))
        pXYZ = numpy.array([x[i], y[i], 0.])
        for c in range(0,len(cid)):
            C = cubit.curve(cid[c])
            cpXYZ = numpy.array(C.closest_point(pXYZ))
            dist[c] = numpy.linalg.norm(cpXYZ - pXYZ)
        if vertex_on_surface[i] == True:
            # Nonlinear constraint is satisfied
            nlcon[i] = -1. * numpy.min(dist)
        else:
            # Nonlinear constraint not satisfied
            nlcon[i] = +1. * numpy.min(dist)
    return nlcon


def buildUSpline(degree, continuity):
    pathToCFT = "/home/christopher/cf/master/b_codes_with_debug/bin"
    CFT_command = pathToCFT + "/cf_trelis " + "mesh.cub" + " --degree " + str(degree) + " --continuity " + str(continuity)
    sys.stdout.write(CFT_command + "\n")
    sys.stdout.flush()
    try:
        status = subprocess.check_call(CFT_command,shell=True)
    except: 
        sys.stdout.write("buildUSpline FAILED" + "\n")
        status = True
        sys.stdout.flush()
    return status

def buildSimInput(bc_xyz, num_elem):
    #pathToFreqInput = "/home/christopher/optimization_project/Dakota_CFS/src/cf_run_scripts/"
    #pathToFreqInput = "/home/greg/Dakota_CFS/src/cf_run_scripts/"
    pathToFreqInput = os.getcwd() + "/"
    XYZ = [[bc_xyz[i][0], bc_xyz[i][1], 0.] for i in range(0,len(bc_xyz))]
    str_XYZ = str(XYZ).replace(" ","")
    py_command = "python3 " + pathToFreqInput + "freqInput.py " + "mes.json " + "-p " + str_XYZ + " -n " + str(num_elem) + " -o -1" 
    sys.stdout.write(py_command + "\n")
    sys.stdout.flush()
    try:
        status = subprocess.check_call(py_command, shell=True)
    except:
        sys.stdout.write("buildSimInpout FAILED" + "\n")
        status = True
        sys.stdout.flush()
    return status

def assemble_LinearSystem():
    pathToCFS = "/home/christopher/cf/master/b_codes_with_debug/bin/"
    cfs_command = pathToCFS + "cfs " + "test.json"
    sys.stdout.write(cfs_command + "\n")
    sys.stdout.flush()
    try:
        status = subprocess.check_call(cfs_command, shell=True)
    except:
        sys.stdout.write("assemble_LinearSystem FAILED" + "\n")
        status = True
        sys.stdout.flush()
    return status

def compute_Eigenvalue(useMatlab):
    #pathToJulia = "/home/christopher/cf/master/deps/srcs/julia/julia-1.3.0/bin/"
    pathToJulia = "/usr/local/bin/"
    jl_command = pathToJulia + "julia " + "GenEigProb.jl" + " " + str(useMatlab).lower()
    sys.stdout.write(jl_command + "\n")
    sys.stdout.flush()
    try:
        status = subprocess.check_call(jl_command, shell=True)
    except:
        sys.stdout.write("compute_Eigenvalue -- Julia FAILED" + "\n")
        status = True
        sys.stdout.flush()
        return status
    
    if useMatlab == True:
        mat_command = 'matlab -nodisplay -batch "GenEigProb(' + str("'EigenValue.txt'") + ')"'
        sys.stdout.write(mat_command + "\n")
        sys.stdout.flush()
        try:
            status = subprocess.check_call(mat_command, shell=True)
        except:
            sys.stdout.write("compute_Eigenvalue -- Matlab FAILED" + "\n")
            status = True
            sys.stdout.flush()
            return status
    return status

if __name__ == "__main__":
    print(sys.argv)
    paramFile = sys.argv[1]
    objFile = sys.argv[2]
    main(paramFile, objFile)
