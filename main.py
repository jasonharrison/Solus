import asynchat,asyncore,socket,sys,os,time
try:
	import config
except ImportError:
	print("Please edit config.py.dist - rename it to config.py when you're done")
	exit()
class asynchat_bot(asynchat.async_chat):
	def __init__(self, host, port):
		asynchat.async_chat.__init__(self)
		self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
		self.set_terminator('\r\n')
		self.data=''
		self.remote=(host,port)
		self.connect(self.remote)
		#set vars
		self.versionnumber = 0.01
		self.version = "Solus "+str(self.versionnumber)+". (servername) [(protocol)]"
		self.modules = {}
		#stuff to be set on a rehash
		self.remotehost = config.remotehost
		self.remoteport = config.remoteport
		self.protocolname = config.protocolname
		self.loglevel = config.loglevel
		self.reportchannel = config.reportchannel
		#end of stuff to be set on a rehash
		self.servername = config.servername
		self.mysid = config.sid
		self.debugmode = debugmode
		self.firstping = 1
		try:
			__import__("modules.protocol."+config.protocolname)
			self.protocol = sys.modules["modules.protocol."+config.protocolname]
			self.protocol.modinit(self)
		except ImportError:
			print("Error: protocol \""+config.protocolname+"\" does not exist.")
			exit()
	#api
	def sendLine(self,data):
		if self.debugmode == 1:
			print("{"+str(time.time())+"} Send: "+data)
		self.push(data+"\r\n")
	#def load(self,modtoload):
	#	modname = "modules.services."+modtoload
	#	self.m = __import__(modname)
	#	module.modinit(self)
	#	return module
	#altara's load() and unload()
	def modexists(module, modname):
		modparts = modname.split(".")
		modparts.pop(0)
		assert modparts != []
		currentpart = ""
		for modpart in modparts:
			currentpart = currentpart + "." + modpart
			if hasattr(module, currentpart):
				pass
			else:
				return False
		return True
	def load(self,modname):
		module = __import__(modname)
		if "." in modname:
			modparts = modname.split(".")[1:]
			for part in modparts:
				module = getattr(module, part)
		module.modinit(self)
		self.modules[modname] = module
	def unload(self,modname):
		self.modules[modname].moddeinit(self)
		del self.modules[modname]
	def sendNotice(self,sender,target,message):
		if self.myclients == [] or sender == "server":
			self.protocol.sendNotice(self,"server",target,message)
		else:
			self.protocol.sendNotice(self,sender,target,message)
	def sendPrivmsg(self,sender,target,message):
		if self.myclients == [] or sender == "server":
			self.protocol.sendPrivmsg(self,"server",target,message)
		else:
			self.protocol.sendPrivmsg(self,sender,target,message)
	def log(self,level,data):
		if level.lower() in self.loglevel.lower():
			if self.myclients == []:
				self.sendNotice("server",self.reportchannel,data)
			else:
				self.sendNotice(self.myclients[0],self.reportchannel,data)
	def getVersion(self):
		version = self.version.replace("(servername)",self.servername).replace("(protocol)",self.protocolname)
		return version
	def createClient(self,cnick,cuser,chost,cgecos):
		return self.protocol.createClient(self,cnick,cuser,chost,cgecos)
	def destroyClient(self,client,reason):
		self.protocol.destroyClient(self,client,reason)
	def joinChannel(self,client,channel):
		self.protocol.joinChannel(self,client,channel)
	#end of api
	#start hooks
	def getPrivmsg(self,user,target,message):
		parc = message.count(" ")
		parv = message.split(" ")
		#WARNING: d-exec is ONLY FOR DEBUGGING AND CHECKING VARIABLES FOR DEVELOPMENT PURPOSES.  *DO NOT* use this in production.
		if "d-exec" in message:
			#try:
				query = message.split('d-exec ')[1]
				self.log("info",str(eval(query)))
			#except Exception,e:
			#	self.log("info","error: "+str(e))
		for modname,module in self.modules.items():
			if hasattr(module, "onPrivmsg"):
				module.onPrivmsg(self,user,target,parc,parv,message)
	#end hooks
	def handle_connect(self):
		self.protocol.handle_connect(self,config)
		f = open("modules.conf","r")
		for line in f.read().split("\n"):
			if "#" in line or line == "":
				pass
			else:
				self.load(line)
		self.startts = time.time()
	def handle_error(self):
		raise
	def get_data(self):
		r=self.data
		self.data=''
		return r
	def collect_incoming_data(self, data):
		self.data+=data
	def found_terminator(self):
		data=self.get_data()
		if self.debugmode == 1:
			print("{"+str(time.time())+"} Recv: "+data)
		self.protocol.handle_data(self,data)
if __name__ == '__main__':
	debugmode = 0
	for arg in sys.argv[1:]:
		if " " not in arg and "python" not in arg and "main.py" not in arg:
			if arg == "-d":
				debugmode = 1
				print "Starting in debug mode."
			else:
				print "Unknown argument: "+arg+" - ignoring"
	print("Solus started.  PID: "+str(os.getpid()))
	asynchat_bot(config.remotehost,int(config.remoteport))
	asyncore.loop()
