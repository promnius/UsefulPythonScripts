
# A basic python script for generating Gcode for cutting open center barley twists on a 4 axis CNC router 

# TODO: 
# save Gcode to file
# functions/ unit tests
# Adjust profile diameter for following profile
# vectorize profile diameter for variable diameter
# vectorize profile num sides for variable profile shapes?????
# optional lead-ins (not expected to be supported any time soon)
# efficiency improvements: cutting backwards on the back stroke, keeping the tool down (but OUT OF THE WAY), all low priority at the moment

# limitations/ usage:
# designed to generate Gcode for creating an open center barley twist on a fourth axis CNC router
# WITHOUT predrilling the hole, WITHOUT a custom barley twist bit, with the goal of having the barley
# twist column be symetric all the way around (ie, the backside does not have the concave cut of a center drill,
# and a circular profile is truly circular). The lack of a custom barley twist bit allows this to be used in harder
# materials like stone with a diamond grinding bit, and means you don't need a custom bit for every size you can think of.

# terminology: for this project, the A axis spins the part, Z is height up and down, Y is the length of the rotated part,
# and X is side to side (the dimension normally hidden from a rotory part, where you always cut on center)

# there are many tool paths that can achieve a barley twist. This one uses the SIDE of the cutter, offsetting the cutter
# in the X direction, then cutting a spiral (A-Y move). It then repeats this with a new A-X start. The Z values are never 
# critical, since we actually use the side of the cutter- they just need to be deep enough (and get there gradually enough
# for the depth of cut). As such, you can use a round or square cutter. The smaller the cutter, the less lost material (and
# tighter of turns you can generate), but larger diameters will not be possible, since the tool needs to be long enough.

# other possible tool paths: 
# 1: a full A-X-Y surface milling operation (a standard xy surface milling that is then repeated
# at many angular steps). Technically, this is the most comprehensive tool path possible and if a twist can be cut with
# a four axis machine (and defined by a solid model), this will cut it. However, completely impractical since the toolpath
# times will be days, weeks, or even months.
# 2: an A-Y spiral with no X exposed (centerline cutting). Only works with a barley twist or with the perfect round bit size,
# and even then suffers from areas of low resolution. This is the standard way I've seen barley twists done, usually pre-drilling
# holes. The profile is not round/ not controllable, and a custom bit is needed, but it is potentially faster (less cut time)
# than my method.
# 3: a standard A-Y surface milling operation with no X exposed. Works acceptably for a barley twist with NO OPEN CENTER, 
# but besides that is quite powerful- it can do variable diameter, arbitrary profiles, all sorts of 3D detailing, etc-
# if you can model it (and there's no hole), you can cut it.

# this script can do any number of starts, but does not check to see if tool will gouge one of the other starts
# while cutting the current one, ie, trying 10 tightly wound starts with a giant cutter will probably not work, but
# this script will not error check. It also does no error checking for tool length or tool cut length. be warned.

# (0,0,0,0) is defined as the bottom of the twist (Y moving away), but the tool does not compensate in Y so it will actually cut
# the tool radius below this value, center of the rotary axis in X (duh), center of the rotary axis in Z (NOT top of the part,
# which allows for zeroing against the table rather than the part, and not needing to worry about not perfectly round stock),
# and zero for A probably doesn't matter, but will be the center of the start of the first twist unless manually overridden.

# this script expects you to prepare the stock to be circular, just slightly larger than the desired OD of the twist (how much depends
# on shape- if doing something like a square or circular profile, more extra material is needed to make sure the flat face is completed,
# since the ACTUAL OD will be slightly larger- you specify OD based on the distance between the spirals, not the tips)

# Possible things you could want a barley twist to do:
# open center (required for this script- it's easy otherwise)
# n-starts (supported, but the clearance requirements get dicey after 3 or 4, 5 starts would require very thin profiles. This is a limitation
	# of milling with the side of the cutter)
# arbitrary barley profile (convex simple shapes supported, circles approximated by many sided shape. This is a limitation of using the side of the cutter)
# sliding vs. following profile (sliding supported, following can be approximated with the correctly distorted
	# shape, IF the twist speed is fixed. Note- I may have found a solution to this?)
