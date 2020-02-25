import config
import socket
import select
import sys
import pickle
from atm import *
import traceback
import json

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
    self.balances = {"alice":100,"bob":100,"carol":0}
    self.pins = {'alice':'1111','bob':'2222','carol':'3333'}


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
          message['user'] = inObject['user']
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
    self.s.sendto(pickle.dumps(m), (config.local_ip, config.port_router))

  def recvBytes(self):
    data, addr = self.s.recvfrom(config.buf_size)
    if addr[0] == config.local_ip and addr[1] == config.port_router:
      return True, data
    else:
      return False, bytes(0)

  def mainLoop(self):
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
