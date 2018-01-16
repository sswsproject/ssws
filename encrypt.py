import aiohttp
import asyncio
import socket,struct,time

from Crypto.Cipher import AES

def myencrypt(btext,key):

    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    secretdata, tag = cipher.encrypt_and_digest(btext)
        
    return secretdata,nonce

def mydecrypt(secrettuple,key):

    secretdata,nonce = secrettuple
    cipher = AES.new(key, AES.MODE_EAX,nonce=nonce)
    btext = cipher.decrypt(secretdata)
    
    return btext
    
