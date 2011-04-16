import time,re,socket

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
	self.mainc = self.createClient("egon","egon","egon","egon") #for debugging with d-exec
def handle_data(self,data): #start parsing
	split = data.split(" ")
	if data[:4] == 'PING':
		if self.firstping == 1:
			self.firstping = 0
			endts = time.time()
			self.sendLine("WALLOPS :Synced with network in "+str(float(float(endts)-(float(self.startts))))[:4]+" seconds.")
			#self.mainc = self.createClient("egon","egon","egon","egon") #for debugging with d-exec
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
		if ip == "0":
			ip = ""
		uid = split[9]
		account = split[11]
		if account == "*":
			account = ""
		self.nickstore[nick] = {'uid': uid}
		if "o" in modes: #oper!
			self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': True, 'modes': modes, 'channels': [], 'gecos': gecos, 'ip': ip, 'server': server, 'uid': uid}
		else: #not an oper
			self.uidstore[uid] = {'nick': nick, 'user': user, 'host': host, 'realhost': realhost, 'account': account, 'oper': False, 'modes': modes, 'channels': [], 'gecos': gecos, 'ip': ip, 'server': server, 'uid': uid}
		self.serverstore[server]['users'].append(uid)
		self.getConnect(self.uidstore[uid])
	elif split[1] == "QUIT":
		uid = split[0].strip(":")
		reason = data[data.find(' :')+2:]
		self.getQuit(self.uidstore[uid],reason)
		del self.nickstore[self.uidstore[uid]['nick']]
		self.serverstore[self.uidstore[uid]['server']]['users'].remove(uid)
		del self.uidstore[uid]
	#{1302921049.54} Recv: :05CAAAISU KILL 02KAAABD0 :s4.FOSSnet.info!FOSSnet/staff/bikcmp!jason!bikcmp (<No reason given>)
	elif split[1] == "KILL":
		uid = split[2]
		del self.nickstore[self.uidstore[uid]['nick']]
		self.serverstore[self.uidstore[uid]['server']]['users'].remove(uid)
		del self.uidstore[uid]
	#:02KAAACJL NICK jg :1302376060
	elif split[1] == "NICK":
		uid = split[0].strip(":")
		newnick = split[2]
		oldnick = self.uidstore[uid]['nick']
		del self.nickstore[oldnick]
		self.nickstore[newnick] = {'uid': uid}
		self.uidstore[uid]['nick'] = newnick
	elif split[0] == "SQUIT":
		sid = split[1]
		for uid in self.serverstore[sid]['users']:
			self.log("network","squit: removing client "+uid+" due to "+self.serverstore[sid]['name']+" splitting.")
			self.serverstore[self.uidstore[uid]['server']]['users'].remove(uid)
			del self.uidstore[uid]
		del self.serverstore[sid]
	elif split[1] == "SID": #add uplink to serverstore
	#:42A SID s1.FOSSnet.info 3 11A :Atlanta, Georgia, USA
		#time.sleep(5)
		serverSID = split[4]
		desc = ''.join(str(split[5:]).strip(str(split[5:])[0]))
		servername = split[2]
		self.serverstore[serverSID] = {"name": servername, "SID": serverSID, "desc": desc, "users": []}
	#an ugly hack lies ahead.
	elif split[0] == "PASS": #getting local sid, ugly hack.
			self.uplinkSID = split[4].strip(":")
	elif split[0] == "SERVER":
		self.uplinkservername = split[1]
		self.uplinkserverdesc = ''.join(split[3:]).strip(":")
		self.serverstore[self.uplinkSID] = {"servername": self.uplinkservername, "SID": self.uplinkSID, "serverdesc": self.uplinkserverdesc, "users": []}
	elif split[1] == "ENCAP":
		if split[3] == "SU":
			uid = split[4].replace(":","")
			try:	
				newaccount = split[5].replace(":","")
				self.uidstore[uid]['account'] = newaccount
			except IndexError:
				self.uidstore[uid]['account'] = ""
		#{1302922054.7} Send: :010100001 NOTICE #solus :
	#{1302922063.38} Recv: :10A ENCAP * SU 05CAAAISU :bikcmp
	elif split[1] == "PRIVMSG":
		messagedata = re.search("^:([0-9A-Z]{9}) PRIVMSG ([^ ]*) :(.*)$",data).groups()
		uid = messagedata[0]
		target = split[2]
		message = messagedata[2]
		user = self.uidstore[uid]
		if "#" in target: #channel message
			self.getChannelMessage(user,target,message)
		else: #client sending a message to a pseudoclient
			target = self.uidstore[target]
		self.getPrivmsg(user,target,message)
	elif split[1] == "VERSION" and split[2].replace(":","") == self.mysid:
		uid = split[0].replace(":","")
		self.sendLine(":"+self.mysid+" 351 "+uid+" "+self.getVersion())
	elif split[1] == "WHOIS": #Incoming WHOIS for a pseudo-client.
		cuid = split[0].strip(":")
		uid = split[2]
		self.sendLine(":"+self.mysid+" 311 "+cuid+" "+self.uidstore[uid]['nick']+" "+self.uidstore[uid]['user']+" "+self.uidstore[uid]['host']+" * :"+self.uidstore[uid]['gecos'])
		self.sendLine(":"+self.mysid+" 312 "+cuid+" "+self.uidstore[uid]['nick']+" "+self.servername.replace("(H) ","")+" :"+self.serverdesc)
		self.sendLine(":"+self.mysid+" 313 "+cuid+" "+self.uidstore[uid]['nick']+" :is a Network Service")
		self.sendLine(":"+self.mysid+" 318 "+cuid+" "+self.uidstore[uid]['nick']+" :End of WHOIS")
	elif split[1] == "CHGHOST":
		#:001 CHGHOST 05CAAALTR xyz.
		uid = split[2]
		newhost = split[3]
		self.uidstore[uid]['host'] = newhost
		
