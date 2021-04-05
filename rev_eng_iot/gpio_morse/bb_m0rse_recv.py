#!/usr/bin/python3

# script allows a beagle-bone black to recieve morse code (or other encodings)
# through a small photo resistor.

import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.PWM as PWM

from time import sleep
from datetime import datetime,time


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
'(':'-.--.',    ')':'-.--.-', 	' ':'.......',
'end':"...-.-"}

# define pins for RGB
red_pin = "P9_16"
green_pin = "P8_19"
blue_pin = "P9_14"

#Trigger ressistence for photoresistor
TRIGGER = 0.01

#setup junk, create empty lists
ADC.setup()
t0 = datetime.now()
morse_list = []
morse_char_list = []
encoded = []
message = []

# function to get dict key from value
def get_key(val):
	for key, value in MORSE_CODE_DICT.items():
		if val == value:
			return key

# checks if 'cmd' is first word in message, then executes from there.
def is_cmd(message):
	print(message)
	cmd = "cmd"
	if cmd == message[0]:
		print("\nCOMMAND DETECTED! RUNNING!")
		#LED COLOR
		if "red" in message:
			PWM.start(red_pin, 100)
			PWM.start(green_pin, 0)
			PWM.start(blue_pin, 0)
		if "blue" in message:
			PWM.start(red_pin, 0)
			PWM.start(green_pin, 0)
			PWM.start(blue_pin, 100)
		if "green" in message:
			PWM.start(red_pin, 0)
			PWM.start(green_pin, 100)
			PWM.start(blue_pin, 0)
		if "purple" in message:
			PWM.start(red_pin, 100)
			PWM.start(green_pin, 0)
			PWM.start(blue_pin, 100)
		if "gold" in message:
			PWM.start(red_pin, 100)
			PWM.start(green_pin, 84)
			PWM.start(blue_pin, 0)
		if "white" in message:
			PWM.start(red_pin, 100)
			PWM.start(green_pin, 100)
			PWM.start(blue_pin, 100)
		if "off" in message:
			PWM.start(red_pin, 0)
			PWM.start(green_pin, 0)
			PWM.start(blue_pin, 0)
	else:
		return

# Main while loop, checks if resistence is below trigger.
# Have to check when laser is on, in order to determain "off" time.
while(True):
	if ADC.read("P9_40") < TRIGGER:
		# get time to check off time
		t1 = datetime.now()
		# start new count for new on time
		t2 = datetime.now()
		elapsed_off = (t1-t0).seconds

		# if elapsed_off is either 3 or 4 due to lag.
		# determain if space between morse chars
		if elapsed_off > 2 and elapsed_off < 5:
			morse_char = "".join(morse_list)
			morse_list = []
			if morse_char is not None:
				print("MORSE CHAR FOUND: %s \t %s" % (morse_char, get_key(morse_char)))
				encoded.append(get_key(morse_char))

			#if end of transmission char.
			if morse_char == "...-.-":
				print("END OF TRANSMISSION FOUND: %s" %(morse_char))
				print("\nDUMPING MORSE: %s" %(" ".join(morse_char_list)))
				print("\nENCODED MESSAGE: %s\n\n\n\n" %("".join(encoded[:-1])))
				message = "".join(encoded[:-1])
				message = message.split()
				is_cmd(message)
				morse_char_list = []
				morse_list = []
				encoded = []
				sleep(5)
				pass
			else:
				morse_char_list.append(morse_char)
		if elapsed_off == 7:
			print("\n\n\n")

		# nested while loop to check for resistence above trigger
		# measures on time, and if char recieved is a . or a -
		while(True):
			if ADC.read("P9_40") > TRIGGER:
				t3 = datetime.now()
				elapsed_on = (t3-t2).seconds
				if elapsed_on == 1:
					print("CHAR FOUND: .")
					char = "."
					morse_list.append(char)
				if elapsed_on > 2 and elapsed_on < 5 :
					print("CHAR FOUND: -")
					char = "-"
					morse_list.append(char)
				# starts new count for next cycle.
				t0 = datetime.now()
				# breaks from nested while loop, and returns to main.
				break
