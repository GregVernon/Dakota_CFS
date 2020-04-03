#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import ast
import re
import numpy as np
import matplotlib.pyplot as plt
import pprint


# Take a subdomain from 2d and convert it to a subdomain in 3d (for a 1d-2d tp solid)


def computeSubdomain( domain_id, peids, param_bound, elem_xsec, l ):
    subdomain = []
    for peid in peids:
        for i in range( 0, l ):
            subdomain.append( [ domain_id, i * elem_xsec + peid, param_bound ] )
    return subdomain

def extractPeids( subdomain_elems ):
    peids = []
    for x in subdomain_elems:
        peids.append( x[1] )
    return peids



deg_l = 2
cont_l = deg_l - 1
max_cont_x = 1
thickness = 1


#elem_l_vec = [ 10, 20, 30, 40, 50 ]
elem_l_vec = [ 1 ]

for elem_l in elem_l_vec:

    json_data = []

    #THIS FILE SHOULD INCLUDE:
    #Patch, Uspline, SubdomainElems, SubdomainNodes (for the c0 nodes)
    #Subdomain 1 should include all the elemnts
    #This comes from  a script that runs ./translator/cft
    json_data.append({
          "name": "include",
          "uuid": "",
          "desc": "",
          "file_name": "freqInput.json"
      })

    json_data.append({
          "name": "version",
          "uuid": "",
          "desc": "",
          "version": [ 0, 0, 0, 3 ]
      })


    json_data.append({
          "uuid": "4bf74d10-a281-11e9-bb14-17d2f43a55c2",
          "name": "material_isotropic_elastoplastic",
          "plastic_work_threshold": 0,
          "effective_plastic_work_measure": "plastic_work",
          "yield_type": "J2",
          "material_id": 1,
          "desc": "3 - Copper",
          "E": 110316.16,
          "nu": 0.33,
          "rho": 0.0000089427534
      })

    json_data.append({
          "uuid": "923e37b0-a282-11e9-bb14-17d2f43a55c2",
          "name": "part",
          "formulation_id": 1,
          "desc": "1 - Adhesive Part",
          "part_id": 1,
          "subdomain_ids": [ 1 ]
      })

    json_data.append({
          "uuid": "c3c3d470-a282-11e9-bb14-17d2f43a55c2",
          "name": "formulation_solid",
          "formulation_type": "solid_3d",
          "quadrature": "QP1",
          "desc": "1 - form",
          "formulation_id": 1,
          "material_id": 1
      })


    json_data.append({
          "uuid": "d84b28c0-a292-11e9-bb14-17d2f43a55c2",
          "name": "problem",
          "control_linear_solver": {
              "options_from_command_line": False,
              "solver_type": "superlu"
          },
          "problem_id": 1,
          "desc": "1",
          "part_ids": [
              1
          ],
          "control_timestep_id": 1
      })

    json_data.append({
          "name": "control_timestep_quasistatic",
          "desc": "",
          "control_timestep_id": 1
      })

    json_data.append({
          "uuid": "ee001ae0-a292-11e9-bb14-17d2f43a55c2",
          "name": "control_model",
          "control_time": {
              "initial_time_step": 1,
              "termination_time": 1,
          },
          "enable_parent_basis": False,
          "enable_output": True,
          "enable_output_restart": False,
          "output_restart_file_name_prefix": "result",
          "output_restart_delta_t": 0,
          "output_restart_delta_time_step": 1,
          "output_restart_based_on_time_step": False,
          "control_problem": 1,
          "desc": "1"
      })

    json_data.append({
        "name": "patch_operation_extrude",
        "patch_id": 2,
        "patch_operation_id": 1,
        "patch_id_origin": 1,
        "extrude": [ 0, 0, thickness ],
        "refinement": { "degrees": [ deg_l ], "smoothnesses": [ cont_l ], "num_elems": [ elem_l ] }
    })

    json_data.append({
          "uuid": "f5287210-a33a-11e9-85e8-dfa424b7278f",
          "name": "domain_spline_solid",
          "use_parent_basis": False,
          "domain_id": 1,
          "patch_id": 2,
          "node_map": {
              "tol": 0.000001
          }
      })


    #kaptonPeids = extractPeids( Kapton )
    #adhesivePeids = extractPeids( Adhesive )
    #copperPeids = extractPeids( Copper )
    #allPeids = kaptonPeids + adhesivePeids + copperPeids

    #Subdomain1
    json_data.append({
          "name": "subdomain_elems",
          "desc": "kapton",
          "subdomain_id": 1,
          "domain_elem_segments": computeSubdomain( 1,  kaptonPeids, -1, xSecN, elem_l )
      })


    json_data.append({
          "uuid": "da4ccfb0-a293-11e9-bb14-17d2f43a55c2",
          "name": "subdomain_output_field",
          "file_name_prefix": "freqOut" + str( xSecN ) + "_xC" + str(max_cont_x) + "_L" + str( elem_l ) + "_P" + str(deg_l),
          "file_type": "vtk",
          "sample_type": "BEZIER",
          "cache_basis_evals": True,
          "include_elem_outlines": False,
          "solution_type": "current",
          "subdomain_ids": [ 1 ],
          "subdomain_output_id": 1,
          "desc": "1",
          "function_temporal_id": 1,
          "field_types": [
              "displacement",
              "vm_stress"
          ],
          "delta_time": 0
      })

    json_data.append({
          "uuid": "c8bc32e0-a293-11e9-bb14-17d2f43a55c2",
          "name": "function_temporal_constant",
          "desc": "1",
          "function_temporal_id": 1,
          "value": 1,
          "birth": 0,
          "death": 100000000000000000000,
          "tol": 0.0001
      })

    f = open( "freqInput" + str( xSecN ) + "_xC" + str(max_cont_x) + "_L" + str( elem_l ) + "_P" + str(deg_l) + ".json", 'w' )
    json.dump( json_data, f, indent = 5)

    f.close()
