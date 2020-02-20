import config
import socket
import select
import sys
import pickle
import bank
from atm import *
from bank import *

#====================================================================
# DO NOT MODIFY ANYTHING ANYTHING IN THE ROUTER FILE UNTIL THE
# FINAL PART OF THE PROJECT
#====================================================================

class router: 

  def __init__(self):
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.s.bind((config.local_ip, config.port_router))
    self.log = open("router.log", "w")

  def __del__(self):
    self.s.close()
    self.log.close()

  def sendToBank(self, m):
    self.s.sendto(m, (config.local_ip, config.port_bank))

  def sendToATM(self, m):
    self.s.sendto(m, (config.local_ip, config.port_atm))

  def recvBytes(self):
      data, addr = self.s.recvfrom(config.buf_size)
      return addr[0], addr[1], data

  #===============================================================
  # Handle incoming data
  #===============================================================
  def handleData(self, data, port):
    if port == config.port_atm:
      print("Received from atm:", pickle.loads(data))
      self.sendToBank(data)
      self.log.write("Message from ATM\n")

    else:
      print("Received from bank:", pickle.loads(data))
      self.sendToATM(data)
      self.log.write("Message from BANK\n")
    self.log.write("-----------------------\n")
    self.dumpObject(data)

  def dumpObject(self, data):
    obj = pickle.loads(data)
    self.log.write("Type: " + str(type(obj)) + '\n')
    self.log.write("Raw pickle data: " + str(data) + "\n")
    self.log.write("Contents: ")
    try:
      parts = vars(obj)
    except:
      parts = {}
    if parts == {}:
      self.log.write(str(obj))
    else:
      self.log.write(str(parts))
    self.log.write("\n\n")
    
  def mainLoop(self): 
    while True:
      l_socks = [sys.stdin, self.s]
           
      # Get the list sockets which are readable
      r_socks, w_socks, e_socks = select.select(l_socks, [], [])
           
      for s in r_socks:
        # Incoming data from the router
        if s == self.s:
          ip, port, data = self.recvBytes()
          if ip == config.local_ip:
            self.handleData(data, port) # call handleRequest 
                                 
        # User entered a message
        else:
          m = sys.stdin.readline().rstrip("\n")
          if m == "quit": 
            return
            

if __name__ == "__main__":
  rt = router()
  rt.mainLoop()

