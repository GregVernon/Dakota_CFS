#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import math
import os
import sys
import ast
import re
import numpy as np
#import matplotlib.pyplot as plt
import pprint


in_opts =  { "thickness": 0.025,
             "elems_per_length": 1,
             "deg_l": 2,
             "cont_l": 1,
             "pin_tol": 0.001,
             "file_name": "test" }

in_json = [ { "name": "patch_creation_surface_square", "patch_id": 1, "width": 5, "refinement": { "degrees": [2,2], "num_elems": [2,2] }, "positioning": { "origin": [0,.5,0] } },
            { "name": "domain_spline_solid", "domain_id": 1, "patch_id": 1 },
            { "name": "material_isotropic_elastoplastic", "material_id": 1, "E": 100000., "nu": 0.33, "rho": 0.00001, "thermal_expansion": 0.0000093, "yield_type": "J2", "effective_plastic_work_measure": "plastic_work", "plastic_work_threshold": 0  },
            { "name": "formulation_solid", "formulation_type": "solid_3d", "quadrature": "QP1", "formulation_id": 1, "material_id": 1 },
            { "name": "part", "part_id": 1, "formulation_id": 1, "subdomain_ids": [ 1 ] },
            { "name": "subdomain_output_field", "subdomain_output_id": 1, "subdomain_ids": [1], "function_temporal_id": 1, "field_types": [ "displacement" ], "delta_time": 0, "file_name_prefix": "output", "file_type": "vtk", "sample_type": "BEZIER"  },
            { "name": "function_temporal_constant", "function_temporal_id": 1, "value": 1, "birth": 0, "death": 1e20, "tol": 1e-4 },
            { "name": "version", "version": [0,0,0,3] },
            { "name": "subdomain_elems", "subdomain_id": 1, "domain_elem_segments": [ [1,0,-1], [1,1,-1],[1,2,-1],[1,3,-1] ] } ]
