import config
import socket
import select
import sys
import pickle
from atm import *
import traceback
import os
import json
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_OAEP, AES
from base64 import b64decode, b64encode
from Crypto.Signature import PKCS1_PSS
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import unpad

class bank:
  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((config.local_ip, config.port_bank))
    #====================================================================
    # TO DO: Add any class variables your ATM needs in the __init__
    # function below this.  For example, user balances, PIN numbers
    # etc.
    #====================================================================
    with open('ssBank.bin', 'rb') as ss:
      arr = ss.read().split(b'|')
      self.priv = RSA.importKey(arr[0].rstrip().lstrip())
      self.pub = RSA.importKey(arr[1].rstrip().lstrip())
      self.remotePub = RSA.importKey(arr[2].rstrip().lstrip())
      self.balances = json.loads(arr[3].rstrip().lstrip())
      self.pins = json.loads(arr[4].rstrip().lstrip())
      self.hashes = json.loads(arr[5].rstrip().lstrip())
    self.sigmaker = PKCS1_PSS.new(self.priv)
    self.verifier = PKCS1_PSS.new(self.remotePub)
    self.encryptor = PKCS1_OAEP.new(self.remotePub)
    self.decryptor = PKCS1_OAEP.new(self.priv)
    #self.balances = {"cef1b974fe85a267776b3e22204965d4ecc1025ccf9606e8ba8b2009494441e9":100,"e99bc49bfc1bbf6056f0efcbd3a64c3d67c0008df3b6347ac5eb3cea907803d5":100,"c1ff3c56c4cce611916bab8ce56d469e5b1bd072ebc51d589886925d7f70e7cf":0}
    #self.pins = {'cef1b974fe85a267776b3e22204965d4ecc1025ccf9606e8ba8b2009494441e9':'1111','e99bc49bfc1bbf6056f0efcbd3a64c3d67c0008df3b6347ac5eb3cea907803d5':'2222','c1ff3c56c4cce611916bab8ce56d469e5b1bd072ebc51d589886925d7f70e7cf':'3333'}


  #====================================================================
  # TO DO: Modify the following function to handle the console input
  # Every time a user enters a command at the bank terminal, it comes
  # to this function as the variable "inString"
  # The current implementation simply sends this string to the ATM
  # as a demonstration.  You will want to remove this and instead process
  # this string to deposit money, check balance, etc.
  #====================================================================
  def handleLocal(self,inString):
    stringParts = inString.split()

    if stringParts[0].lower() == "deposit":
      if len(stringParts) != 3:
        print("Invalid command!\n")
        return
      try:
        self.balances[stringParts[1].lower()] += int(stringParts[2])
        print("$"+str(stringParts[2]) + " added to " + stringParts[1]+"'s account\n")
      except KeyError:
        print("Account does not exist\n")


    elif (stringParts[0].lower() == "balance"):
      if len(stringParts) != 2:
        print("Invalid command!\n")
        return
      try:
        if (stringParts[1].lower() in self.balances):
            print("$" + str(self.balances[stringParts[1].lower()]) + "\n")
      except KeyError:
        print("Account does not exist\n")
    else:
        print("Invalid command!\n")
  #====================================================================
  # TO DO: Modify the following function to handle the atm request
  # Every time a message is received from the ATM, it comes to this
  # function as "inObject".  You will want to process this message
  # and potentially allow a user to login, dispense money, etc.
  # You will then have to respond to the ATM by calling the send()
  # function to notify the ATM of any action you approve or disapprove.
  # Right now it just prints any message sent from the ATM to the screen
  # and sends the same message back to the ATM.
  #====================================================================
  def handleRemote(self, inObject):
    print("From ATM: ", inObject) #Debug
    message = dict()
    try:
      if inObject['operation'] == 'begin':
        if self.pins[inObject['user']] == inObject['auth']: # Throws keyerror when user not in dict
          message['operation'] = 'responseStartSession'
          message['user'] = self.hashes[inObject['user']]
          self.send(message)
        else:
          message['operation'] = 'responseError'
          message['msg'] = 'Invalid pin!'
          self.send(message)
      elif inObject['operation'] == 'withdraw':
        #Check auth token
        message['operation'] = 'responseWithdrawal'
        if (int(self.balances[inObject['user']]) >= int(inObject['amount']) and int(inObject['amount']) > 0):
          message['success'] = True
          message['amount'] = inObject['amount']
          self.balances[inObject['user']] -= inObject['amount']
          self.send(message)
        else:
          message['success'] = False
          message['amount'] = str(0) 
          self.send(message) 
      elif inObject['operation'] == 'balance':
        #Check auth
        message['operation'] = 'responseBalance'
        message['amount'] = self.balances[inObject['user']]
        self.send(message)
      else:
        message['operation'] = 'responseError'
        message['msg'] = 'Unhandled command'
        self.send(message)
    except Exception as e:
      text = traceback.format_exc()
      message['operation'] = 'responseError'
      message['msg'] = 'Invalid command'
      self.send(message)
      print("Recv error: " + text)




  #====================================================================
  # DO NOT MODIFY ANYTHING BELOW THIS UNLESS YOU ARE REALLY SURE YOU
  # NEED TO FOR YOUR APPROACH TO WORK. This is all the network IO code
  # that makes it possible for the ATM and bank to communicate.
  #====================================================================
  def prompt(self):
    sys.stdout.write("BANK:")
    sys.stdout.flush()

  def __del__(self):
    self.s.close()

  def send(self, m):
    dump = pickle.dumps(m)
    hash = SHA256.new()
    hash.update(dump)
    sig = self.sigmaker.sign(hash)
    data = [dump, sig]
    stringData = pickle.dumps(data)
    #Here you have a string/bytes representation of the data in pickle format, encrypt and send
    # ctextBytes = self.encryptor.encrypt(stringData)
    # b64forSend = b64encode(ctextBytes)
    # self.s.sendto(b64forSend, (config.local_ip, config.port_router))
    cipher = AES.new(self.symKey, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(stringData)
    json_k = ['nonce','ciphertext','tag']
    json_v = [ b64encode(x).decode('utf-8') for x in [cipher.nonce, ciphertext, tag] ]
    output = pickle.dumps(dict(zip(json_k,json_v)))

    self.s.sendto(output,(config.local_ip, config.port_router))
    # cipher_text=rsa_publickey.encrypt(data,32)[0]
    # m=base64.b64encode(cipher_text)
    # self.s.sendto(json.dumps(m), (config.local_ip, config.port_router))

  def recvBytes(self):
    data, addr = self.s.recvfrom(config.buf_size)
    if addr[0] == config.local_ip and addr[1] == config.port_router:
      # decodedctextBytes= b64decode(data)
      # plaintext = self.decryptor.decrypt(decodedctextBytes)
      # try:
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
    else:
      return False, bytes(0)

  def sendSymKey(self):
    self.symKey = os.urandom(16)
    ctext = self.encryptor.encrypt(self.symKey)
    self.s.sendto(pickle.dumps(ctext), (config.local_ip, config.port_router))


  def mainLoop(self):
    self.sendSymKey()
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
  b = bank()
  b.mainLoop()
