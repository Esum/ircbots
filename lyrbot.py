from bot import Bot
import os
import random
import unicodedata


def remove_accents(data):
    return unicodedata.normalize('NFKD', data).encode('ASCII', 'ignore').decode('utf-8').casefold()

def normalize(s):
    return remove_accents(s).replace("-", " ").replace("'", " ").replace("?", "").replace(",", "").replace('.', '').strip()

chansons = {}

def update_songs():
    global chansons
    chanson = {'': [], 'disney': []}
    lines = [""]
    for file in os.listdir("paroles"):
        if not file.endswith(".txt"):
            continue
        with open("paroles/" + file) as file:
            lines.pop()
            lines += file.readlines()
    for i in range(0, len(lines)-1):
        line = lines[i]
        if line.startswith("=="):
            chanteur = line[2:].strip()
        elif line.startswith("="):
            line = [field.strip() for field in line[1:].split('=')]
            if len(line) == 3:
                line.append([])
            else:
                line[3] = [field.strip() for field in line[3].split('|')]
            if len(line) == 4:
                line.append("")
            strophes = []
            j = i+1
            while not lines[j].startswith('='):
                if lines[j] == '\n':
                    strophes.append([])
                else:
                    strophes[-1].append(lines[j].strip())
                j += 1
            chansons[''].append({"title": line[0], "youtube": line[1], "lines": int(line[2]), "remove": line[3], "strophes": strophes, "chanteur": chanteur, "remark": line[4]})
    lines = [""]
    for file in os.listdir("paroles/disney"):
        if not file.endswith(".txt"):
            continue
        with open("paroles/" + file) as file:
            lines.pop()
            lines += file.readlines()
    for i in range(0, len(lines)-1):
        line = lines[i]
        if line.startswith("=="):
            chanteur = line[2:].strip()
        elif line.startswith("="):
            line = [field.strip() for field in line[1:].split('=')]
            if len(line) == 3:
                line.append([])
            else:
                line[3] = [field.strip() for field in line[3].split('|')]
            if len(line) == 4:
                line.append("")
            strophes = []
            j = i+1
            while not lines[j].startswith('='):
                if lines[j] == '\n':
                    strophes.append([])
                else:
                    strophes[-1].append(lines[j].strip())
                j += 1
            chansons['disney'].append({"title": line[0], "youtube": line[1], "lines": int(line[2]), "remove": line[3], "strophes": strophes, "chanteur": chanteur, "remark": line[4]})


class LyrBot(Bot):
    def __init__(self):
        Bot.__init__(self, "lyr")
        self.answer = ""
        self.answers = []
        self.load_scores()

    def do_command_ext(self, conn, command, level, source):
        global chansons
        if command[0].casefold() == "update" and level >= 100:
            if self.started:
                self.command_buffer.append((conn, command, level, source))
                return
            update_songs()
            self.started = False
            self.answers = []
        if command[0].casefold() == "answer" and level >= 100:
            conn.privmsg(source, "Réponse: \"" + self.answer + "\"")
        if command[0].casefold() == "reset" and level >= 100:
            self.started = False
        if command[0].casefold() == "scores":
            scores = [ (self.scores[nick], nick) for nick in self.scores ]
            scores.sort()
            mess = ""
            while scores:
                score, nick = scores.pop()
                mess += ", " + nick + ": " + str(score)
            conn.privmsg(source, mess[2:])
        if command[0].casefold() == "help":
            conn.privmsg(source, "Commandes privées: SCORES (affiche les scores des joueurs), HELP (affiche cette aide), STATS (affiche le nombre chansons et le nom des chanteur·euse·s)")
            conn.privmsg(source, "Commandes: ENCORE (jouer à nouveau), HINT ou INDICE (affiche un indice)")
        if command[0].casefold() == "stats":
            for cat in ['', 'disney']:
                if cat:
                    conn.privmsg(source, "Catégorie: "+cat)
                conn.privmsg(source, "Chansons: " + str(len(chansons[cat])))
                chanteurs = {}
                for chanson in chansons[cat]:
                    chanteur = chanson["chanteur"]
                    if chanteur in chanteurs:
                        chanteurs[chanteur] += 1
                    else:
                        chanteurs[chanteur] = 1
                mess = ""
                first = True
                finished = False
                for chanteur in chanteurs:
                    finished = False
                    mess += ", " + chanteur + " (" + str(chanteurs[chanteur]) + ")"
                    if len(mess) >= 400:
                        if first:
                            conn.privmsg(source, "Chanteur·euse·s: " + mess[2:])
                            first = False
                        else:
                            conn.privmsg(source, mess[2:])
                            finished = True
                        mess = ""
                conn.privmsg(source, mess[2:])

    def on_pubmsg(self, conn, e):
        global chansons
        canal = e.target
        s = e.arguments[0]
        if canal not in self.active:
            return
        if self.started:
            if normalize(self.answer) in normalize(s):
                nick = e.source[:e.source.index('!')]
                if nick in self.scores:
                    self.scores[nick] += 1
                else:
                    self.scores[nick] = 1
                self.save_scores()
                conn.privmsg(canal, "Bravo " + nick + ", la réponse était \"" + self.answer + "\" de " + self.chanteur + ((" " + self.remark) if self.remark else "") + ((" (https://www.youtube.com/watch?v=" + self.youtube + ")" ) if self.youtube else "" ))
                self.started = False
                for command in self.command_buffer:
                    self.do_command(*command)
                self.command_buffer.clear()
                return
        s = [field.strip() for field in s.split(':')]
        if not s[0] == self.nick:
            return
        if len(s) < 2:
            return
        if s[1].casefold() == "help":
            self.do_command(conn, ["help"], 0, e.source.nick)
        if s[1].casefold() == "scores":
            self.do_command(conn, ["scores"], 0, e.source.nick)
        if s[1].casefold() == "stats":
            self.do_command(conn, ["stats"], 0, e.source.nick)
        if s[1].casefold() == "indice" or s[1].casefold() == "hint":
            if self.started:
                conn.privmsg(canal, "Indice: "+self.chanteur)
                return
        if s[1].casefold() == "encore" or s[1].casefold() == "disney":
            cat = s[1].casefold() if s[1].casefold() in chanson else ""
            if self.started:
                conn.privmsg(canal, "Rappel: "+self.mess)
                return
            i = random.randint(0, len(chansons[cat])-1)
            while (cat, i) in self.answers:
                i = random.randint(0, len(chansons[cat])-1)
            if len(self.answers) >= 10:
                del self.answers[0]
            self.answers.append((cat, i))
            chanson = chansons[cat][i]
            self.answer = chanson["title"]
            self.youtube = chanson["youtube"]
            self.chanteur = chanson["chanteur"]
            self.remark = chanson["remark"]
            self.started = True
            while True:
                strophe = random.choice(chanson["strophes"])
                try:
                    vers = random.randint(0, len(strophe) - chanson["lines"])
                    valid = True
                    for word in chanson["remove"]:
                        for v in range(vers, vers + chanson["lines"]):
                            if word in strophe[v]:
                                valid = False
                    if valid:
                        self.mess = ""
                        for v in range(vers, vers + chanson["lines"]):
                            self.mess += " // " + strophe[v]
                        self.mess = self.mess[4:]
                        conn.privmsg(canal, self.mess)
                        return
                except:
                    continue


if __name__ == "__main__":
    update_songs()
    bot = LyrBot()
    bot.start()
