#!/usr/bin/env python

#necessary imports.
import socket
import string
import time

from xgoogle.search import GoogleSearch

#User/pass for identifying with nickserv, set to False if not used
USERNAME=False
PASSWORD=False

googling=False
creator="PythonNub"

#these are the connection details, pretty much self-explanitory
HOST="irc.freenode.net"
PORT=6667
NICK="SirChatsALot"
IDENT="Gateway"
REALNAME="Linux4Ever!"

AllowedNicks=["JavaNub", "PythonNub"]
StartChannels=["#python", "#testingclient", "##brainstorm", "#puppylinux-chat"]
channels=[]
HelpMessages=["Hello, I am "+NICK+", a automated bot developed by "+creator+".", "My general commands are (comments start with $, and are not part of the command):", "!google QUERY $ displays the title and url of top 5 google results for QUERY",  "!googledesc QUERY $ same as !google, but it includes the description as well", "!help $ shows this message", "Then, my 'admin' (meaning you must ask "+creator+" for permission to add you to my permission list) commands are:", "!join CHANNEL $ where CHANNEL is a valid channel name, INCLUDING the #'s", "!leave CHANNEL $ pretty much the same as !join, but leaves a channel instead", "!say CHANNEL WORDS $ CHANNEL is optional, if it's not a valid channel or I (the bot) am not logged into the channel, it displays the whole message in the channel (or pm window) you said it in"]

#Buffer to read data from server into
readbuffer=""

#misc stuff to prevent mass spam from Message of the day and connection info
foundResponse=False
motd=False

# Makes the socket to connect with
s=socket.socket( )

#Connects to the irc server
print "Connecting Socket..."
s.connect((HOST, PORT))

#These are login details, won't let you do anything until you send them
s.send("NICK %s\r\n" % NICK)
s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))
if USERNAME != False and PASSWORD != False:
	s.send("PRIVMSG NickServ :identify %s %s\r\n" % (USERNAME, PASSWORD))

