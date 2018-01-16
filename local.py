import aiohttp
import asyncio
import socket,struct,time
import argparse
import logging
import gc

from encrypt import myencrypt,mydecrypt

VERSION = (0, 1)
__version__ = '.'.join(map(str, VERSION[0:2]))
__homepage__ = 'https://github.com/bigbagboom/ssws'

config = { 'key' : '', 
           'concurrent' : 0,
           'proxy' : None,
           'url': '' } 

logger = logging.getLogger(__name__)

    
async def localreader(client_address,key, reader, ws):

    while True:
        get_text = await reader.read(4096)
        if get_text==b'':
            break
        else:
            encdata = myencrypt(get_text,key)
            await ws.send_bytes(encdata[0] + encdata[1])


async def localwriter(client_address, writer, queue):

    while True:
        get_text = await queue.get()
        if get_text is None:
            # the producer emits None to indicate that it is done
            break
        else:
            writer.write(get_text)


async def localproxy(reader, writer):

    addrToSend = ""
    
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)

    key = config['key'].encode()
    url = config['url']
    proxy = config['proxy']
    connectstr = ''

    client_address = writer.get_extra_info('peername')
    logger.info('client connected: %r %r' % client_address)

    get_text = await reader.read(262)

    writer.write(b'\x05\x00')
    await writer.drain()

    data = await reader.read(4)
    if len(data) == 4 and url != '':
        fullurl = 'https://' + url + '/ws'
        mode = data[1]
        addrtype = data[3]
        
        addrToSend = data[3:4]

        if addrtype == 1:
            ip_bytes = await reader.read(4)
            addr = socket.inet_ntoa(ip_bytes)
            addrToSend = addrToSend + ip_bytes

        elif addrtype == 3:
        
            addrlen_byte = await reader.read(1)
            addrlen = ord(addrlen_byte)
            addr = await reader.read(addrlen)
            addrToSend = addrToSend + addrlen_byte + addr
            
            addr = addr.decode()
            
        port = await reader.read(2)
        
        addrToSend = addrToSend + port

        reply = b"\x05\x00\x00\x01\x00\x00\x00\x00" 

        logger.info('%r connect remote :%r %r' % (client_address, addr, struct.unpack('>H',port)[0]))
        
        if mode != 1:
            logger.info('unsupported mode: %r' % mode)
            reply = b"\x05\x07\x00\x01" 
            writer.write(reply)
            await writer.drain()
            writer.close()

        if mode ==1 :

            writer.write(reply + port)
            await writer.drain()
            
            config['concurrent'] = config['concurrent'] + 1
            logger.info('Concurrent connetion %d' % config['concurrent'])
            
            async with aiohttp.ClientSession() as session:
                try:

                    wsconnectargs = {}
                    if proxy:
                        wsconnectargs['proxy'] = proxy 

                    async with session.ws_connect(fullurl, **wsconnectargs) as ws:  
                    
                        senddata = addrToSend
                        encdata = myencrypt(senddata,key)
                        ws.send_bytes(encdata[0] + encdata[1])
                        
                        future1 = asyncio.run_coroutine_threadsafe(localreader(client_address, key, reader, ws), loop)
                        future2 = asyncio.run_coroutine_threadsafe(localwriter(client_address, writer, queue), loop)

                        secretdata,nonce=None,None
                        decMsg = None

                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.BINARY:
                                secretdata = msg.data[:-16]
                                nonce = msg.data[-16:]
                                
                                decMsg = mydecrypt((secretdata,nonce),key)
                                secretdata,nonce=None,None
                                    
                                if decMsg!=b'*** remote unaccess ***':
                                    await queue.put(decMsg)
                                else:
                                    await queue.put(None)
                                    break

                                decMsg = None

                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                break
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.info('%r ws connection closed with exception %s' % (client_address, ws.exception()))
                                break
                    
                    future1.cancel()
                    future2.cancel()

                except aiohttp.client_exceptions.ClientConnectorError: 
                    logger.info('%r ws connection time out!',client_address)        #aiohttp.client_exceptions.ClientConnectorError
                
                config['concurrent'] = config['concurrent'] - 1
                logger.info('Concurrent connetion %d' % config['concurrent'])

    writer.close()
    gc.collect()
    

def main():
    parser = argparse.ArgumentParser(
        description='local.py v%s' % __version__,
        epilog='Having difficulty using local.py? Report at: %s/issues/new' % __homepage__
    )
    
    parser.add_argument('--hostname', default='127.0.0.1', help='Default: 127.0.0.1')
    parser.add_argument('--port', default='7071', help='Default: 7071')
    parser.add_argument('--key', default='1234567890123456', help='Default: Never Use the default key!!!')
    parser.add_argument('--url')
    parser.add_argument('--proxy')
    parser.add_argument('--log-level', default='INFO', help='DEBUG, INFO, WARNING, ERROR, CRITICAL')
    args = parser.parse_args()
    
    logging.basicConfig(level=getattr(logging, args.log_level), format='%(asctime)s - %(levelname)s - pid:%(process)d - %(message)s')
    
    hostname = args.hostname
    port = int(args.port)
    config['key'] = args.key
    config['proxy'] = args.proxy
    config['url'] = args.url
    
    logger.info('url %r' % args.url)
    logger.info('proxy %r' % args.proxy)

    loop = asyncio.get_event_loop()
    server=asyncio.start_server(
        localproxy,
        host = hostname,
        port = port
    )

    running_server = loop.run_until_complete(server)
    loop.run_forever()


if __name__ == '__main__':
    main()

