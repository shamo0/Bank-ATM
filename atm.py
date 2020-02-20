import config
import socket
import select
import sys
import json
import pickle
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
    self.loggedIn = False
    self.user = None
    self.users = {'1234': "alice",'4321':"bob",'9999':'carol'}


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
    self.send(inString)

    if inString.split(' ')[0]=="begin-session":
        
        insert = (open("Inserted.card",'rb')).read()

        inputCard = bytes((input("Please enter your PIN: ")),'utf-8')

        if inputCard == insert.strip():
            self.loggedIn = True
            self.user = self.users[insert] 
            self.user = (inString.split(" ")[1]).split(".")[0]
            print("authorized")
        else:
            print("Error")

    elif (inString.split(" "))[0]=="withdraw":
        bank.self.balances[self.user] -= int(inString.split(" ")[1])
        print("$" + str(bank.self.balances[self.user]) + "dispensed")

    elif inString=="balance":
        string = "balance " + str(self.user).lower()
        print(string)
        print(bank.self.handleLocal(string))

    elif inString=="end-session":
        print(self.user+"logged out")
        self.loggedIn = False
        self.user = None

    else:
        return



  #====================================================================
  # TO DO: Modify the following function to handle the bank's messages.
  # Every time a message is received from the bank, it comes to this
  # function as "inObject".  You will want to process this message
  # and potentially allow a user to login, dispense money, etc.
  # Right now it just prints any message sent from the bank to the screen.
  #====================================================================
  def handleRemote(self, inObject):
    print("From Bank: ", inObject)


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
  a = atm()
  a.mainLoop()
