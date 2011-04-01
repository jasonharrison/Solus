import time

def handle_connect(self,config):
	#introduce server
	self.sendLine("PASS "+str(config.remotepass)+" TS 6 "+str(config.sid))
	self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD")
	self.sendLine("SERVER "+str(config.servername)+" 1 :"+str(config.serverdesc))
def handle_data(self,data):
	if data[:4] == 'PING':
		if self.firstping == 1:
			self.firstping = 0
			endts = time.time()
			self.sendLine("WALLOPS :Synced with network in "+str(float(float(endts)-(float(self.startts))))+" seconds.")
		self.sendLine('PONG %s' % data[5:])