#end parsing
#start functions
def add_kline(self,kliner,time,user,host,reason):
	#:uid ENCAP * KLINE 60 user host :reason
	self.sendLine(":"+kliner['uid']+" ENCAP * KLINE "+time+" "+user+" "+host+" :"+reason)
def find_user(self,uid):
	return self.uidstore[uid]
def sendNotice(self,sender,target,data):
	if type(sender) == dict:
		sender = sender['uid']
	if type(target) == dict:
		target = target['uid']
	if "#" in target:
		self.sendLine(":"+sender+" NOTICE "+target+" :"+data)
	else:
		self.sendLine(":"+sender+" NOTICE "+target+" :"+data)
def sendPrivmsg(self,sender,target,data):
	if type(sender) == dict:
		sender = sender['uid']
	if type(target) == dict:
		target = target['uid']
	if "#" in target:
		self.sendLine(":"+sender+" PRIVMSG "+target+" :"+data)
	else:
		self.sendLine(":"+sender+" PRIVMSG "+target+" :"+data)
def createClient(self,cnick,cuser,chost,cgecos):
	myuid = self.baseuid
	if str(self.mysid)+str(myuid) in self.myclients:
		i=0
		while i == 0 and myuid != "99999":
			myuid+=1
			if str(self.mysid)+str(myuid) not in self.myclients:
				cuid = str(self.mysid)+str(myuid)
				self.myclients.append(cuid)
				i=1
	else:
		cuid = str(self.mysid)+str(myuid)
		self.myclients.append(cuid)
	modes = "+ioS"
	self.sendLine(':'+str(self.mysid)+' EUID '+cnick+' 0 '+str(time.time())+' '+modes+' '+cuser+' '+chost+' 0.0.0.0 '+cuid+' 0.0.0.0 0 :'+cgecos)
	self.uidstore[cuid] = {'nick': cnick, 'user': cuser, 'host': chost, 'realhost': chost, 'account': "", 'oper': True, 'modes': modes, 'channels': [], 'gecos': cgecos, 'ip': "", 'server': self.mysid, 'uid': cuid}
	self.nickstore[cnick] = {'uid': cuid}
	self.joinChannel(cuid,self.reportchannel)
	self.sendLine("MODE "+self.reportchannel+" +o "+cuid)
	return self.uidstore[cuid]
def destroyClient(self,cuid,reason):
	if type(cuid) == dict:
		cuid = cuid['uid']
		nick = cuid['nick']
	else:
		nick = self.uidstore[cuid]['nick']
	self.sendLine(":"+cuid+" QUIT :"+reason)
	self.myclients.remove(cuid)
	del self.uidstore[cuid]
	del self.nickstore[cnick]
def joinChannel(self,cuid,channel):
	if channel not in self.uidstore[cuid]['channels']:
		self.sendLine(':'+cuid+' JOIN '+str(time.time())+' '+channel+' +')
		self.uidstore[cuid]['channels'].append(channel)
def partChannel(self,cuid,channel):
	if channel in self.uidstore[cuid]['channels']:
		self.sendLine(':'+cuid+' PART '+channel)
		self.uidstore[cuid]['channels'].remove(channel)
#def getMask(self,client): #should be done in main.py...
#	return :001 CHGHOST 05CAAALTR test.
def kill_user(self,killer,killed,reason):
	if type(killed) == dict:
			killed = killed['uid']
	if type(killer) == dict:
		killer = killer['uid']
	cserver = self.servername
	chost = self.uidstore[killed]['host']
	cuser = self.uidstore[killed]['user']
	cnick = self.uidstore[killed]['nick']
	self.sendLine(":"+killer+" KILL "+killed+" :"+cserver+"!"+chost+"!"+cuser+"!"+cnick+" ("+reason+")")
	del self.nickstore[self.uidstore[killed]['nick']]
	self.serverstore[self.uidstore[killed]['server']]['users'].remove(killed)
	del self.uidstore[killed]
#end functions