# twist speed, inclduing variable speed (variable speed supported, included a reversal of direction mid barley twist)
# twist diameter, including variable diameter (supported)
# arbitrary barley profile rotation, ie, barley profile rotates independent of barley twist (NOT SUPPORTED YET! - but could be)
# arbitrary 3D (bas relief) or 2D (text, etc) engraved on column. Note that arbitrary detailing on the back of a column is not
	# always possible for an arbitrary number of twists on a 4 axis machine, and may require cutting much deeper than the radius 
	# (such as for 3 twists). (NOT SUPPORTED- BUT, it probably wouldn't be too hard to hack Vectric Aspire to do this- just carve
	# a standard XY raster, but between each Y move, also rotate the A axis so the front of the twist is always pointing UP. Also
	# add in a round base in Vectric so it naturally wraps to the barley column. Text is a bit trickier, since you need 4 axis toolpaths-
	# it needs to conform to the AZ surface as well as shape the letters in XY. But for simple shapes, this may be programatically doable.)
# NO need for a relief band at top and bottom (supported natively by the use of a standard cutter instead of a barley twist cutter)
# variable column shape/ diameter, ie, having a triangle column transform into a square column, and then get thicker. (yea . . . not happening.
	# Not unless the inside edge is manually defined for every A-Y cut path.)

import math

