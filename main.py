import asynchat, asyncore, socket, sys, os, time

try:
    import config
except ImportError:
    print("Please edit config.py.dist - rename it to config.py when you're done")
    exit()


class asynchat_bot(asynchat.async_chat):
    def __init__(self, host, port):
        asynchat.async_chat.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_terminator('\r\n')
        self.data = ''
        self.remote = (host, port)
        self.connect(self.remote)
        # set vars
        self.versionnumber = 0.01
        self.version = "Solus " + str(self.versionnumber) + ". (servername) [(protocol)]"
        self.modules = {}
        # stuff to be set on a rehash
        self.remotehost = config.remotehost
        self.remoteport = config.remoteport
        self.protocolname = config.protocolname
        self.loglevel = config.loglevel
        self.reportchannel = config.reportchannel
        # end of stuff to be set on a rehash
        self.servername = config.servername
        self.serverdesc = config.serverdesc
        self.mysid = config.sid
        self.debugmode = debugmode
        self.firstping = 1
        self.ignored = []
        self.myclients = []
        try:
            __import__("modules.protocol." + config.protocolname)
            self.protocol = sys.modules["modules.protocol." + config.protocolname]
            self.protocol.modinit(self)
        except ImportError:
            print("Error: protocol \"" + config.protocolname + "\" does not exist.")
            exit()

    # api
    def sendLine(self, data):
        if self.debugmode == 1:
            print("{" + str(time.time()) + "} Send: " + data)
        self.push(data + "\r\n")

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

    def load(self, modname):
        module = __import__(modname)
        if "." in modname:
            modparts = modname.split(".")[1:]
            for part in modparts:
                module = getattr(module, part)
        module.modinit(self)
        self.modules[modname] = module

    def unload(self, modname):
        self.modules[modname].moddeinit(self)
        del self.modules[modname]

    def modreload(self, modname):
        reload(self.modules[modname])

    def modfullreload(self, modname):
        self.modules[modname].moddeinit(self)
        reload(self.modules[modname])
        self.modules[modname].modinit(self)

    def rehash(self):
        try:
            reload(config)
            self.remotehost = config.remotehost
            self.remoteport = config.remoteport
            self.protocolname = config.protocolname
            self.loglevel = config.loglevel
            self.reportchannel = config.reportchannel
        except Exception, e:
            print
            "Error: " + str(e)

    def sendNotice(self, sender, target, message):
        self.protocol.sendNotice(self, sender, target, message)

    def sendPrivmsg(self, sender, target, message):
        self.protocol.sendPrivmsg(self, sender, target, message)

    def log(self, level, data):
        if level.lower() in self.loglevel.lower():
            if self.myclients == []:
                self.sendNotice("server", self.reportchannel, data)
            else:
                self.sendNotice(self.myclients[0], self.reportchannel, data)

    def add_kline(self, kliner, time, user, host, reason):
        self.protocol.add_kline(kliner, time, user, host, reason)

    def getVersion(self):
        version = self.version.replace("(servername)", self.servername).replace("(protocol)", self.protocolname)
        return version

    def createClient(self, cnick, cuser, chost, cgecos):
        c = self.protocol.createClient(self, cnick, cuser, chost, cgecos)
        self.myclients.append(c)
        return c

    def destroyClient(self, client, reason):
        self.protocol.destroyClient(self, client, reason)

    def joinChannel(self, client, channel):
        self.protocol.joinChannel(self, client, channel)

    def partChannel(self, client, channel):
        self.protocol.partChannel(self, client, channel)

    def kill(self, client, killee, reason):
        self.protocol.kill(client, killee, reason)

    def getUserList(self):
        if self.protocolname == "TS6":
            return self.uidstore.items()

    def find_user(self, client):
        if type(client) == str:
            return self.protocol.find_user(self, client)
        elif type(client) == dict:
            return client

    def kill_user(self, killer, killed, reason):
        self.protocol.kill_user(self, killer, killed, reason)

    def getMask(self, client):
        if type(client) == str:
            client = self.find_user(client)
        hostmask = client['nick'] + "!" + client['user'] + "@" + client['host']
        return hostmask

    # end of api
    # begin hooks
    def getConnect(self, user):
        for modname, module in self.modules.items():
            if hasattr(module, "onConnect"):
                module.onConnect(self, user)

    def getQuit(self, user, reason):
        for modname, module in self.modules.items():
            if hasattr(module, "onQuit"):
                module.onQuit(self, user, reason)

    def getPrivmsg(self, user, target, message):
        for modname, module in self.modules.items():
            if hasattr(module, "onPrivmsg"):
                module.onPrivmsg(self, user, target, message)

    def getChannelMessage(self, user, channel, message):
        for modname, module in self.modules.items():
            if hasattr(module, "onChannelPrivmsg"):
                module.onChannelPrivmsg(self, user, channel, message)

    # end hooks
    def handle_connect(self):
        self.protocol.handle_connect(self, config)
        f = open("modules.conf", "r")
        for line in f.read().split("\n"):
            if "#" in line or line == "":
                pass
            else:
                self.load(line)
        self.startts = time.time()

    def handle_error(self):
        raise

    def get_data(self):
        r = self.data
        self.data = ''
        return r

    def collect_incoming_data(self, data):
        self.data += data

    def found_terminator(self):
        data = self.get_data()
        if self.debugmode == 1:
            print("{" + str(time.time()) + "} Recv: " + data)
        self.protocol.handle_data(self, data)


if __name__ == '__main__':
    debugmode = 0
    for arg in sys.argv[1:]:
        if " " not in arg and "python" not in arg and "main.py" not in arg:
            if arg == "-d":
                debugmode = 1
                print
                "Starting in debug mode."
            else:
                print
                "Unknown argument: " + arg + " - ignoring"
    print("Solus started.  PID: " + str(os.getpid()))
    asynchat_bot(config.remotehost, int(config.remoteport))
    asyncore.loop()
