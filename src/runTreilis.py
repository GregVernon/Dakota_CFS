#!python
import os
import sys
import numpy
from math import *

pathToTrelis = "/home/christopher/trelis/cubit_build/claro/bin"
pathToTrelis = r"C:\Program Files\Trelis 17.1\bin"
sys.path.append(pathToTrelis)

if os.name == 'nt':
  binPath = pathToTrelis #os.path.dirname(os.path.abspath(__file__))
  acisPath = r"/acis/code/bin"
  try:
    os.add_dll_directory(binPath + acisPath)
  except AttributeError:
    os.environ['path'] += ';' + binPath + acisPath

# if sys.version_info[0] < 3:
#   from cubit2 import *
# else:
#   from cubit3 import *

# pathToTrelis = "/home/christopher/trelis/cubit_build/claro/bin"

import cubit
cubit.init(['cubit', '-nojournal', '-noecho','-nobanner','-nographics'])


def main(paramFile):
    x,y = readParamFile(paramFile)
    makeGeometry(x,y)

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

def makeGeometry(x,y):
    cubit.cmd("reset")
    cubit.cmd('open "circleGeom.trelis"')
    
    for i in range(0,len(x)):
        cubit.cmd("create vertex " + str(x[i]) + " " + str(y[i]) + " 0 on surface 1")
    V = cubit.get_list_of_free_ref_entities("vertex")
    for i in range(0,len(V)):
        cubit.cmd("imprint volume all with vertex " + str(V[i]))
    cubit.cmd("delete free vertex all")
    cubit.cmd("compress ids")
    for i in range(0,len(V)):
        cubit.cmd("nodeset 1 add vertex " + str(V[i]))
    cubit.cmd("surface all size 0.2")
    cubit.cmd("mesh surf all")
    cubit.cmd("surface all smooth scheme mean ratio cpu 0.1")
    cubit.cmd("smooth surf all")
    
    cubit.cmd('create group "cf_crease_entities"')
    for i in range(0,len(V)):
        ssID = cubit.get_next_sideset_id()
        N = cubit.get_vertex_node(V[i])
        nodeEdges = cubit.parse_cubit_list('edge','in node ' + str(N))
        for e in range(0,len(nodeEdges)):
            cubit.cmd("sideset " + str(ssID) + " add Edge " + str(nodeEdges[e]))
            cubit.cmd("cf_crease_entities add Edge " + str(nodeEdges[e]))
        cubit.cmd("sideset " + str(ssID) + ' name "node_' + str(N) + '_edges"')
    buildUSpline(2,1,2)
    cubit.cmd('save trelis ' + '"mesh.trelis"' + " overwrite")




def buildUSpline(degree, continuity, method):
    if method == 1:
        cubit.cmd("imprint mesh onto body all ")
        cubit.cmd("stitch body all")
        cubit.cmd("compress")
        cubit.cmd('build uspline body all p ' + str(degree) + ' c ' + str(continuity) + ' domain "solid"')
    elif method == 2:
        cubit.cmd('build uspline from mesh p ' + str(degree) + ' c ' + str(continuity) + ' domain "solid"')

if __name__ == "__main__":
    print(sys.argv)
    paramFile = sys.argv[1]
    main(paramFile)