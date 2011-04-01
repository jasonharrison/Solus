import time

def modinit(self):
	self.uidstore = {}
	self.nickstore = {}
	self.serverstore = {}
	self.baseuid = 100000 #start adding numbers onto this uid to generate clients (self.baseuid+=1)
	self.myclients = [] #uids of clients rezzed with createClient()
def moddeinit(self):
	pass
def handle_connect(self,config):
	#introduce server
	self.sendLine("PASS "+str(config.remotepass)+" TS 6 "+str(config.sid))
	self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
	self.sendLine("SERVER "+str(config.servername)+" 1 :"+str(config.serverdesc))
def handle_data(self,data):
	split = data.split(" ")
	if data[:4] == 'PING':
		if self.firstping == 1:
			self.firstping = 0
			endts = time.time()
			self.sendLine("WALLOPS :Synced with network in "+str(float(float(endts)-(float(self.startts))))[:4]+" seconds.")
			x = self.createClient("test","test","unknown","test")
		self.sendLine('PONG %s' % data[5:])
	elif split[1] == "EUID":
		modes = split[5].strip("+").strip("-")
		nick = split[2]
		user = split[6]
		host = split[7]
		server = split[0].strip(":")
		gecos = ' '.join(split[12:]).strip(":")
		if split[10] == "*":
			realhost = split[7]
		else:
			realhost = split[10]
		ip = split[8]
		uid = split[9]
		account = split[11]
		if account == "*":
			account = ""
		self.nickstore[nick] = {'uid': uid}
		if "o" in modes: #oper!
			self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': True, 'modes': modes, 'channels': [], 'gecos': gecos, 'ip': ip, 'server': server}
		else: #not an oper
			self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': False, 'modes': modes, 'channels': [], 'gecos': gecos, 'ip': ip, 'server': server}
		self.serverstore[server]['users'].append(uid)
	elif split[1] == "SID": #add uplink to serverstore
	#:42A SID s1.FOSSnet.info 3 11A :Atlanta, Georgia, USA
		#time.sleep(5)
		serverSID = split[4]
		desc = ' '.join(str(split[5:]).strip(str(split[5:])[0]))
		servername = split[2]
		self.serverstore[serverSID] = {"servername": servername, "SID": serverSID, "desc": desc, "users": []}
	#an ugly hack lies ahead.
	elif split[0] == "PASS": #getting local sid, ugly hack.
			self.uplinkSID = split[4].strip(":")
	elif split[0] == "SERVER":
		self.uplinkservername = split[1]
		self.uplinkserverdesc = ' '.join(split[3:]).strip(":")
		self.serverstore[self.uplinkSID] = {"servername": self.uplinkservername, "SID": self.uplinkSID, "serverdesc": self.uplinkserverdesc, "users": []}
def sendNotice(self,sender,target,data):
	if sender == "server":
		self.sendLine("NOTICE "+target+" :"+data)
	else:
		self.sendLine(":"+sender+" NOTICE "+target+" :"+data)
def sendPrivmsg(self,sender,target,data):
	if sender == "server":
		self.sendLine("NOTICE "+target+" :"+data)
	else:
		self.sendLine(":"+sender+" PRIVMSG "+target+" :"+data)
def createClient(self,cnick,cuser,chost,cgecos):
	self.baseuid+=1
	cuid = str(self.mysid)+str(self.baseuid)
	modes = "+ioS"
	self.sendLine(':'+str(self.mysid)+' EUID '+cnick+' 0 '+str(time.time())+' +'+modes+' '+cuser+' '+chost+' 0.0.0.0 '+cuid+' 0.0.0.0 0 :'+cgecos)
	self.uidstore[cuid] = {'nick': cnick, 'user': cuser, 'host': chost, 'realhost': chost, 'account': "", 'oper': True, 'modes': modes, 'channels': [], 'gecos': cgecos, 'ip': "", 'server': self.mysid}
	self.myclients.append(cuid)
	self.joinChannel(cuid,self.reportchannel)
	self.uidstore[cuid]['channels'].append(self.reportchannel)
	self.sendLine("MODE "+self.reportchannel+" +o "+cuid)
def joinChannel(self,cuid,channel):
	self.sendLine(':'+cuid+' JOIN '+str(time.time())+' '+channel+' +')
	self.uidstore[cuid]['channels'].append(channel)
