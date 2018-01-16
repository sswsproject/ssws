import os
import aiohttp
import asyncio
import socket,struct,time
import logging

from aiohttp import web
from encrypt import myencrypt,mydecrypt

logger = logging.getLogger(__name__)


async def remotereader(key, reader, ws):

    while True:
        get_text = await reader.read(4096)
        if get_text==b'':
            break
        else:
            encdata = myencrypt(get_text,key)
            await ws.send_bytes(encdata[0] + encdata[1])


async def remotewriter(writer, queue):

    while True:
        get_text = await queue.get()
        if get_text is None:
            # the producer emits None to indicate that it is done
            break
        else:
            writer.write(get_text)


async def handle(request):

    text = "asdf"
    return web.Response(text=text)


async def websocket_handler(request):

    peername = request.transport.get_extra_info('peername')
    if peername is not None:
        host, port = peername
    
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    key = b'1234567890123456'  # DEFAULT PASSWORD, NEVER USE!
    key = os.environ['PASS'].encode()
    
    future1 = None
    future2 = None

    preaddrind = 0
    
    secretdata,nonce=None,None
    gotdata = None
    
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.BINARY:
            secretdata = msg.data[:-16]
            nonce = msg.data[-16:]            
            gotdata = mydecrypt((secretdata,nonce),key)
            secretdata,nonce=None,None
            
            if preaddrind == 0 :
                preaddrind = 1
                
                addrtype = gotdata[0]
                
                if addrtype == 3:
                    addrlen = gotdata[1] 
                
                if addrtype == 1:
                    remotehost = socket.inet_ntoa(gotdata[1:5]) 
                    remoteport = struct.unpack('>H',gotdata[5:7])[0] 
                
                if addrtype == 3:
                    remotehost = gotdata[2:2 + addrlen]
                    remoteport = struct.unpack('>H',gotdata[2 + addrlen:4 + addrlen]) [0]
                    
                    remotehost = remotehost.decode()
                    
                if addrtype == 1 or addrtype == 3:
                    logger.debug('%r Connect to %r at address %r' % (peername, remotehost, remoteport))
                
                    try:
                        reader, writer = await asyncio.open_connection(
                            host = remotehost,
                            port = remoteport
                        )
                        
                        future1 = asyncio.run_coroutine_threadsafe(remotereader(key, reader, ws), loop)
                        future2 = asyncio.run_coroutine_threadsafe(remotewriter(writer, queue), loop)

                    except Exception as e:
                        logger.debug('%r Connect remote %r at address %r' % (peername, remotehost, remoteport))
                        logger.exception('Exception while connecting remote server %r' % e)

                        senddata = b'*** remote unaccess ***'
                        encdata = myencrypt(senddata,key)
                        await ws.send_bytes(encdata[0] + encdata[1])

                        break
                    
                else:
                    break
                        
            else:
                await queue.put(gotdata)
                            
                    
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            await queue.put(None)
            break
            
        elif msg.type == aiohttp.WSMsgType.ERROR:
            await queue.put(None)
            logger.debug('ws connection closed with exception %r' % ws.exception())
            break

    if future1:
        future1.cancel()
        
    if future2:
        future2.cancel()
    
    return ws         


def main():
    logging.basicConfig(level=getattr(logging, 'DEBUG'), format='%(asctime)s - %(levelname)s - pid:%(process)d - %(message)s')
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/ws', websocket_handler)

    web.run_app(app, port = int(os.environ['PORT']))


if __name__ == '__main__':
    main()
