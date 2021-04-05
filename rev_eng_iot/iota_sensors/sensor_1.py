#!/usr/bin/python3

## The aim of this project was to simulate a machine-to-machine economy using the crypto currency Iota.
## This scipt acts as a first sensor, which relies on another sensor to send all the data requested by the user, or end device
## making the request. 


from iota import Iota, Address, TryteString, ProposedTransaction, Tag
from iota.crypto.types import Seed
import socket, sys
import json

#Cryptographic seed
##Should be protected and not plain text.
my_seed = Seed(b'<INSERT SEED HERE>')

# Subcontractor Sensor_2 info
sensor_2_ip = "127.0.0.1"
sensor_2_port = 22222

# Declare an API object
api = Iota(
    adapter='https://nodes.devnet.iota.org:443',
    seed=my_seed,
    testnet=True,
)

#Create HTTP Server to Tangle Addressess and Transaction IDs (Bundles)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind(('127.0.0.1', 11111))
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

#Send Transaction Request to Subcontractor
def sendTransactionRequest(msg):
    srv1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv1.connect((sensor_2_ip, sensor_2_port))
    new_addy = genAddress()
    srv1.send(str.encode(str(new_addy)))
    resp = srv1.recv(1024)
    resp = eval(resp.decode())
    print(type(resp))
    if resp:
        if resp[0] == "Request Accepted":
            print("Preparing to send transaction . . .")
            sensor_2_tangle_address = resp[1]
            sendTransaction(sensor_2_tangle_address, srv1, msg)
        else:
            print("Connection Refused.")
    return srv1

#Send Transaction to subcontractor
def sendTransaction(sensor_addy, srv1, msg):
    success = False
    print('Constructing transfer of 3i...')

    # Create the transfer object
    tx = ProposedTransaction(
        address=Address(str.encode(sensor_addy)),
        value=3,
        message=TryteString.from_unicode(msg),
    )

    print('Preparing bundle and sending it to the network...')

    # Prepare the transfer and send it to the network
    response = api.send_transfer(transfers=[tx])

    print(response)

    trans_hash = response['bundle'].hash

    print('Transaction Sent!')
    print('https://utils.iota.org/bundle/%s/devnet' % response['bundle'].hash)
    print('\n')

    srv1.send(str.encode(str(trans_hash)))

    return srv1

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
            if x.as_json_compatible()['value'] >= 10:
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
    print(recv_msg)
    return recv_msg

#Do the task
def doWork():
    work = "Sensor 1 Data"
    return work

#Main Loop
while(True):
    new_addy, return_addy, bundle_hash, connection = recvReq()
    is_confirmed = False
    while not is_confirmed:
        if getPaid(new_addy, bundle_hash):
            print("Confirmed: %s" %(bundle_hash))
            is_confirmed = True
        else:
            print("Transaction Not Confirmed")

    if is_confirmed:

        print("\nGETTING MSG FROM TRANS\n---------------")
        recv_msg = getMessage(bundle_hash)

        print("\nSENDING TO SENSOR 2\n---------------")
        srv1 = sendTransactionRequest(recv_msg)


        print("\nRECV FROM SENSOR 2\n----------------")
        sensor_2_return_trans = srv1.recv(1024)
        print(sensor_2_return_trans)
        return_msg = api.find_transaction_objects(bundles=[sensor_2_return_trans])
        msg_list = getMessage(sensor_2_return_trans)


        print("\nDO WORK\n----------------")
        work = doWork()
        print(work)


        print("\nBUNDLE INFO\n----------------")
        msg_list = [work] + [msg_list]
        msg = " ".join(msg_list)

        print("\nSEND DATA BACK TO return_addy\n--------------------")
        return_trans_hash = sendReturnData(return_addy, msg)
        connection.send(str.encode(str(return_trans_hash)))
        connection.close()
        srv1.close()
