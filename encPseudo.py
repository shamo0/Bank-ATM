#Pseudo code for server/client 

from Crypto import Random 
from Crypto.PublicKey import RSA
import hashlib


#HANDSHAKE STUFF 
    #client
    random_generator = Random.new().read
    key = RSA.generate(1024,random_generator) 
    public = key.publickey().exportKey()
    #hash_objet, hash_digest --> vars
    hash_object = hashlib.sha1(public) 
    hex_digest = hash_object.hexdigest()

    #Send the key as a string

    #Server 
    key = os.urandom(16)
    #encrypt CTR MODE session key
    en = AES.new(key_128,AES.MODE_CTR,counter = lambda:key_128) encrypto = en.encrypt(key_128)
    #hashing sha1
    en_object = hashlib.sha1(encrypto)
    en_digest = en_object.hexdigest()

    #encrypting session key and public key
    E = server_public_key.encrypt(encrypto,16)


    #client (completing the handshake)
    #get the key as a string
    en = eval(msg)
    decrypt = key.decrypt(en)
    # hashing sha1
    en_object = hashlib.sha1(decrypt) en_digest = en_object.hexdigest()

    



