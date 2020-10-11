
# limitations/ usage:
# designed to generate Gcode for creating an open center barley twist on a fourth axis CNC router
# WITHOUT predrilling the hole, WITHOUT a custom barley twist bit, WITH the goal of having the barley
# twist column be symetric all the way around (ie, the backside does not have the concave cut of a center drill).

# terminology: for this project, the A axis spins the part, Z is height up and down, Y is the length of the rotated part,
# and X is side to side (the dimension normally hidden from a rotory part, where you always cut on center)

# there are many tool paths that can achieve a barley twist. This one uses the SIDE of the cutter, offsetting the cutter
# in the X direction, then cutting a spiral (A-Y move). It then repeats this with a new A-X start. The Z values are never 
# critical, since we actually use the side of the cutter- they just need to be deep enough (and get there gradually enough
# for the depth of cut). As such, you can use a round or square cutter. The smaller the cutter, the less lost material (and
# tighter of turns you can generate), but larger diameters will not be possible, since the tool needs to be long enough.

# the script can do any number of starts, but does not check to see if tool will gouge one of the other starts
# while cutting the current one, ie, trying 10 tightly wound starts with a giant cutter will probably not work, but
# this script will not error check.

# Possible things you could want a barley twist to do:
# open center (required for this script)
# n-starts (supported)
# arbitrary barley profile (convex simple shapes supported, circles approximated by many sided shape)
# sliding vs. following profile (sliding supported, following can be approximated with the correctly distorted
	# shape, IF the twist speed is fixed)
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
	# Not unless the inside edge is manually defined.)

# User setup variables:
numTwists = 2
idVector = # inner diameter vector. If not changing twist diameter,
profile = # how to specify??