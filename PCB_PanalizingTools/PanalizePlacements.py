
# Panalize Placements
# Kyle Mayer
# February 2020

# this is a very crude tool- it just takes a JLC compatible placement file and BOM, 
# and copies the placements X*Y times, applying fixed offsets (so no rotating 
# individual boards, and only rectangular grids are supported). It adds a third 
# digit to the Ref Des for each extra board, which designates which panel it is on 
# (ie, C1 becomes C101 on the second panel), so this also breaks if you have more 
# than 100 of any part type. It also modifies the BOM to include the references to the extra parts.
# it is farily limited in scope, but has it's uses.

# much of this is hardcoded. It works so shush =O
# BOM columns should be: Comment, designator, footprint, lcsc (only one that matters is designator in second column)
# placement should be: Designator, Mid X, Mid Y, Layer, Rotation
# both files should have a one-row header.

import csv
import re
refDesSplitter = re.compile("([a-zA-Z]+)([0-9]+)") 

# ---------------------------- USER VARIABLE, UPDATE THIS BEFORE RUNINNG ------------------------------------------------
xShift = 13.0 # in mm. How far to move each panel
yShift = 24.59

numRepeatX = 6 # how many panels are there?
numRepeatY = 4

xOffset = 0.0 # in mm. Where is the first panel? If you added rails or something else that caused
yOffset = 0.0 # the first board to no longer be at the origin, set that here

bomFileName = "GLEAM_SmartAccelLEDDriver_ATMEGA328_JLC.csv"
placementFileName = "KM_GLEAM_SmartAccelATMEGA328_JLCPLACEMENT.csv"

# ------------------------------------- END USER VARIABLES -------------------------------------------------------------

numBoards = numRepeatX * numRepeatY

# first, update the merged placements data
with open(placementFileName, newline='') as csvfile:
	placementReader = csv.reader(csvfile, delimiter=',')
	with open('combinedPLACEMENT.csv', 'w', newline='') as csvfile:
		placementWriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
		booFirstLine = True
		for row in placementReader:
			boardCounter = 0
			if booFirstLine: # the first line is a header, we don't want to copy or modify it
				placementWriter.writerow(row)
				booFirstLine = False
			else:
				for countX in range(numRepeatX):
					for countY in range(numRepeatY): # for each row, we want to copy it once for each board, doing some math
						# on it for each entry
						(refDesLetter, refDesNumber) = refDesSplitter.match(row[0]).groups() # split C5 into [C,5]
						refDesNumber = int(refDesNumber) + 100*boardCounter
						boardCounter = boardCounter + 1
						newRow0 = str(refDesLetter)+str(refDesNumber) # we have hardcoded the column order format. This is the ref des
						newRow1 = float(row[1]) + countX*xShift + xOffset # we have hardcoded the column order format. This is the X dimension.
						newRow2 = float(row[2]) + countY*yShift + yOffset # we have hardcoded the column order format. This is the Y dimension

						rowOutput = [] # so we don't overwrite the original row- we may still need it for further loops
						# this is a total hack. I don't want to talk about it. need a for loop here.
						rowOutput.append(str(newRow0))
						rowOutput.append(str(newRow1))
						rowOutput.append(str(newRow2))
						rowOutput.append(str(row[3]))
						rowOutput.append(str(row[4]))
						placementWriter.writerow(rowOutput)
    
# next, update the merged BOM data
with open(bomFileName, newline='') as csvfile:
	bomReader = csv.reader(csvfile, delimiter=',')
	with open('combinedBOM.csv', 'w', newline='') as csvfile:
		bomWriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
		booFirstLine = True
		for row in bomReader:
			#print(row)
			boardCounter = 0
			if booFirstLine: # the first line is a header, we don't want to copy it
				bomWriter.writerow(row)
				booFirstLine = False
			else:
				# ok, the only entry we care about is the reference designator. It needs to be broken down and incremented.
				# it may look like: "C1,C5-C10". for two boards, this should become "C1, C101, C5-C10, C105-110" or something similar
				refDesList = row[1].split(",") # get the separate clusters
				newRefDesList = []
				for refDesCallout in refDesList:
					singledRefDes = refDesCallout.split("-") # get the start and end of clusters
					if len(singledRefDes) == 1: # these were single ones in the list, not clusters
						(refDesLetter, refDesNumber) = refDesSplitter.match(singledRefDes[0]).groups() # split C5 into [C,5]
						for counter in range(numBoards):
							newRefDesList.append(refDesLetter+str(int(refDesNumber)+100*counter))
					else: # could make this able to handle arbitrary lengths, but with ref des its always 1 or 2 (C1, or C1-C5)
						# these were double ones in the list.
						(refDesLetter0, refDesNumber0) = refDesSplitter.match(singledRefDes[0]).groups() # split C5 into [C,5]
						(refDesLetter1, refDesNumber1) = refDesSplitter.match(singledRefDes[1]).groups() # split C5 into [C,5]
						for counter in range(numBoards):
							newRefDesList.append(refDesLetter0+str(int(refDesNumber0)+100*counter)+"-"+refDesLetter1+str(int(refDesNumber1)+100*counter))

				# reassembling the mess we've created: taking a list and turning it into a string with commas in the right place . . . 
				# this can probably be done better with a library somewhere.
				finalRefDes = ""
				for entryNumber in range(len(newRefDesList)):
					finalRefDes = finalRefDes + newRefDesList[entryNumber]
					if entryNumber < len(newRefDesList)-1:
						finalRefDes = finalRefDes + ","
				row[1] = finalRefDes

				bomWriter.writerow(row) # and finally, updating the output file
