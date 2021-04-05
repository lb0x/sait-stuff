#!/usr/bin/python3
from iota import Iota, Address, TryteString, ProposedTransaction, Tag
from iota.crypto.types import Seed
import json
import socket, sys

#from simplecrypt import decrypt
#from base64 import b64decode
#from getpass import getpass

#Cryptographic seed
##Should be protected and not plain text.
#Generate seed using: cat /dev/urandom |tr -dc A-Z9|head -c${1:-81}
#Fund using (I know it's got an https error, big whoop):
#https://faucet.devnet.iota.org/
#If not working, I can get an address funded from a dev
#Only need to fund this seed and not the others
#### You must generate an address the first time from a seed. #####
#### Uncomment the print statement in genAddress() do grab an address. ####
my_seed = Seed(b'<INSERT YOUR SEED HERE>')

# Sensor_1 info
sensor_1_ip = "google.com"
sensor_1_port = 11111

# Declare an API object
api = Iota(
    adapter='https://nodes.devnet.iota.org:443',
    seed=my_seed,
    testnet=True,
)

#Generate a new address
##Doesn't seem to be creating a new address after address is spent from
##But it shows in the tangle as a new address.
##The seed probably does the work.
def genAddress():
    new_addy = api.get_new_addresses()
    new_addy = new_addy['addresses'][0]
    #print(str(new_addy))
    return new_addy

#Send Transaction Request to Sensor_1 for some data in return.
def sendTransactionRequest():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.connect((sensor_1_ip, sensor_1_port))
    new_addy = genAddress()
    srv.send(str.encode(str(new_addy)))
    resp = srv.recv(1024)
    resp = eval(resp.decode())
    if resp:
        if resp[0] == "Request Accepted":
            print("Preparing to send transaction . . .")
            sensor_1_tangle_address = resp[1]
            sendTransaction(sensor_1_tangle_address, srv)
        else:
            print("Connection Refused.")
    return srv

#Send the Transaction
def sendTransaction(sensor_addy, srv):
    msg = input("Enter Command: ")
    success = False
    print('Constructing transfer of 10i...')

    # Create the transfer object
    tx = ProposedTransaction(
        address=Address(str.encode(sensor_addy)),
        value=10,
        message=TryteString.from_unicode(msg),
    )

    # Prepare the transfer and send it to the network
    response = api.send_transfer(transfers=[tx])
    trans_hash = response['bundle'].hash

    print("Transaction Sent!")
    print('https://utils.iota.org/bundle/%s/devnet' % response['bundle'].hash)
    print('\n')

    srv.send(str.encode(str(trans_hash)))

    return srv

#Main stuffs
srv = sendTransactionRequest()

data_returned = False
while not data_returned:
    print("\nRECV DATA\n---------------")
    sensor_1_return_trans = srv.recv(1024)
    print(sensor_1_return_trans)
    return_msg = api.find_transaction_objects(bundles=[sensor_1_return_trans])

    msg_list = []
    if not return_msg['transactions']:
        print('Couldn\'t find data for the given address.')
    else:
        print('Found:')
    # Iterate over the fetched transaction objects
    for tx in return_msg['transactions']:
    # data is in the signature_message_fragment attribute as trytes, we need
    # to decode it into a unicode string
        data = tx.signature_message_fragment.decode(errors='ignore')
        msg_list.append(data)

    msg = "".join(msg_list)
    type(msg)
    print("\n\n", msg)
    data_returned = True
