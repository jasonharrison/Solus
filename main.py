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
		self.remotehost = config.remotehost
		self.remoteport = config.remoteport
		self.protocolname = config.protocolname
		self.debugmode = debugmode
		self.startts = time.time()
		self.firstping = 1
		try:
			__import__(config.protocolname)
			self.protocol = sys.modules[config.protocolname]
			print str(self.protocol)
		except ImportError:
			print("Error: protocol \""+config.protocolname+"\" does not exist.")
			exit()
	#small api
	def sendLine(self,data):
		if self.debugmode == 1:
			print("{"+str(time.time())+"} Send: "+data)
		self.push(data+"\r\n")
	#end of api
	def handle_connect(self):
		self.protocol.handle_connect(self,config)
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
