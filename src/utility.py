import urllib
import datetime
import os

def find(list, fn):
    for el in list:
        if fn(el):
            return el
    return None


def delete(list, fn):
    for el in list:
        if fn(el):
            list.remove(el)
            return el
    return None


def replace(list, fn, val):
    for idx, el in enumerate(list):
        if fn(el):
            list[idx] = val
            return list[idx]
    return None


def await_internet():
    # Ping Google since if it is down WarBot is least of worries
    host = "http://www.google.com"
    # Infinite loop until the request is sent without error
    while True:
        try:
            response = urllib.request.urlopen(host)
            return
        except Exception:
            # Wait 10 seconds before attempting again
            time.sleep(10)
            pass


def log(message, filepath="log.txt"):
    # Gather time and create formatted string from it
    now = datetime.datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    # Open the log file and append the message with timestamp to end
    with open(filepath, 'a+') as f:
        f.write("%s:\t%s\n" % (date_time, message))


def pid():
    return os.getpid()