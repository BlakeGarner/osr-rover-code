#!/usr/bin/env python
import socket
import os
import time
from bluetooth import *
import xbox
import gamepad


class Connections(object):
	'''
	Sets up all the connections for running the rover, from a bluetooth app, xbox controller, and a unix socket for
	communication to thread running the LED screen

	'''
	def __init__(self):
		super(Connections,self).__init__()
		self.connection_type = None
		self.joy = None
		self.led = 0
		self.unix_sock = None

	def _xBoxConnect(self):
		'''
		Initializes a listener for the Xbox controller
		'''
		self.joy = xbox.Joystick()
		print 'Waiting on Xbox connect'
		while not self.joy.connected():
			time.sleep(1)
		print 'Accepted connection from  Xbox controller', self.joy.connected()

	def _gamepadConnect(self):
		'''
		Initializes a listener for a generic gamepad controller
		'''
		self.joy = gamepad.Gamepad()
		print 'Waiting on Gamepad'
		while not self.joy.connected():
			time.sleep(1)
		print 'Accepted connection from Gamepad', self.joy.connected()

	def _xboxVals(self):
		'''
		Parses values from the Xbox controller. By default the speed is halved, and the "A" button
		is used as a boost button. The D-pad controls the LED screen

		'''

		if self.joy.connected():
			if self.joy.dpadUp():      self.led = 0
			elif self.joy.dpadRight(): self.led = 1
			elif self.joy.dpadDown():  self.led = 2
			elif self.joy.dpadLeft():  self.led = 3
			return

        def getDriveVals(self):
            self._xboxVals()

	def unixSockConnect(self):
		'''
		Connects to a unix socket from the process running the LED screen, which expects
		values of strings [0-3]

		'''
		if os.path.exists('/tmp/screen_socket') :
			client = socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
			client.connect('/tmp/screen_socket')
			self.unix_sock = client
			print "Sucessfully connected to Unix Socket at: ", "/tmp/screen_socket"
		else:
			print "Couldn't connect to Unix Socket at: ", "/tmp/screen_socket"

	def connectController(self):
		'''
		Connects to a controller based on what type it is told from command line arg

		:param str type: The tpye of controller being connected, b (default) for 
							bluetooth app and x for xbox controller 

		'''
		#self._xBoxConnect()
		self._gamepadConnect()

	def sendUnixData(self):
		'''
		Sends the LED screen process commands for the face over unix socket
		'''
		self.unix_sock.send(str(self.led))

	def closeConnections(self):
		'''
		Closes all the connections opened by the Rover
		'''

		if self.connection_type == 'b':
			try:
				self.bt_sock.send('0')
				time.sleep(0.25)
				self.bt_sock.close()
			except:
				pass
		elif self.connection_type == 'x':
			self.joy.close()
		elif self.connection_ype == 'g':
			self.joy.close()

		if self.unix_sock != None:
			self.unix_sock.close()

if __name__ == '__main__':
    connection = Connections()
    connection.connectController()
    connection.unixSockConnect()

    while True:
        try:
            connection.getDriveVals()
            try:
                connection.sendUnixData()
            except Exception as e:
                print e
            time.sleep(0.1)
        except Exception as e:
            connection.closeConnections()
            time.sleep(0.5)
            connection.connectController()


