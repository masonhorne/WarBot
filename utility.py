import urllib
import datetime
import os
import json

# Location to store accounts backup at
ACCOUNTS_LOCATION = 'accounts.json'


def await_internet():
    """
    Awaits internet connection on host device before initializing WarBot
    """
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
    """
    Logs formatted messages to the log file specified for WarBot default if not supplied
    :param message: message to log to file
    :param filepath: file to log message to (WarBot log file by default)
    """
    # Gather time and create formatted string from it
    now = datetime.datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    # Open the log file and append the message with timestamp to end
    with open(filepath, 'a+') as f:
        f.write("%s:\t%s\n" % (date_time, message))


def load_registration():
    """
    Loads registration from accounts.json file and returns the resulting dictionary
    :return: Dictionary containing the accounts that are registered
    """
    # If accounts exist return the registered accounts, otherwise an empty list
    return json.load(open(ACCOUNTS_LOCATION, "r")) if os.path.exists(ACCOUNTS_LOCATION) else {}

def backup_registration(accounts):
    """
    Outputs the contents of the registration list to a json file
    """
    # Open the file and output the account information
    with open(ACCOUNTS_LOCATION, 'w') as file:
        json.dump(accounts, file)

def pid():
    """
    Returns the process ID for current program
    :return: process ID for the currently executing program
    """
    return os.getpid()