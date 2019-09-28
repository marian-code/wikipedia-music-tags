import re
import signal
import sys
def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

s = "w\"e\"gwseg   -   1:12"

s = re.sub(r"\"", "", s)
print(s)

s = re.search(r"\d+\:\d+", s).group()
#s.group()

print(s)

a = "\g"
a = re.sub(r"\<|\>|\:|\"|\/|\\|\||\?|\*", "", a)
print(a)

string = "aaaaaaaaaaaaab....."
string = re.sub(r"\.+$", "", string)
print(string)

b = "/wiki/Music_genre"
b = re.match(r"/wiki/(?!Music_genre)", b)
print(b)

r="010. gsdgg"

number = re.search(r"\d+\.", r).group()
print(number)
number = re.sub(r"^0|\.", "", number.strip())
print(number)

r = "Magic Forest -4:40"
r = re.sub(r"\s*–?-?\s*", "", r)
print(r)

daco = "By by st"
daco = re.sub(r"[Bb]y|[St]udio album", "a", daco)
print(daco)

print("###################################x")

t = "gssgsdgd cept gdgfgggg"
t = t.split("except")
print(t)

import unicodedata
def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text)

w = "\"The Book Of Nature\", \"The Last Home\" and Prayer To The Lost by Clémentine Delauney"
if normalize("Clémentine Delauney") in normalize(w): print("ggod")
else: print("not good")

import time

time.sleep(20)
    