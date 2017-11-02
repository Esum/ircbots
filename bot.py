import irc.bot
import config


"""
def upgrade(file):
    try:
        with open(file) as file:
            src = file.readlines()
        for i in range(len(src)):
            line = src[i]
            if line.startswith("## BEGIN on_command"):
                j = i = i + 1
                while not src[j].startswith("## END"):
                    j += 1
                exec(''.join(src[i:j]), globals())
        return do_command_ext, on_pubmsg_ext
    except Exception as e:
        print("Upgrade failed :", e)
        return lambda *args, **kwargs: None, lambda *args, **kwargs: None
"""


class Bot(irc.bot.SingleServerIRCBot):
    
    def __init__(self, nickname, channel="#bot", server="irc.crans.org", port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.nick = nickname
        self.channel = channel
        self.operators = config.operators
        self.started = False
        self.active = []
        self.command_buffer = []
        self.scores = {}
        self.load_scores()
        #self.on_command_ext = lambda *args, **kwargs: None
        #self.on_pubmsg_ext = lambda conn, e: None
        #self.source_file = ""

    def load_scores(self):
        with open("scores_"+self.nick+".txt") as file:
            for line in file.readlines():
                nick, score = line.split(':')
                self.scores[nick] = int(score)

    def save_scores(self):
        with open("scores_"+self.nick+".txt", 'w') as file:
            for nick in self.scores:
                file.write(nick + ":" + str(self.scores[nick]) + "\n")

    def on_nicknameinuse(self, conn, e):
        conn.nick(conn.get_nickname() + "_")
        self.nick += "_"

    def on_welcome(self, conn, e):
        conn.join(self.channel)

    def on_privmsg(self, conn, e):
        if e.source.nick in self.operators:
            return self.do_command(conn, e.arguments[0].split(' '), self.operators[e.source.nick], e.source.nick)
        return self.do_command(conn, e.arguments[0].split(' '), 0, e.source.nick)

    def do_command(self, conn, command, level, source):
        if command[0].casefold() == "op":
            if len(command) == 2:
                dst_level = 100
            else:
                try:
                    dst_level = int(command[2])
                except:
                    dst_level = 0
            if 0 <= dst_level < level:
                self.operators[command[1]] = dst_level
        elif command[0].casefold() == "upgrade" and level >= float("inf"):
            pass
            #if self.source_file:
            #    self.do_command_ext, self.on_pubmsg_ext = updgrade(self.source_file)
        elif command[0].casefold() == "join" and level >= 100:
            for channel in command[1:]:
                conn.join(channel)
        elif command[0].casefold() == "leave" and level >= 100:
            for channel in command[1:]:
                conn.part(channel, "Ce n'est qu'un au revoir")
        elif command[0].casefold() == "on" and level >= 100:
            for channel in command[1:]:
                self.active.append(channel)
        elif command[0].casefold() == "off" and level >= 100:
            for channel in command[1:]:
                if channel in self.active:
                    self.active.remove(channel)
        else:
            self.do_command_ext(conn, command, level, source)
