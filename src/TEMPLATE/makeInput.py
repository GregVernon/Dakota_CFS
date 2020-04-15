import os
import sys
import random
import numpy

def main(template_file, out_name, num_pins, bounds):
    makeInputFile(template_file, out_name, num_pins, bounds)
    makeInterface(num_pins)
    makeParamTemplate(num_pins)


def makeInputFile(template_file, out_name, num_pins, bounds):
    f = open(template_file, 'r')
    fLines = f.readlines()
    f.close()
    
    fLines = define_variables(fLines, num_pins, bounds)
    fLines = define_responses(fLines, num_pins)
    
    f = open(out_name, "w+")
    for i in range(0,len(fLines)):
        f.write(fLines[i])
    f.close()

def makeInterface(num_pins):
    f = open("interface_template.py", "r")
    fLines = f.readlines()
    f.close
    
    fLines = define_qois(fLines, num_pins)
    
    f = open("interface.py", "w+")
    for i in range(0,len(fLines)):
        f.write(fLines[i])
    f.close()


def makeParamTemplate(num_pins):
    f = open("params.template", "w+")
    for i in range(0,num_pins):
        f.write("{x" + str(i+1) + "}" + "\n")
        f.write("{y" + str(i+1) + "}" + "\n")
    f.close()


def define_qois(fLines, num_pins):
    qoi_str = 'qois = [qoi.QoiAnchor("objective", 1, qoi.FIELDS, 1, qoi.FIELDS, qoi.AFTER, "ObjVal"),' + "\n"
    for i in range(0,num_pins):
        qoi_str += " "*8 + 'qoi.QoiAnchor("nlcon_' + str(i+1) + '", 1, qoi.FIELDS, 1, qoi.FIELDS, qoi.AFTER, "nlcon_' + str(i+1) + '"),' + "\n"
    qoi_str += " "*8 + "]"

    for i in range(0,len(fLines)):
        fLines[i] = fLines[i].replace("#{define_qois}", qoi_str)
    return fLines


def define_variables(fLines, num_pins, bounds):
    if bounds[0] >= 0.:
        x_lower_bound_str = "+" + str(bounds[0])
    else:
        x_lower_bound_str = str(bounds[0])
    
    if bounds[1] >= 0.:
        x_upper_bound_str = "+" + str(bounds[1])
    else:
        x_upper_bound_str = str(bounds[1])
    
    if bounds[2] >= 0.:
        y_lower_bound_str = "+" + str(bounds[2])
    else:
        y_lower_bound_str = str(bounds[2])
    
    if bounds[3] >= 0.:
        y_upper_bound_str = "+" + str(bounds[3])
    else:
        y_upper_bound_str = str(bounds[3])
    
    for i in range(0, num_pins):
        if i == 0:
            var_name_str  = '"x' + str(i+1) + '"' + " " + '"y' + str(i+1) + '"'
        else:
            var_name_str += " " + '"x' + str(i+1) + '"' + " " + '"y' + str(i+1) + '"'    
    
    for i in range(0, num_pins*2, 2):
        xInit = (bounds[1] - bounds[0]) * numpy.random.random() + bounds[0]
        yInit = (bounds[3] - bounds[2]) * numpy.random.random() + bounds[2]
        
        if xInit >= 0.:
            xInit_str = "+" + str(xInit)
        else:
            xInit_str = str(xInit)
        
        if yInit >= 0.:
            yInit_str = "+" + str(yInit)
        else:
            yInit_str = str(yInit)
        
        if i == 0:
            lower_bound_str = x_lower_bound_str + " " + y_lower_bound_str
            upper_bound_str = x_upper_bound_str + " " + y_upper_bound_str
            init_point_str  = xInit_str + " " + yInit_str + " "
        else:
            lower_bound_str += " " + x_lower_bound_str + " " + y_lower_bound_str
            upper_bound_str += " " + x_upper_bound_str + " " + y_upper_bound_str
            init_point_str  += " " + xInit_str + " " + yInit_str
    
    for i in range(0, len(fLines)):
        fLines[i] = fLines[i].replace("#{num_vars}", str(num_pins*2))
        fLines[i] = fLines[i].replace("#{initial_point}", init_point_str)
        fLines[i] = fLines[i].replace("#{lower_bounds}" , lower_bound_str)
        fLines[i] = fLines[i].replace("#{upper_bounds}" , upper_bound_str)
        fLines[i] = fLines[i].replace("#{var_names}", var_name_str)
    return fLines


def define_responses(fLines, num_pins):
    for i in range(0, num_pins):
        if i == 0:
            nl_ineq_const_str  = '"nlcon_' + str(i+1) + '"'
        else:
            nl_ineq_const_str += " " + '"nlcon_' + str(i+1) + '"'
    
    for i in range(0,len(fLines)):
        fLines[i] = fLines[i].replace("#{num_nl_ineq_const}", str(num_pins))
        fLines[i] = fLines[i].replace("#{nl_ineq_const}", nl_ineq_const_str)
    
    return fLines




if __name__ == "__main__":
    template_file = sys.argv[1]
    out_name = sys.argv[2]
    num_pins = int(sys.argv[3])
    xmin = float(sys.argv[4])
    xmax = float(sys.argv[5])
    ymin = float(sys.argv[6])
    ymax = float(sys.argv[7])
    main(template_file, out_name, num_pins, [xmin, xmax, ymin, ymax])


