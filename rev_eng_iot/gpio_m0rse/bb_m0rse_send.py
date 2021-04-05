#!/usr/bin/python3

# script allows a beagle-bone black to send morse code through a small GPIO device.
# in my case a laser.

import Adafruit_BBIO.GPIO as gpio
from time import sleep

gpio.setup("P8_7", gpio.OUT, gpio.PUD_DOWN)
gpio.output("P8_7", gpio.LOW)

MORSE_CODE_DICT = { 'a':'.-',       'b':'-...',
                      'c':'-.-.',     'd':'-..',      'e':'.',
                      'f':'..-.',     'g':'--.',      'h':'....',
                      'i':'..',       'j':'.---',     'k':'-.-',
                      'l':'.-..',     'm':'--',       'n':'-.',
                      'o':'---',      'p':'.--.',     'q':'--.-',
                      'r':'.-.',      's':'...',      't':'-',
                      'u':'..-',      'v':'...-',     'w':'.--',
                      'x':'-..-',     'y':'-.--',     'z':'--..',
                      '1':'.----',    '2':'..---',    '3':'...--',
                      '4':'....-',    '5':'.....',    '6':'-....',
                      '7':'--...',    '8':'---..',    '9':'----.',
                      '0':'-----',    ', ':'--..--',  '.':'.-.-.-',
                      '?':'..--..',   '/':'-..-.',    '-':'-....-',
                      '(':'-.--.',    ')':'-.--.-',	  ' ':'.......',
                      'end':'...-.-'}

#send function - x is either 1 (.) or 3 (-)
def send(x):
	gpio.output("P8_7", gpio.HIGH)
	sleep(x)
	gpio.output("P8_7", gpio.LOW)

#main send message loop
while True:
	inp = input("Enter a string: ")

	for i in inp:
		morse = MORSE_CODE_DICT[i]
		#do for all but last char
		for x in morse[:-1]:
			if x == ".":
				send(1)
				sleep(1)
			elif x == "-":
				send(3)
				sleep(1)

		#last char
		for x in morse[-1]:
			if x == ".":
				send(1)
			elif x == "-":
				send(3)
		sleep(4)

	#send end of transmission
	#do for all but last char
	for x in MORSE_CODE_DICT["end"][:-1]:
		if x == ".":
			send(1)
			sleep(1)
		elif x == "-":
			send(3)
			sleep(1)
	#last char
	for x in MORSE_CODE_DICT["end"][-1]:
		if x == ".":
			send(1)
		elif x == "-":
			send(3)
	sleep(4)

	#kill last char
	send(.25)