def main():
	# User Machine setup variables (all units in inches unless specified):
	toolDiameterUserInput = .25
	depthOfCut = .25
	numDepthCutsUserInput = 3 # it's kind of weird to specify both number of depth cuts AND depth of cut, but I'm being lazy and not doing the math to figure
		# out where the physical part starts (and if I did, you'd have to tell me more about the stock shape), since it can be a bit complicated for the
		# geometry we're starting with. I could feed from the very top plane of the part, but when cutting on the edge this would be a lot of wasted time.
		# so instead, you tell me how many passes to take and how much to take on each one, so if you say .25" and 4 passes, the first pass will start .75"
		# off the finished target, then cut .5" away, .25" away, and finally on the target. Is .75" a good distance away to start? I don't know, it depends
		# on your stock geometry and the shape of barley twist you're trying to cut. You can always make this number extra large for safety, you'll just waste
		# time cutting air. If you find you cut lots of air before the first cut takes place, try lowering this.
	agressiveCutting = True # If set to true, depth of cut will only apply on certain A-Y spirals, since previous A-Y spirals have probably hogged out
		# most of the material we are about to try cutting. As such, it will then plunge to full depth for these cuts. There's not a lot more control here,
		# but this is a nice option to boost speed (possibly by a lot!) without using a deep depth of cut. Note there is no error checking to see how much
		# material is ACTUALLY being removed, so depending on settings and bit diameter, this may get you into trouble. be advised, be careful, and consider
		# running in foam first.
	finishingPasses = [.01, 0] # this is a list of the number of passes to take, and the amount of material to leave on each pass, so the last entry should always
		# be zero, and if you want no finishing passes you can just enter [0]. If you want two finishing passes, you could go [.01,.003,0], for example. Note
		# they are cut in order with no sorting, so [0,.01] wouldn't make much sense.
	spiralFeed = 10 # inches per minute. Note this is approximate, since we actually use G93 for faster simultaneous A axis moves, and we fudge some of the math.
	plungeFeed = 2 # currently, this code does not support lead in cuts. It has been investigated and the basic idea is there, but for now it just plunges.
		# use a center cutting bit, optionally use the Z level roughing to reduce stress, use finishing passes to avoid plunge gouges, and use this parameter
		# to slow down the plunges.
	spindleSpeed = 25000 # rpm. You could probably set this manually, but I'll be nice and throw a G command in for people who's machines support this.

	# User Barley Twist setup variables (all units in inches unless specified):
	numTwists = 2
	# NOTES ABOUT VECTORS. There is very little error checking here, strange results may occur if the Z values are not 
	# continuously increasing, and it will error out if the same Z value exists twice. This really shouldn't be an issue.
	# from a python standpoint, they MUST be double lists (a list of points, where the point is a list of numbers), even
	# if only one fixed value is desired. This could be wrapped up in a class someday. Also, for all vector quantities, if
	# you can keep your first point at least .100" from 0, and your last point at least .100" from the end, that will help
	# with lead ins- the lead ins will only take place up until the first Y point, because I'm lazy and the math starts getting
	# painful.
	twistDiameterVector = [[2,10]] # inner diameter vector. If not changing twist diameter, this can be a single value pair [x,y] where Y is the max length.
		# otherwise, this is a list of points specifying the vector. Each point applies from the start to the point, so the first diameter is straight
		# from y=0 to the y value, if a y=0 point is not supplied
	twistRateVector = [[-.25,10]] # twists per inch, so larger number is a tighter pitch, and fractional numbers are common. Supply a single value pair for a fixed 
		# twist rate [twist_per_inch,y] where Y is the max length. Negative numbers mean twist the other way, and yes, crossing over from positive to
		# negative IS supported. EDGE CASE: IS 0 HANDLED CORRECTLY? Applies from the start up to the point, then the next one takes over.
	length = 10 # length of the twist. Note this is the authoritive value, so this is how far the cutter will travel in the Y axis. If the final points
		# of the diameterVector and twistRateVector do not have this Y value, they will continue on with their last applied point. If they extend beyond this
		# point, they will be cut short.
	# COULD BE VECTORIZED (WITH SOME EFFORT) FOR VARIABLE PROFILE SHAPE
	numProfileFaces = 8 # so 4 for a square etc. A circle is approximated by a large number such as 16 or 32
	# COULD BE VECTORIZED FOR VARIABLE PROFILE DIAMETER!!
	profileDiameter = .5 # a circle that is enclosed by a geometric shape where the flats of the shape touch the circle. For a circle approximation (many sides),
		# this is the diameter. For a square, this is the side length. Note it's a bit funny for a triangle, as the triangle may end up being much larger than
		# planned.
	slidingOrFollowing = True # true for following, false for sliding. Note with following turned on, you MUST make any changes in twistRate via a large number
		# of small points (ie, a rounded transition), since otherwise linear extrapolation of the two end points will cause either gouging or funny steps in
		# the part.

	# Advanced user setup variables (can usually be left alone, includes barley twist setup and machine setup variables):
	twistStartAngles = None # if none, each twist will be evenly spaced around the base. Otherwise, you can use this to do interesting things like have 2 twists
		# that both start on the same side. You specify it as a list of start angles. if the length of this list is NOT the same as numTwists, strange things
		# may happen. You've been warned. In degrees.
	profileStartAngle = 0 # 0 will always place a flat face outward, but you can also specify a degree start angle if, for instance, you want the point of
		# a triangle pointed outwards.
	ZrapidHeight = "AUTO_CALCULATE" # if you didn't make your stock circular to start with . . . shame on you. But you can maybe play with this value to compensate. Note cut
		# depth is still from the nominal surface, so the first cut may be very heavy if you have extra material.
	debug = True # just for script debugging, will mess up the Gcode potentially. If correctly formated, this can be left on to make the Gcode more human readable.
	zDepthOverExtend = .05 # how far below the profile do we go while cutting? Typically, this value doesn't matter. Too large and we remove more material,
		# could run out of cutting length on the tool, or could gouge a design on the backside. Too small and we could fail to finish the cut, especially
		# while using rounded nose tools or cutting profiles with very few sides like squares and triangles (they have the 'longest' corners)

	generateBarleyTwistGcode(toolDiameterUserInput = toolDiameterUserInput, depthOfCut = depthOfCut, numDepthCutsUserInput = numDepthCutsUserInput, 
		agressiveCutting = agressiveCutting, finishingPasses = finishingPasses, spiralFeed = spiralFeed, plungeFeed = plungeFeed, 
		spindleSpeed = spindleSpeed, numTwists = numTwists, twistDiameterVector = twistDiameterVector, 
		twistRateVector = twistRateVector, length = length, numProfileFaces = numProfileFaces, profileDiameter = profileDiameter, 
		slidingOrFollowing = slidingOrFollowing, twistStartAngles = twistStartAngles, profileStartAngle = profileStartAngle, 
		ZrapidHeight = ZrapidHeight, zDepthOverExtend = zDepthOverExtend, debug = debug)

