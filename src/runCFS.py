import sys
from math import *

def main(inputFile, outputFile):
	x = importFile(inputFile)
	objVal = computeObjectiveValue(x)
	exportResults(objVal,outputFile)


def importFile(inputFile):
	f = open(inputFile,"r")
	fLines = f.readlines()
	x = []
	for line in fLines:
		x.append(float(line.strip()))
	return x


def computeObjectiveValue(x):
	objValue = 0
	for i in range(0,len(x)):
		objValue += sqrt(x[i]**2.)
	return objValue


def exportResults(objValue, outputFile):
	f = open(outputFile,"w+")
	f.write("ObjVal: " + str(objValue))
	f.close()


if __name__ == "__main__":
	inputFile = sys.argv[-2]
	outputFile = sys.argv[-1]
	main(inputFile,outputFile)
