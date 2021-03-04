import pylab as plt
import numpy as np
import keyboard
import time

X = np.linspace(0,2,1000)
Y = X**2 + np.random.random(X.shape)

plt.ion()
graph = plt.plot(X,Y)[0]

while True:
	Y = X**2 + np.random.random(X.shape)
	graph.set_ydata(Y)
	plt.draw()
	plt.pause(.01)

	try:  # use try so that if user pressed other than the given key error will not be shown
		if keyboard.is_pressed('q'):  # if key 'q' is pressed 
			print('Exiting prematurely per user request')
			break  # fq inishing the loop
		else:
			pass
	except:
		break  # if user pressed a key other than the given key the loop will break