def generateBarleyTwistGcode(toolDiameterUserInput = .25, depthOfCut = .25, numDepthCutsUserInput = 3, agressiveCutting = True, 
	finishingPasses = [.01, 0], spiralFeed = 10, plungeFeed = 2, spindleSpeed = 25000, numTwists = 2, twistDiameterVector = [[2,10]], 
	twistRateVector = [[-.25,10]], length = 10, numProfileFaces = 8, profileDiameter = .5, slidingOrFollowing = True, 
	twistStartAngles = None, profileStartAngle = 0, ZrapidHeight = "AUTO_CALCULATE", zDepthOverExtend = .05, debug = False):

	# ERROR CHECKING
	# add code here if desired

	# HOUSEKEEPING
	# figure out everywhere a parameter changes, so we know when to include a new line
	YBreaks = []
	# ADD ENTRIES HERE FOR ADDITIONAL VECTORIZED COMPONENTS
	vectorizedInputs = [twistDiameterVector,twistRateVector]
	for vector in vectorizedInputs:
		for point in vector:
			YBreaks.append(point[1])
	YBreaks.append(length)
	YBreaks = list(set(YBreaks)) # remove duplicates
	YBreaks = [x for x in YBreaks if x <= length] # remove points past the end
	YBreaks.sort()
	print("Unique Y values where parameters get updated: " + str(YBreaks))

	# compute rate of change for diameters, since that is more useful when we are making a Y move of undefined length
	# ADD CODE HERE FOR ADDITIONAL VECTORIZED COMPONENTS, IF THEY ARE NOT RATE SPECIFIED (possibly create a function)
	twistRadiusVector = []
	for entry in twistDiameterVector:
		twistRadiusVector.append([entry[0]/2,entry[1]])
	twistRadiusRateVector = []
	for entryCounter in range(len(twistRadiusVector)):
		if entryCounter == 0:
			twistRadiusRateVector.append([0,twistRadiusVector[0][1]]) # the rate is always zero up until the first point- if the user doesn't want this,
			# then their first point needs to be at y=0
		else:
			# rate of change in Radius is (change in radius) / (change in length) 
			rate = (twistRadiusVector[entryCounter][0] - twistRadiusVector[entryCounter-1][0])/(twistRadiusVector[entryCounter][1] - twistRadiusVector[entryCounter-1][1])
			twistRadiusRateVector.append([rate,twistRadiusVector[entryCounter][1]])
	print("Adjusted Radius vectors, defined by rate of change rather than radius (diameter): " + str(twistRadiusRateVector))

	# compute the spiral start angles (start angles for each face of a profile) and sort them by the desired cut order, and twist start angles
	spiralStartAngles = [x for x in range(0,36000,int(36000.0/numProfileFaces))] # cheating on not being able to use floats here
	spiralStartAngles = [x/100.0 for x in spiralStartAngles]
	spiralStartAngles = [x + profileStartAngle for x in spiralStartAngles]
	adjustedSpiralStartAngles = []
	# NOTE THIS CORRECTION IS ONLY intended for cases where adding the spiral start angle moves us past 360, the expectation is that the spiral start angle
	# is bounded within (-360,360), or else this correction is not perfect. Note that because we interpret this angles differently for > or < 180, they DON't
	# wrap around correctly
	for x in spiralStartAngles:
		if x < 0:
			adjustedSpiralStartAngles.append(x+360)
		elif x >= 360:
			adjustedSpiralStartAngles.append(x-360)
		else:
			adjustedSpiralStartAngles.append(x)
	spiralStartAngles = adjustedSpiralStartAngles

	# these are sorted by default, based on the weird interpretation of angles.
	print("Spiral start angles (sorted by cut order for maximum cut depth efficiency): " + str(spiralStartAngles))
	print("(Note these are kind of weird- all the cuts index from -90 degrees, swing over to +90, then 90.01 with the cutter on the other side, and swing back to -90. This maps to 0-360 for our list of start angles, so 180 is halfway through the rotation and 270 is vertical (0 degree), but with the cutter on the second side. sorry not sorry. This mapping makes them natively happen in the correct order. Good news is, you shouldn't have to mess with these directly.")
	if twistStartAngles == None:
		twistStartAngles = [x for x in range(0,36000,int(36000.0/numTwists))]
	twistStartAngles = [x/100.0 for x in twistStartAngles]

	print("Twist start angles: " + str(twistStartAngles))

	# compute Z rapid plane
	if ZrapidHeight == "AUTO_CALCULATE":
		maxRadius = 0
		for entry in twistRadiusVector:
			maxRadius = max(maxRadius, entry[0])
		# ADD CODE HERE FOR ADDITIONAL VECTORIZED COMPONENTS!!
		ZrapidHeight = maxRadius + profileDiameter
		ZrapidHeight += .15 # some real world clearance, but not too much, we don't want to waste Z travel

	print("Z rapid height set to: " + str(ZrapidHeight))
	print("(This should be slightly more than the radius of your blank)")

	currentA = 0

	# GCODE GENERATION:
	Gcode = ""
	if debug: Gcode += "DEBUG: HEADER: \n"
	Gcode += "G20 \n" # units in inches
	Gcode += "G90 \n" # absolute work coordinates
	Gcode += "G54 \n" # work offset
	Gcode += "G93 \n" # interpret feed rates as a number of minutes rather than a rate
	Gcode += "G40 \n" # cutter comp off, we do that math in the code
	Gcode += "S" + str(spindleSpeed) + "\n"
	Gcode += "M03 \n" # start spindle
	Gcode += "G04 P2000 \n" # dwell 2 seconds to wait for spindle to speed up 
	for finishingPass in range(len(finishingPasses)):
		toolDiameter = toolDiameterUserInput + (finishingPasses[finishingPass]*2)
		if debug: Gcode += "DEBUG: ROUGHING/FINISH PASS #" + str(finishingPass) + "\n"
		for twist in range(numTwists):
			if debug: Gcode += "	DEBUG: TWIST #" + str(twist) + "\n"
			twistStartAngle = twistStartAngles[twist]
			firstCutFront = True # for the aggressive mode
			firstCutBack = True
			for AY_Spiral in range(numProfileFaces):
				if debug: Gcode += "		DEBUG: PROFILE SPIRAL #" + str(AY_Spiral) + "\n"
				spiralStartAngle = spiralStartAngles[AY_Spiral]

				# compute all the adjustment values that occur for this starting A-X pair
				startTwistRate = twistRateVector[0][0]
				XRadiusRatio = -math.cos(math.radians(spiralStartAngle)) # Radius is 0 with the spiral directly up (90 degrees, 270 degrees)
				ZRadiusRatio = abs(math.sin(math.radians(spiralStartAngle)))
				if spiralStartAngle <= 180:
					# MODIFY THIS IF YOU ADD VARIABLE PROFILE DIAMETER
					startMaxZdepth = math.sin(math.radians(spiralStartAngle))*twistRadiusVector[0][0] - .5*profileDiameter*abs(math.cos(math.radians(spiralStartAngle)))-zDepthOverExtend
					startA = twistStartAngle -90 + spiralStartAngle
					XtoolComp = toolDiameter/2 # UPDATE HERE FOR ROUGHING PASS SUPPORT
					XprofileRatio = (math.sin(math.radians(spiralStartAngle-90))+1)/2
					#XprofileRatio = math.sin(math.radians(spiralStartAngle/2.0)) # maybe need a negative here, profile is maximum with the spiral directly up (90 degrees, 270 degrees)
				else: 
					# MODIFY THIS IF YOU ADD VARIABLE PROFILE DIAMETER
					startMaxZdepth = math.sin(math.radians(spiralStartAngle-180))*twistRadiusVector[0][0] - .5*profileDiameter*abs(math.cos(math.radians(spiralStartAngle-180)))-zDepthOverExtend
					startA = twistStartAngle + 90 - (spiralStartAngle-180) 
					XtoolComp = -toolDiameter/2 # UPDATE HERE FOR ROUGHING PASS SUPPORT
					XprofileRatio = -(math.sin(math.radians(spiralStartAngle-270))+1)/2
					#XprofileRatio = -math.sin(math.radians((spiralStartAngle-180)/2.0))
				slideFollowCorrectionRatio = math.sin(math.radians(spiralStartAngle))
				# UPDATE HERE IF PROFILE DIAMETER BECOMES A VECTOR
				XprofileOffset = XprofileRatio*adjustedProfileDiameter(profileDiameter,slidingOrFollowing,startTwistRate,spiralStartAngle)
				startX = XRadiusRatio*twistRadiusVector[0][0] + XprofileOffset + XtoolComp
				
				# debugging
				#print("HELP: AY spiral: " + str(AY_Spiral))
				#print("Xradius ratio: " + str(XRadiusRatio))
				#print("twistRadiusVector[0][0]: " + str(twistRadiusVector[0][0]))
				#print("XprofileRatio: " + str(XprofileRatio))
				#print("adjustedProfileDiameter(): " + str(adjustedProfileDiameter(profileDiameter,slidingOrFollowing,startTwistRate)))
				#print("XtoolComp: " + str(XtoolComp))

				if (firstCutFront == True and spiralStartAngle <=180) or (firstCutBack == True and spiralStartAngle > 180) or agressiveCutting == False: 
					# do depth cuts for this spiral cut
					numDepthCuts = numDepthCutsUserInput
				else:
					numDepthCuts = 1
				if finishingPass > 0 and agressiveCutting == True: # that logic expression was getting painful, just splitting it up a bit
					numDepthCuts = 1

				for zPass in range(numDepthCuts):
					# insert initial Gcode here
					# move to Z plane
					# move to Y0
					# move to AX start
					closestA = int(currentA/360)*360+startA # avoid wasting time doing a rotary move
					if debug: Gcode += "				"
					Gcode += "G00 " + "Z" + str(round4(ZrapidHeight)) + "\n"
					if debug: Gcode += "				"
					Gcode += "G00 " + "X" + str(round4(startX)) + " Y0 " + " A" + str(round4(closestA)) + "\n"
					if debug: Gcode += "			DEBUG: ZPASS #" + str(zPass) + "\n"
					if debug: Gcode += "				"
					deltaZ = ZrapidHeight - (startMaxZdepth + (numDepthCuts-zPass-1)*depthOfCut)
					moveDuration = deltaZ/plungeFeed
					Gcode += "G01 " + "F" + str(round4(1/moveDuration)) + " " + "Z" + str(round4(startMaxZdepth + (numDepthCuts-zPass-1)*depthOfCut)) + "\n"
					currentX = startX
					currentA = closestA
					currentY = 0
					currentZ = startMaxZdepth + (numDepthCuts-zPass-1)*depthOfCut
					currentTwistRate = startTwistRate
					currentRadiusChangeRate = twistRadiusRateVector[0][0]
					currentRadius = twistRadiusVector[0][0]

					for YBreak in YBreaks:
						deltaY = YBreak - currentY
						# UPDATE HERE IF PROFILE DIAMETER BECOMES A VECTOR
						# ALSO NEED TO ADJUST FOR A CHANGING DIAMETER DUE TO FOLLOWING A NEW TWIST RATE!!!
						deltaX = deltaY*currentRadiusChangeRate*XRadiusRatio
						deltaZ = deltaY*currentRadiusChangeRate*(ZRadiusRatio)
						# Need to update twist rate here, not later
						#newXprofileOffset = XprofileRatio*adjustedProfileDiameter(profileDiameter,slidingOrFollowing,currentTwistRate,spiralStartAngle)
						
						# Debugging only
						#Gcode+= ('deltaX: ' + str(deltaX) + ", deltaZ: " + str(deltaZ) + ' currentRadiusChangeRate: ' + 
						#	str(currentRadiusChangeRate) + ' XRadiusRatio: ' + str(XRadiusRatio) + ' \n')
						
						deltaA = 360*deltaY*currentTwistRate

						currentY += deltaY
						currentX += deltaX
						currentA += deltaA
						currentZ += deltaZ
						# GENERATE G CODE HERE, NEED TO ADD FEEDS AND SPEEDS, MODE, ETC.
						if debug: Gcode += "				"
						# currentRadius is not compensated for off-x-center cuts, or for the diameter of the profile, but
						# IS compensated for changes in inner diameter. oh well, it just has to be close
						moveDistance = math.sqrt(deltaY**2+deltaX**2+deltaZ**2+((deltaA/360.0)*3.14*currentRadius*2)**2)
						moveDuration = moveDistance/spiralFeed
						Gcode += "G01 " + "F" + str(round4(1/moveDuration)) + " " + "X" + str(round4(currentX)) + " Y" + str(round4(currentY)) + " Z" + str(round4(currentZ)) + " A" + str(round4(currentA)) + "\n"

						# Update change rates based on vectors
						# Note if we walked off the end of the vector, this *CRUDE* search method will just not update the values
						for entry in twistRadiusRateVector:
							if entry[1] > currentY+.001: # first entry that is greater is assumed to be the one of interest,
								# .001 avoids rounding error. points tighter than .001 will be ignored. My machine can't do it.
								# yours probably can't either. Even though you think it can.
								currentRadiusChangeRate=entry[0]
								break
						for entry in twistRateVector:
							if entry[1] > currentY+.001:
								currentTwistRate = entry[0]
								break
						for entry in twistRadiusVector:
							if entry[1] > currentY+.001:
								currentRadius = entry[0]
								break
				# update first cut conditions so we can skip the z-level on future passes
				if (firstCutFront == True and spiralStartAngle <=180):
					firstCutFront = False
				if (firstCutBack == True and spiralStartAngle > 180):
					firstCutBack = False 

	# cleaning up at the end
	if debug: Gcode += "DEBUG: CLOSING ACTIONS: \n"
	if debug: Gcode += "	"
	Gcode += "G00 " + "Z" + str(round4(ZrapidHeight)) + "\n"
	if debug: Gcode += "	"
	Gcode += "G00 " + "X0 Y0\n" # No A command, since there's no need to unwind

	Gcode += "M05 \n" # stop spindle
	Gcode += "M02 \n" # end command

	print("Gcode:")
	print(Gcode)
	# save to file
	file = open("BarleyTwistGcode.txt", "w")
	file.write(Gcode)
	file.close()
	print("Gcode saved!")