#infinite loop to recieve/send data
while 1:
    #Reads about a kb or mb of data (can't remember which)
    readbuffer=readbuffer+s.recv(1024)
    
    #Splits the buffer into a list by the new lines
    temp=string.split(readbuffer, "\n")
    
    #Gets a message out
    readbuffer=temp.pop( )
    
    #loops over each line in the array temp
    for line in temp:
        #Strips leading and trailing whitespace, so there's not a bunch of spaces at the end
        line=string.rstrip(line)
        
        #Splits the line on the space char, makes it easier to process the data recieved
        line=string.split(line)
        
        #Checks to see if we have gotten a response from server yet
        if not foundResponse:
            if line[4]=="Looking" and line[5]=="up":
                print "Connected! "
                print "Discarding /MOTD response"
                foundResponse=True
        
        #Sends a ping back to the server saying we're still here
        if(line[0]=="PING"):
            s.send("PONG %s\r\n" % line[1])
        
        #Checks for the end of the Message of the day (motd) spam. it's annoying in a bot.
        if(len(line) > 2 and line[2]==NICK and line[3]==":End" and line[4]=="of" and line[5]=="/MOTD"):
            print "Done discarding /MOTD response. "
            print "Now joining channels..."
            motd=True #Flag to state motd spam is done, start showing messages
            
            #pause to make sure nickserv registers us before logging into +r channels
            time.sleep(5)
			
            #Joins starting channel, and adds it to logged in channels
            for r in StartChannels:
                s.send("JOIN %s\r\n" % r)
                channels.append(r)
        
        #checks if the annoying motd is over or not, then
        #checks to see if it's a user list response, if it's a user list, we don't bother with it.
        #makes sure it's not  ping request
        if(motd and line[1]!="366" and line[1]!="353" and line[0]!="PING"):
            
            #prints normal message rather than an array, easier to read
			print ' '.join(line)
            
            #prints the array, better for debugging, harder to read
			#print line
            
			#trims the array to our needs, making it easier to use
			sendingUser=line[0][1:string.find(line[0], '!')]
			sendingChannel=line[2]
			messageType=line[1]
			command=""
			args=[]
			if len(line) > 3 and line[3][0:2] == ":!":
				isCommand=True
				command=line[3][2:]
				args=line[4:]
			else:
				isCommand=False
			
			if messageType=="PRIVMSG" and isCommand:
			
				if(command=="say" and sendingUser in AllowedNicks):
					#checks in case first arg to !say is a channel
					if(args[0][0]=="#"):
						if(len(args) > 1):
							if args[0] in channels:
								s.send("PRIVMSG %s :%s\r\n" % (args[0], ' '.join(args[1:])))
							else:
								s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, ' '.join(args[0:])))
						else:
							s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, ' '.join(args[0:])))
					else:
						if(len(args) > 0):
							if sendingChannel in channels:
								s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, ' '.join(args[0:])))
							else:
								s.send("PRIVMSG %s :%s\r\n" % (sendingUser, ' '.join(args[0:])))
						else:
							s.send("PRIVMSG %s :%s\r\n" % (sendingUser, ' '.join(args[0:])))
				
				#Join command.
				#checks if command is !join , then makes sure there's a argument to it, then make sure the sender is a allowed to use it
				elif(command=="join" and len(args) > 0 and sendingUser in AllowedNicks):
					if args[0] in channels: #if argument is in logged in channels list
						f = None
					else: #argument is NOT in list, it's ok to join
						s.send("JOIN %s\r\n" % args[0])
						#adds argument to channels list
						channels.append(args[0])

				#Leave command.
				#checks if command is !leave , then makes sure there's a argument to it, then make sure the sender is a allowed to use it
				elif(command=="leave" and len(args) > 0 and sendingUser in AllowedNicks):
					if args[0] in channels: #if argument is in logged in channels list
						s.send("PART %s\r\n" % args[0])
						#removes argument from channels list
						channels.remove(args[0])

				elif(command=="google" and len(args) > 0 and not googling):
					googling = True
					message = ""
					gs = GoogleSearch((' '.join(args)))
					pmResults = gs.get_results()
					chanResults = pmResults[:2]
					if sendingChannel == NICK:
						for i in pmResults:
							message = "TITLE: "+i.title.encode('UTF-8')+"  URL: "+i.url.encode('UTF-8')+"\r\n"
							s.send("PRIVMSG %s :%s\r\n" % (sendingUser, message))
						s.send("PRIVMSG %s :%s\r\n" % (sendingUser, "If you want more results, try using !google in a private message to me."))
					else:
						for i in chanResults:
							message = "TITLE: "+i.title.encode('UTF-8')+"  URL: "+i.url.encode('UTF-8')+"\r\n"
							s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, message))
						s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, "If you want more results, try using !google in a private message to me."))
					googling = False

				elif(command=="googledesc" and len(args) > 0 and not googling):
					googling = True
					message = ""
					gs = GoogleSearch((' '.join(args)))
					pmResults = gs.get_results()
					chanResults = pmResults[:2]
						#message = "TITLE: "+i.title.encode('UTF-8')+"  DESCRIPTION:"+i.desc.encode('UTF-8')+"  URL: "+i.url.encode('UTF-8')+"\r\n"
					if sendingChannel == NICK:
						for i in pmResults:
							message = "TITLE: "+i.title.encode('UTF-8')+"  DESCRIPTION:"+i.desc.encode('UTF-8')+"  URL: "+i.url.encode('UTF-8')+"\r\n"
							s.send("PRIVMSG %s :%s\r\n" % (sendingUser, message))
						s.send("PRIVMSG %s :%s\r\n" % (sendingUser, "If you want more results, try using !googledesc in a private message to me."))
					else:
						for i in chanResults:
							message = "TITLE: "+i.title.encode('UTF-8')+"  DESCRIPTION:"+i.desc.encode('UTF-8')+"  URL: "+i.url.encode('UTF-8')+"\r\n"
							s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, message))
						s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, "If you want more results, try using !googledesc in a private message to me."))
					googling = False
				
				elif(command=="help"):
					for i in HelpMessages:
						s.send("PRIVMSG %s :%s\r\n" % (sendingUser, i))
					
				else:
					if sendingChannel == NICK:
						s.send("PRIVMSG %s :%s\r\n" % (sendingUser, "Unknown command"))
					else:
						s.send("PRIVMSG %s :%s\r\n" % (sendingChannel, "Unknown command"))
					
