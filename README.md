# ssws

First of all, ssws is a rework of shadowsocks-heroku(https://github.com/mrluanma/shadowsocks-heroku), written in python3 instead of nodejs.

ssws is a lightweight tunnel proxy which can bypass the censorship of internet, from an organization to a whole country.

ssws can be deployed on any platform(Windows/Mac/Linux) which support python3, so does the client. And because ssws is a port of shadowsocks-heroku, so it can be deployed on Heroku too. But you should do so on your own risk. In the 'Prohibited Actions' section of the AUP of Heroku(https://www.heroku.com/policy/aup), the service provider specifically indicate that the user may not 'use the Service to operate an "open proxy" or any other form of Internet proxy service that is capable of forwarding requests to any End User or third party-supplied Internet host'. I strongly suggest you only deploy ssws on Heroku as a personal testing or study, and do not use it as a production.

# Usage

You should have the python 3.6+ installed on the server(of course, out of the firewall/censorship area), and you need install 2 other python libraries - aiohttp, pycrytodome. Copy the 2 python programs(ssws.py and encrypt.py) to a folder. You should set up 2 OS enviroment variables. One is 'PASS' which is String length of 16, like '1234567890123456' (Don't use this!). You will use the same passcode in the client side. The other is 'PORT', you should set it to '80' as it is the default web port for most web servers. If you deployed ssws on Heroku, you can omit the 'PORT' safely.

At the end, use 'python ssws.py' to start the server. When you open the url of your ssws deployed server, you should see a blank web page with 4 letters 'asdf'.

On the client side, also need 2 python programs, one is encrypt.py, same as the server, the other is local.py which can be run as a lightweight socks 5 server. To start it, you should use the some command like following:

python local.py --key 1234567890123456 --port 8080 --url any.valid.domain --proxy http://10.10.10.10:3228

again, you should not use '1234567890123456' as the passcode, you should replace it with your own passcode, same as the one set up on the server enviroment variable. The '--port' part indicate the socks 5 port you will use. The '--url' part is the remote server which deployed ssws, replace the domain name with your own. And the last part '--proxy' is optional, if you work in an enviroment with a HTTP proxy, then you should use this one, and don't omit the 'http://'.

If you have any question, you can contact sswsproject@protonmail.com, but I can not guarantee I can/will fix any of the problems, I am still a beginner. 

That's all. Have a nice try. 
