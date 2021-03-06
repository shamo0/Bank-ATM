import config
import socket
import select
import sys
import json
import pickle
import time
import traceback
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_PSS
from Crypto.Cipher import PKCS1_OAEP
from base64 import b64decode, b64encode
from Crypto.PublicKey import RSA
from bank import *


class atm:
  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((config.local_ip, config.port_atm))
    #====================================================================
    # TO DO: Add any class variables your ATM needs in the __init__
    # function below this.  I have started with two variables you might
    # want, the loggedIn flag which indicates if someone is logged in to
    # the ATM or not and the user variable which holds the name of the
    # user currently logged in.
    #====================================================================
    with open('ssATM.bin', 'rb') as ss:
      arr = ss.read().split(b'|')
      self.priv = RSA.importKey(arr[0].rstrip().lstrip())
      self.pub = RSA.importKey(arr[1].rstrip().lstrip())
      self.remotePub = RSA.importKey(arr[2].rstrip().lstrip())
    self.sigmaker = PKCS1_PSS.new(self.priv)
    self.verifier = PKCS1_PSS.new(self.remotePub)
    self.encryptor = PKCS1_OAEP.new(self.remotePub)
    self.decryptor = PKCS1_OAEP.new(self.priv)
    self.loggedIn = False
    self.user = None


  #====================================================================
  # TO DO: Modify the following function to handle the console input
  # Every time a user enters a command at the ATM terminal, it comes
  # to this function as the variable "inString"
  # The current implementation simply sends this string to the bank
  # as a demonstration.  You will want to remove this and instead process
  # this string and determine what, if any, message you want to send to
  # the bank.
  #====================================================================
  def handleLocal(self,inString):
    message = {
      'operation':'',
      'user':'',
      'auth':'',
      'amount': ''
    }

    if inString.split(' ')[0]=="begin-session":
      message['user'] = (open("Inserted.card",'r')).read().rstrip()
      message['auth'] = (input("Please enter your PIN: "))
      message['operation'] = 'begin'
      self.send(message)

    elif (inString.split(" "))[0]=="withdraw":
      if not self.loggedIn: print('Not Logged in!\n'); return
      message['operation'] = 'withdraw'
      message['user'] = self.user
      try:
        message['amount'] = int(inString.split(" ")[1])
      except ValueError:
        print("Could not convert to int\n")
        return
      self.send(message)
      

    elif inString=="balance":
      if not self.loggedIn: print('Not Logged in!\n'); return
      message['operation']='balance'
      message['user'] = self.user
      self.send(message)

    elif inString=="end-session":
      if not self.loggedIn: print("Not Logged in!\n"); return
      print(self.user + " logged out\n")
      self.loggedIn = False
      self.user = None

    else:
        print("Invalid Command!\n")



  #====================================================================
  # TO DO: Modify the following function to handle the bank's messages.
  # Every time a message is received from the bank, it comes to this
  # function as "inObject".  You will want to process this message
  # and potentially allow a user to login, dispense money, etc.
  # Right now it just prints any message sent from the bank to the screen.
  #====================================================================
  def handleRemote(self, inObject):
    #print("From Bank: ", inObject)
    try:
      if inObject['operation'] == 'responseStartSession':
        self.loggedIn = True
        self.user = inObject['user']
        print('authorized\n')
      elif inObject['operation'] == 'responseWithdrawal':
        if inObject['success']:
          print("$" + str(inObject['amount']) + " dispensed")
        else:
          print("Invalid amount\n")
      elif inObject['operation'] == 'responseBalance':
        print("balance: $" + str(inObject['amount']))
      elif inObject['operation'] == "responseError":
        print("Bank error: " + str(inObject['msg']))
      else:
        raise Exception(inObject)
    except Exception as e:
      text = traceback.format_exc()
      print("Invalid message received from bank: "+ text+'\n')


  #====================================================================
  # DO NOT MODIFY ANYTHING BELOW THIS UNLESS YOU ARE REALLY SURE YOU
  # NEED TO FOR YOUR APPROACH TO WORK. This is all the network IO code
  # that makes it possible for the ATM and bank to communicate.
  #====================================================================
  def prompt(self):
    print("ATM" + (" (" + self.user + ")" if self.user != None else "") + ":", end="")
    sys.stdout.flush()

  def __del__(self):
    self.s.close()

  def send(self, m):
    try:
      dump = pickle.dumps(m)
      hash = SHA256.new()
      hash.update(dump)
      sig = self.sigmaker.sign(hash)
      data = [dump, sig]
      stringData = pickle.dumps(data)
      #Here you have a string representation of the data in pickle format, encrypt and send
      cipher = AES.new(self.symKey, AES.MODE_GCM)
      ciphertext, tag = cipher.encrypt_and_digest(stringData)
      json_k = ['nonce','ciphertext','tag']
      json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, ciphertext, tag] ]
      output = pickle.dumps(dict(zip(json_k,json_v)))
      self.s.sendto(output,(config.local_ip, config.port_router))
    except:
      print("Error: Could not send from ATM!")

  def recvBytes(self):
    data, addr = self.s.recvfrom(config.buf_size)
    if addr[0] == config.local_ip and addr[1] == config.port_router:
      try:
        b64 = pickle.loads(data)
        json_key =['nonce', 'ciphertext', 'tag' ]
        jv = {k:b64decode(b64[k]) for k in json_key}
        cipher = AES.new(self.symKey, AES.MODE_GCM, nonce=jv['nonce'])
        plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
        #Here I assume a decrypted string of a pickle dump of Array[dump, sig]
        sigArray = pickle.loads(plaintext)
        hash = SHA256.new()
        hash.update(sigArray[0])
        verified = self.verifier.verify(hash, sigArray[1])
        if verified: return True, sigArray[0]
        else: return False, bytes(0)
      except:
         print("Recv error: Error with receiving data from BANK")

    else:
      return False, bytes(0)

  def waitForSymKey(self):
    print('waiting for session key from bank...')
    print('ensure ATM was started first...')
    try:
      ctext = self.s.recv(1024)
      self.symKey = self.decryptor.decrypt(pickle.loads(ctext))
    except:
      print("Error receiving the Key")


  def mainLoop(self):
    self.waitForSymKey()
    self.prompt()

    while True:
      l_socks = [sys.stdin, self.s]

      # Get the list sockets which are readable
      r_socks, w_socks, e_socks = select.select(l_socks, [], [])

      for s in r_socks:
        # Incoming data from the router
        if s == self.s:
          ret, data = self.recvBytes()
          if ret == True:
            self.handleRemote(pickle.loads(data)) # call handleRemote
            self.prompt()


        # User entered a message
        elif s == sys.stdin:
          m = sys.stdin.readline().rstrip("\n")
          if m == "quit":
            return
          self.handleLocal(m) # call handleLocal
          self.prompt()


if __name__ == "__main__":
  a = atm()
  a.mainLoop()
