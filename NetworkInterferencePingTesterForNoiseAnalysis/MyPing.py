
from multiping import MultiPing
import time
import keyboard
import numpy as np
import matplotlib.pyplot as plt

address = "192.168.30.1"

def computeY(counter, base, plotX):
	# rebuild the Y plot ***********************************************************************************
	validPlotPoints = counter/base
	pingPointer = 0
	#print("valid plot points:" +str(validPlotPoints))
	if validPlotPoints < len(plotX):
		plotY = [0] * (len(plotX)-validPlotPoints)
	else:
		plotY = []

	if validPlotPoints>len(plotX):
		pingPointer = base*(validPlotPoints-len(plotX))
		validPlotPoints = len(plotX)
		# UPDATE X VALUES!!

	for i in range(0,validPlotPoints):
		temp = sum(pingResults[pingPointer:pingPointer+base])
		#print("next data point: " + str(temp))
		temp = (temp*1.0)/base
		plotY.append(temp)
		pingPointer = pingPointer + base
		#print("Ping Pointer: " + str(pingPointer))
	return plotY
	# ******************************************************************************************************

numTotalTests = 1000000
pingResults = []
pingHubResults = []
base = 10
plotX = np.linspace(0,100,100)
plotY = [0] * 100

#print("Plot X: " +str(plotX))
#print("Plot Y: " +str(plotY))

fig = plt.figure()
plt.ion()
myplot = plt.plot(plotX,plotY)
graph = myplot[0]
plt.ylim((-.05, 1.05))   # set the ylim to bottom, top
plt.xlim(0, 100)
plt.yticks(np.linspace(-.05,1.05,23))
plt.grid(b=True,which='major',axis='y')


plt.xlabel("Time: averaged pings per entry: " + str(base))
plt.ylabel("percentage pings successful (1.0 == perfect)")

for counter in range(0,numTotalTests):
	
	mp = MultiPing([address])
	mp.send()
	responses, no_responses = mp.receive(.02)
	if responses == {}:
		print("Ping " + str(counter) + "/" + str(numTotalTests) + " FAILED")
		pingResults.append(0)
	elif no_responses == []:
		print("Ping " + str(counter) + "/" + str(numTotalTests) + " passed")
		pingResults.append(1)
	else:
		print("ERROR: SYSTEM NEITHER GOT A RESPONSE NOR FAILED TO GET A RESPONSE.")
		print("RESPONSES: " + str(responses))
		print("NO_RESPONSES: " + str(no_responses))

	time.sleep(.02) # prevent us from overloading the cpu with lots of pings

	#print(str(responses) + str(no_responses))

	if counter%100==0:
		plotY = computeY(counter, base, plotX)
		graph.set_ydata(np.asarray(plotY))
		plt.draw()
		plt.pause(.01)

	try:  # use try so that if user pressed other than the given key error will not be shown
		if keyboard.is_pressed('q'):  # if key 'q' is pressed 
			print('Exiting prematurely per user request')
			break  # finishing loop
		elif keyboard.is_pressed('a'):
			print('ADJUSTING GRAPHING PARAMETERS: adjusting timescale to average 10 datapoints')
			base = 10
			plt.xlabel("Time: averaged pings per entry: " + str(base))
		elif keyboard.is_pressed('s'):
			print('ADJUSTING GRAPHING PARAMETERS: adjusting timescale to average 100 datapoints')
			base = 100
			plt.xlabel("Time: averaged pings per entry: " + str(base))
		elif keyboard.is_pressed('d'):
			print('ADJUSTING GRAPHING PARAMETERS: adjusting timescale to average 1,000 datapoints')
			base = 1000
			plt.xlabel("Time: averaged pings per entry: " + str(base))
		elif keyboard.is_pressed('f'):
			print('ADJUSTING GRAPHING PARAMETERS: adjusting timescale to average 10,000 datapoints')
			base = 10000
			plt.xlabel("Time: averaged pings per entry: " + str(base))
		elif keyboard.is_pressed('j'):
			print('ADJUSTING GRAPHING PARAMETERS: plotting 100 points')
			plt.close()
			plotX = np.linspace(0,100,100)
			plotY = computeY(counter, base, plotX)
			plt.ion()
			myplot = plt.plot(plotX,plotY)
			graph = myplot[0]
			plt.ylim((-.05, 1.05))
			plt.xlim(0, 100) 
			plt.yticks(np.linspace(-.05,1.05,23))
			plt.grid(b=True,which='major',axis='y')
		elif keyboard.is_pressed('k'):
			print('ADJUSTING GRAPHING PARAMETERS: plotting 1,000 points')
			plt.close()
			plotX = np.linspace(0,1000,1000)
			plotY = computeY(counter, base, plotX)
			plt.ion()
			myplot = plt.plot(plotX,plotY)
			graph = myplot[0]
			plt.ylim((-.05, 1.05))
			plt.xlim(0, 1000) 
			plt.yticks(np.linspace(-.05,1.05,23))
			plt.grid(b=True,which='major',axis='y')
		elif keyboard.is_pressed('l'):
			print('ADJUSTING GRAPHING PARAMETERS: plotting 10,000 points')
			plt.close()
			plotX = np.linspace(0,10000,10000)
			plotY = computeY(counter, base, plotX)
			plt.ion()
			myplot = plt.plot(plotX,plotY)
			graph = myplot[0]
			plt.ylim((-.05, 1.05))
			plt.xlim(0, 10000) 
			plt.yticks(np.linspace(-.05,1.05,23))
			plt.grid(b=True,which='major',axis='y')
		else:
			pass
	except:
		pass  # if user pressed a key other than the given key the loop will break


# plt.plot(pingResults)
print(pingResults)