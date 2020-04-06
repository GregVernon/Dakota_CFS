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
        error_handle(objFile, nlcon)
        return
    
    buildUSpline(2,0)
    buildSimInput(bc_xyz, num_elem)
    execute_cfs()
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

def error_handle(objFile, nlcon):
    f = open(objFile,"w+")
    f.write("ObjVal 100000000.0" + "\n")
    for n in range(0,len(nlcon)):
        f.write("nlcon_" + str(n+1) + " " + str(nlcon[n]) + "\n")
    f.close()


def write_objvalue(objFile, nlcon):
    # Get fundamental eigenvalue
    f = open("EigenValue.txt","r")
    freq = float(f.readlines()[0].strip())
    f.close()
    # Calculate objective value
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
    target_surface = cubit.surface(1)
    vertex_on_surface = [False for i in range(0,len(x))]
    for i in range(0,len(x)):
        vertex_on_surface[i] = target_surface.point_containment([x[i], y[i], 0.])
        if vertex_on_surface[i] == True:
            cubit.cmd("create vertex " + str(x[i]) + " " + str(y[i]) + " 0 on surface 1")
        
    #if any(vertex_on_surface) == False:
    #    # No pins on board, return with large objective value
    #    status = 1
    #    return status, [], []
    
    nlcon = computeNonlinearConstraint(x,y)
    sys.stdout.write("Nonlinear Constraints: ")
    sys.stdout.write(str(nlcon))
    sys.stdout.write("\n")
    sys.stdout.flush()
    
    if any(vertex_on_surface) == False:
        # No pins on board, return with large objective value and nonlinear constraint values
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
     
    cubit.cmd('create group "cf_crease_entities"')
    bc_xyz = [[] for i in range(0,len(V))]
    for i in range(0,len(V)):
        #ssID = cubit.get_next_sideset_id()
        bc_xyz[i] = list(cubit.vertex(V[i]).coordinates())
        N = cubit.get_vertex_node(V[i])
        nodeEdges = cubit.parse_cubit_list('edge','in node ' + str(N))
        for e in range(0,len(nodeEdges)):
            #cubit.cmd("sideset " + str(ssID) + " add Edge " + str(nodeEdges[e]))
            cubit.cmd("cf_crease_entities add Edge " + str(nodeEdges[e]))
        #cubit.cmd("sideset " + str(ssID) + ' name "node_' + str(N) + '_edges"')
    
    cubit.cmd('save as "mesh.cub" overwrite')
    #cubit.cmd('open "mesh.cub"')
    #cubit.cmd("regularize surf 1")
    #cubit.cmd('save as "mesh.cub" overwrite')
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
    sys.stdout.write(CFT_command)
    sys.stdout.flush()
    status = subprocess.check_call(CFT_command,shell=True)
    return status

def buildSimInput(bc_xyz, num_elem):
    #pathToFreqInput = "/home/christopher/optimization_project/Dakota_CFS/src/cf_run_scripts/"
    pathToFreqInput = "/home/greg/Dakota_CFS/src/cf_run_scripts/"
    XYZ = [[bc_xyz[i][0], bc_xyz[i][1], 0.] for i in range(0,len(bc_xyz))]
    str_XYZ = str(XYZ).replace(" ","")
    py_command = "python3 " + pathToFreqInput + "freqInput.py " + "mes.json " + "-p " + str_XYZ + " " + "-n " + str(num_elem)
    sys.stdout.write(py_command)
    sys.stdout.flush()
    status = subprocess.check_call(py_command, shell=True)
    return status

def execute_cfs():
    pathToCFS = "/home/christopher/cf/master/b_codes_with_debug/bin/"
    cfs_command = pathToCFS + "cfs " + "test.json"
    sys.stdout.write(cfs_command)
    sys.stdout.flush()
    status = subprocess.check_call(cfs_command, shell=True)
    return status

if __name__ == "__main__":
    print(sys.argv)
    paramFile = sys.argv[1]
    objFile = sys.argv[2]
    main(paramFile, objFile)
