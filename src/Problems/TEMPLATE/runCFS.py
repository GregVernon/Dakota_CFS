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
    
    status = buildUSpline(2,0)
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
    
    status = compute_Eigenvalue()
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
        f.write("FAIL")
        f.write("ObjVal " + str(numpy.min([0.,numpy.min(nlcon)])) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "buildSimInput":
        f.write("FAIL")
        f.write("ObjVal " + str(numpy.min([0.,numpy.min(nlcon)])) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "assemble_LinearSystem":
        f.write("FAIL")
        f.write("ObjVal " + str(numpy.min([0.,numpy.min(nlcon)])) + "\n")
        for n in range(0,len(nlcon)):
            f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    elif callingFunction == "compute_Eigenvalue":
        f.write("FAIL")
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
    cubit.cmd('open "circleGeom.trelis"')
    cubit.cmd("compress ids")
    num_base_vertex = len(cubit.get_entities("vertex"))
    
    x = numpy.array(x)
    y = numpy.array(y)
    target_surface = cubit.surface(1)
    vertex_on_surface = numpy.zeros(len(x),dtype=bool)
    for i in range(0,len(x)):
        vertex_on_surface[i] = target_surface.point_containment([x[i], y[i], 0.])
        if vertex_on_surface[i] == True:
            cubit.cmd("create vertex " + str(x[i]) + " " + str(y[i]) + " 0 on surface 1")
        
    nlcon = computeNonlinearConstraint(x,y)
    sys.stdout.write("Nonlinear Constraints: ")
    sys.stdout.write(str(nlcon))
    sys.stdout.write("\n")
    sys.stdout.flush()
    
    X = x[vertex_on_surface]
    Y = y[vertex_on_surface]
    num_active_pins = len(X)
    if num_active_pins == 0:
        # No pins on board, return with nonlinear constraint values
        status = 1
        return status, [], [], nlcon
    
    V = cubit.get_list_of_free_ref_entities("vertex")
    for i in range(0,len(V)):
        cubit.cmd("imprint volume all with vertex " + str(V[i]))
    cubit.cmd("delete free vertex all")
    cubit.cmd("compress ids")
    #for i in range(0,len(V)):
    #    cubit.cmd("nodeset 1 add vertex " + str(V[i]))
    cubit.cmd("surface all size 0.2")
    cubit.cmd("mesh surf all")
    cubit.cmd("surface all smooth scheme mean ratio cpu 0.1")
    cubit.cmd("smooth surf all")
    
    cubit.cmd("compress ids")
    
    V = numpy.zeros(num_active_pins, dtype=int)
    #N = numpy.zeros(num_active_pins, dtype=int)
    bc_xyz = [[] for i in range(0,num_active_pins)]
    cubit.cmd('create group "cf_crease_entities"')
    for i in range(0,num_active_pins):
        bc_xyz[i] = [X[i], Y[i], 0.]
        N = cubit.parse_cubit_list("node"," at " + str(X[i]) + " " + str(Y[i]) + " 0.")
        for n in range(0,len(N)):
            nodeEdges = cubit.parse_cubit_list("edge", "in node " + str(N[n]))
            for e in range(0,len(nodeEdges)):
                cubit.cmd("cf_crease_entities add Edge " + str(nodeEdges[e]))
    
    EinC = cubit.parse_cubit_list("edge"," in curve 1")
    #for e in range(0,len(EinC)):
    #    cubit.cmd("cf_crease_entities add Edge " + str(EinC[e]))

    
    VinC = cubit.parse_cubit_list("node"," in curve 1")
    for n in range(0,len(VinC)):
        nxyz = cubit.get_nodal_coordinates(VinC[n])
        bc_xyz.append(list(nxyz))
        N = cubit.parse_cubit_list("node", " at " + str(nxyz[0]) + " " + str(nxyz[1]) + " 0.")
        
        for n in range(0,len(N)):
            nodeEdges = cubit.parse_cubit_list("edge", "in node " + str(N[n]))
            for e in range(0,len(nodeEdges)):
                if nodeEdges[e] in EinC:
                    pass
                else:
                    cubit.cmd("cf_crease_entities add Edge " + str(nodeEdges[e]))
        
    
    #V = cubit.get_entities("vertex")[num_base_vertex:]
    
    #cubit.cmd('create group "cf_crease_entities"')
    #bc_xyz = [[] for i in range(0,len(V))]
    #for i in range(0,len(V)):
    #    #ssID = cubit.get_next_sideset_id()
    #    bc_xyz[i] = list(cubit.vertex(V[i]).coordinates())
    #    cubit.parse_cubit_list("vertex", "at " + str(bc_)
    #    N = cubit.get_vertex_node(V[i])
    #    nodeEdges = cubit.parse_cubit_list('edge','in node ' + str(N))
    #    for e in range(0,len(nodeEdges)):
    #        #cubit.cmd("sideset " + str(ssID) + " add Edge " + str(nodeEdges[e]))
    #        cubit.cmd("cf_crease_entities add Edge " + str(nodeEdges[e]))
    #    #cubit.cmd("sideset " + str(ssID) + ' name "node_' + str(N) + '_edges"')
    
    cubit.cmd('save as "mesh.cub" overwrite')
    num_elem = len(cubit.get_entities("Face"))
    return status, bc_xyz, num_elem, nlcon


def computeNonlinearConstraint(x,y):
    nlcon = numpy.zeros(len(x))
    target_surface = cubit.surface(1)
    vertex_on_surface = [False for i in range(0,len(x))]
    # First, determine whether the nonlinear constraint is satisfied
    for i in range(0,len(x)):
        vertex_on_surface[i] = target_surface.point_containment([x[i], y[i], 0.])
    # Second, determine the magnitude of the nonlinear constraint value
    #         which is the distance of the point to the closest curve
    cid = cubit.get_entities("Curve")
    for i in range(0,len(x)):
        dist = numpy.zeros(len(cid))
        pXYZ = numpy.array([x[i], y[i], 0.])
        for c in range(0,1):
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
    pathToFreqInput = "/home/christopher/optimization_project/Dakota_CFS/src/cf_run_scripts/"
    #pathToFreqInput = "/home/greg/Dakota_CFS/src/cf_run_scripts/"
    XYZ = [[bc_xyz[i][0], bc_xyz[i][1], 0.] for i in range(0,len(bc_xyz))]
    str_XYZ = str(XYZ).replace(" ","")
    py_command = "python3 " + pathToFreqInput + "freqInput.py " + "mes.json " + "-p " + str_XYZ + " " + "-n " + str(num_elem)
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

def compute_Eigenvalue():
    pathToJulia = "/home/christopher/cf/master/deps/srcs/julia/julia-1.3.0/bin/"
    #pathToJulia = "/usr/local/bin/"
    jl_command = pathToJulia + "julia " + "GenEigProb.jl"
    sys.stdout.write(jl_command + "\n")
    sys.stdout.flush()
    try:
        status = subprocess.check_call(jl_command, shell=True)
    except:
        sys.stdout.write("compute_Eigenvalue FAILED" + "\n")
        status = True
        sys.stdout.flush()
    return status

if __name__ == "__main__":
    print(sys.argv)
    paramFile = sys.argv[1]
    objFile = sys.argv[2]
    main(paramFile, objFile)
