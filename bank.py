import config
import socket
import select
import sys
import pickle
from atm import *
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
    self.PINS = {'alice':'1111','bob':'2222','carol':'3333'}


  #====================================================================
  # TO DO: Modify the following function to handle the console input
  # Every time a user enters a command at the bank terminal, it comes
  # to this function as the variable "inString"
  # The current implementation simply sends this string to the ATM
  # as a demonstration.  You will want to remove this and instead process
  # this string to deposit money, check balance, etc.
  #====================================================================
  def handleLocal(self,inString):
    self.send(inString)
    stringParts = inString.split()

    if stringParts[0].lower() == "deposit":
        self.balances[stringParts[1].lower()] += int(stringParts[2])
        print("$"+str(stringParts[2]) + " added to " + stringParts[1]+"'s account")
        diction = {'operation':'deposit','user':stringParts[1].lower()}
        outObj = json.dumps(diction)


    elif (stringParts[0].lower() == "balance"):
        if (stringParts[1].lower() in self.balances):
            print("$" + str(self.balances[stringParts[1].lower()]) + "\n")
            diction = {'operation':'returnBalance','user':stringParts[1],'balance':self.balances[stringPars[1].lower()}
            outObj = json.dumps(diction)
    else:
        print("Error")
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
    print("\nFrom ATM: ", inObject )
    self.send(inObject)
    print(inObject)
    objects = json.loads(inObject)



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