in_geom = { "num_elems": 4, "pin_locations": [ [ 0, 0, 0 ], [ .5, .5, .5 ] ] } #patch sizing indexed by patch_id 
def generateSolidSimulations( input_json, input_options, input_geom ):
    patch_sizing = input_geom["num_elems"]
    file_name = input_options["file_name"]

    thickness = input_options["thickness"]
    length = thickness
    num_elem_l = np.int(np.ceil( length * input_options["elems_per_length"] ))
    length *= input_geom["normal"]
    const_temporal_func_id = -1
    problem_id = -1
    part_ids = []
    domain_offset = 0
    modified_json = input_json.copy()
    add_json = []
    element_subdomain = -1
    for card in modified_json:
        if "name" in card:
            #convert interior surface subdomains to solid
            if card["name"] == "subdomain_elems":
                if "domain_elem_segments" in card:
                    new_segments = []
                    for elem in card[ "domain_elem_segments" ]:
                        if elem[2] == -1: #this is an interior
                            element_subdomain = card["subdomain_id"]
                            domain_id = elem[0] # NOTE this assumes that the patch_id is the same as its domain_id
                            #print(patch_sizing)
                            #print(domain_id)
                            domain_offset = patch_sizing #this gives you the number of elements on the cross section
                            elem_id = elem[1]
                            for i in range(0, num_elem_l):
                                new_segments.append( [ domain_id, i * domain_offset + elem_id, -1 ] )
                        else: print("EDGES DETECTED AND IGNORED") #raise Exception("selection of edges not supported in conversion to solid simulation")
                    card[ "domain_elem_segments" ] = new_segments #replace with the new solid doamin segments
                else: raise Exception("Subdomain_elems has no attribute: domain_elem_segments")

            #update the domain_spline with the new patch
            if card["name"] == "domain_spline_solid":
                if "patch_id" in card:
                    card["patch_id"] += 1000 #increment the patch id by 1000 to point at the new solid geometry that will be created
                else: raise Exception("domain_spline_solid has no attribute: patch_id")
                card["node_map"] = { "tol": 1e-8 }
            if card["name"] == "domain_spline_shell":
                card["name"] = "domain_spline_solid"
                if "patch_id" in card:
                    card["patch_id"] += 1000 #increment the patch id by 1000 to point at the new solid geometry that will be created
                else: raise Exception("domain_spline_solid has no attribute: patch_id")
                card["node_map"] = { "tol": 1e-8 }
                if "thicknesses" in card:
                    del card["thicknesses"]
            if card["name"] == "patch" or card["name"] == "patch_creation_surface_square":
                if "patch_id" in card:
                    patch_id = card["patch_id"] + 1000 #increment the patch_id by 1000 (so that there is no overlap)
                    patch_id_origin = card["patch_id"]
                    extrude = [ 0, 0, length ]
                    refinement = { "degrees": [ input_options["deg_l"] ], "smoothnesses": [ input_options["cont_l"] ], "num_elems": [ num_elem_l ] }
                    add_json.append( {
                        "name": "patch_operation_extrude",
                        "patch_id": patch_id,
                        "patch_operation_id": 1,
                        "patch_id_origin": patch_id_origin,
                        "extrude": extrude,
                        "refinement": refinement
                    } )

        else: raise Exception("card has no attribute: name")


    #add a constant temporal function if none was found (for use in the fixed B.C.)
    if const_temporal_func_id == -1:
        add_json.append( {
            "name": "function_temporal_constant",
            "function_temporal_id": 1000,
            "value": 1,
            "birth": 0,
            "death": 1e20,
            "tol": 1e-4
        } )
        const_temporal_func_id = 1000

    add_json.append({
          "uuid": "923e37b0-a282-11e9-bb14-17d2f43a55c2",
          "name": "part",
          "formulation_id": 1,
          "part_id": 1,
          "subdomain_ids": [ element_subdomain ]
      })
    part_ids.append(1)

    #add a problem if none was found
    if problem_id == -1:
        problem_id = 1
        add_json.append( {
            "name": "problem",
            "control_linear_solver": {
                "options_from_command_line": False,
                "solver_type": "superlu"
            },
            "problem_id": problem_id,
            "part_ids": part_ids,
            "control_timestep_id": 1
        })

        add_json.append({
            "name": "control_timestep_implicit_dynamic_2nd_order",
            "desc": "",
            "control_timestep_id": 1,
            "control_time_integration_id": 1
        })
        add_json.append({
            "name": "control_time_integration_generalized_alpha",
            "control_time_integration_id": 1,
            "rho_inf": 1.0
            })

    add_json.append({
          "name": "material_isotropic_linear_elastic",
          "material_id": 1,
          "E": 110316.16,
          "nu": 0.33,
          "rho": 0.0000089427534
      })


    add_json.append({
          "name": "formulation_solid",
          "formulation_type": "solid_3d",
          "quadrature": "QP1",
          "formulation_id": 1,
          "material_id": 1
      })

    #add a control model
    add_json.append({
        "name": "control_model",
        "control_time": {
            "initial_time_step": 1,
            "termination_time": 1
        },
        "enable_parent_basis": False,
        "enable_output": True,
        "enable_output_restart": False,
        "output_restart_file_name_prefix": "result",
        "output_restart_delta_t": 0,
        "output_restart_delta_time_step": 1,
        "output_restart_based_on_time_step": False,
        "control_problem": problem_id,
    })

    #add boundary conditions
    subdomain_nodal_value_ids = []
    pin_tol = input_options["pin_tol"]
    function_temporal_id = 1000
    for i, location in enumerate( input_geom["pin_locations"] ):
        subdomain_id = i + 2000
        parameters = location + [ location[0], location[1], length ]
        add_json.append( {
            "name": "subdomain_nodes_position",
            "subdomain_id": subdomain_id,
            "geometric_object": "Line",
            "relative_position": "On",
            "parameters": parameters,
            "tol": pin_tol } )
        
        subdomain_nodal_value_id = subdomain_id
        disp = { "enabled": True, "value": 0.0 }
        add_json.append({
            "name": "subdomain_nodal_dva",
            "subdomain_nodal_value_id": subdomain_nodal_value_id,
            "subdomain_ids": [subdomain_id],
            "dva_type": "DISPLACEMENT",
            "UX": disp,
            "UY": disp,
            "UZ": disp,
            "function_temporal_id": const_temporal_func_id
        })
        subdomain_nodal_value_ids.append( subdomain_nodal_value_id )

    add_json.append({
        "name": "problem_boundary_condition",
        "problem_id": problem_id,
        "subdomain_nodal_value_ids": subdomain_nodal_value_ids
    })

    #add the new cards to our modified simulation file
    for card in add_json:
        modified_json.append(card)

    file_out = open( str( file_name ) + ".json", 'w' )
    json.dump( modified_json, file_out, indent = 5 )
    file_out.close()



    #Gather domain spline information
    #return input_json


in_filename = sys.argv[1]
in_json = []
with open( in_filename ) as json_file:
    in_json = json.load(json_file)

#print( in_json )

in_geom = { "num_elems": 0, "pin_locations": [[]], "normal": 1 }
for i in range(2, len(sys.argv)):
    if sys.argv[i] == "-p":
        in_geom["pin_locations"] = ast.literal_eval(sys.argv[i+1])
    if sys.argv[i] == "-n":
        in_geom["num_elems"] = ast.literal_eval(sys.argv[i+1])
    if sys.argv[i] == "-o":
        in_geom["normal"] = ast.literal_eval(sys.argv[i+1])
print(in_geom)
generateSolidSimulations( in_json, in_opts, in_geom )