# round a number to the specified number of decimal places, defaults to 4, which is good enough for any router
def round4(input, numDecimalPlaces = 4):
	multiplier = (10**numDecimalPlaces)*1.0 # 1.0 makes sure this is a float
	return (round(input * multiplier))/multiplier

# if in the following mode, adjust the cross section diameter based on where in the profile we're cutting
# and how fast that profile is twisting around the positive
def adjustedProfileDiameter(profileDiameter,slidingOrFollowing,twistRate,spiralStartAngle):
	if slidingOrFollowing == False:
		return profileDiameter
	else:
		# DO SOME MATH HERE
		return profileDiameter

def unitTestBasic():
	toolDiameterUserInput = .25
	depthOfCut = .25
	numDepthCutsUserInput = 1
	agressiveCutting = True
	finishingPasses = [0]
	spiralFeed = 100
	plungeFeed = 100
	spindleSpeed = 25000
	numTwists = 2
	twistDiameterVector = [[2,10]]
	twistRateVector = [[.5,10]]
	length = 10
	numProfileFaces = 4
	profileDiameter = .5
	slidingOrFollowing = True
	twistStartAngles = None
	profileStartAngle = 0
	ZrapidHeight = "AUTO_CALCULATE"
	zDepthOverExtend = .05
	debug = False

	generateBarleyTwistGcode(toolDiameterUserInput = toolDiameterUserInput, depthOfCut = depthOfCut, numDepthCutsUserInput = numDepthCutsUserInput, 
		agressiveCutting = agressiveCutting, finishingPasses = finishingPasses, spiralFeed = spiralFeed, plungeFeed = plungeFeed, 
		spindleSpeed = spindleSpeed, numTwists = numTwists, twistDiameterVector = twistDiameterVector, 
		twistRateVector = twistRateVector, length = length, numProfileFaces = numProfileFaces, profileDiameter = profileDiameter, 
		slidingOrFollowing = slidingOrFollowing, twistStartAngles = twistStartAngles, profileStartAngle = profileStartAngle, 
		ZrapidHeight = ZrapidHeight, zDepthOverExtend = zDepthOverExtend, debug = debug)

