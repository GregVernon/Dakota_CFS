import sys
from math import *

def main(inputFile, outputFile):
	x,y = importFile(inputFile)
	objVal = computeObjectiveValue(x,y)
	exportResults(objVal,outputFile)


def importFile(inputFile):
	f = open(inputFile,"r")
	fLines = f.readlines()
	x = []
	y = []
	i = 0;
	for line in fLines:
		if int(remainder(i,2)) == 0:
			x.append(float(line.strip()))
		else:
			y.append(float(line.strip()))
		i+=1
	return x,y


def computeObjectiveValue(x,y):
	objValue = 0
	for i in range(0,len(x)):
		objValue += sqrt(x[i]**2. + y[i]**2.)
	return objValue


def exportResults(objValue, outputFile):
	f = open(outputFile,"w+")
	f.write("ObjVal: " + str(objValue))
	f.close()


if __name__ == "__main__":
	inputFile = sys.argv[-2]
	outputFile = sys.argv[-1]
	main(inputFile,outputFile)
