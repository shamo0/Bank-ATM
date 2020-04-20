# ATM/BANK

### In this project, we designed and implemented a prototype ATM/Bank system. 
* The bank should be set up with three user accounts, for Alice, Bob, and Carol. Alice's and Bob's balance should be initialized to $100, and Carol's balance should be initialized to $0. In addition to the ATM, bank, and router programs, you will specify the files Alice.card, Bob.card, and Carol.card, and PINs defined for these users.

### There are three important functions in bank.py/atm.py.
* sendBytes: When you call this function, passing a bytes object, it will send those bytes to the ATM via the router. On the ATM side, this will prompt the handleLocal function to be called where it will receive the bytes sent by the bank.
* handleLocal: This function handles console inputs. Every time a user enters something on the console this function gets called. Currently, it simply takes the input from the console and send it to the router. Modify this function for your code to work as in the sample execution above.
* handleRemote: This functions handles messages (in bytes) coming from the ATM (via the router). Currently, it simply prints out the incoming message and sends the same message back to the ATM. Modify this function so that the bank can handle the ATM messages correctly.

### Bank commands
*  deposit user amt 
*  balance user

### ATM commands 
* begin-session
* withdraw amt 
* balance
* end-session

## Security
*  We have public/private key pairs stored in the ssATM/ssBank files which are later used for RSA signature when we establish the connection. These signatures provide both integrity and authentiction. The communication between the atm and the bank is also encrypted using AES-GCM mode in order to provide confidentiality.
-------------
Read design.doc for additional information
 