def unitTestAdvanced():
	toolDiameterUserInput = 0
	depthOfCut = .25
	numDepthCutsUserInput = 1
	agressiveCutting = True
	finishingPasses = [0]
	spiralFeed = 10
	plungeFeed = 2
	spindleSpeed = 25000
	numTwists = 2
	twistDiameterVector = [[1,5],[2,10]]
	twistRateVector = [[.25,5],[.5,10]]
	length = 10
	numProfileFaces = 8
	profileDiameter = .5
	slidingOrFollowing = True
	twistStartAngles = None
	profileStartAngle = 0
	ZrapidHeight = "AUTO_CALCULATE"
	zDepthOverExtend = .05
	debug = True

	generateBarleyTwistGcode(toolDiameterUserInput = toolDiameterUserInput, depthOfCut = depthOfCut, numDepthCutsUserInput = numDepthCutsUserInput, 
		agressiveCutting = agressiveCutting, finishingPasses = finishingPasses, spiralFeed = spiralFeed, plungeFeed = plungeFeed, 
		spindleSpeed = spindleSpeed, numTwists = numTwists, twistDiameterVector = twistDiameterVector, 
		twistRateVector = twistRateVector, length = length, numProfileFaces = numProfileFaces, profileDiameter = profileDiameter, 
		slidingOrFollowing = slidingOrFollowing, twistStartAngles = twistStartAngles, profileStartAngle = profileStartAngle, 
		ZrapidHeight = ZrapidHeight, zDepthOverExtend = zDepthOverExtend, debug = debug)

if __name__ == '__main__':
	#main()
	#unitTestAdvanced()
	unitTestBasic()