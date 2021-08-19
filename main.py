import discord
import coc
import os
import asyncio
import urllib
from dotenv import load_dotenv
import time
import json

load_dotenv()


def await_internet():
    """
    This function continues to check for internet connection until it is
    available before attempting connection
    :return: once connection has been achieved
    """
    host = "http://www.google.com"
    while True:
        try:
            response = urllib.request.urlopen(host)
            return
        except Exception:
            time.sleep(10)
            pass

# Wait before connecting to accounts for discord/coc


await_internet()

# All variables used for managing clan info
global war
linked_accounts = {}
main_channel = None
clan_tags = ['#28LGRG92U', '#2YQ2RLCC8', '#2L2YVRU8V']
clan_names = ['ToValhalla', 'ValhallaRising', 'Ragnarok']
discord_client = discord.Client()
coc_client = coc.login(
    os.getenv('EMAIL'),
    os.getenv('PASS'),
    key_names="Made with coc.py",
    client=coc.EventsClient)


@discord_client.event
async def on_ready():
    """
    This function announces the bot has logged in, begins
    the background loop to check for sending war info messages,
    it also loads the registry from file if one exists
    :return: None
    """
    print("We have logged in as {0.user}".format(discord_client))
    discord_client.loop.create_task(check_war_time())
    load_registration()


@discord_client.event
async def on_message(message):
    """
    This function handles the commands users enter
    :param message: message object that was sent by user
    :return: None
    """
    if message.author == discord_client.user:
        return
    global war
    # Commands dealing w/ registry
    if message.content.startswith('/unregister'):
        unregister(message.content.split(' ')[1])
    if message.content.startswith('/registry'):
        await send_registry(message)
    if message.content.startswith('/register'):
        register(message.content.split(' ')[1], message.author.id)
    # Commands dealing with ToValhalla
    if message.content.startswith('$currentwar'):
        await update_war_info(0)
        await send_current_war(0, message)
    if message.content.startswith('$timeleft'):
        await update_war_info(0)
        await send_time_remaining(0, message)
    # Commands dealing with ValhallaRising
    if message.content.startswith('!currentwar'):
        await update_war_info(1)
        await send_current_war(1, message)
    if message.content.startswith('!timeleft'):
        await update_war_info(1)
        await send_time_remaining(1, message)
    # Commands dealing with Ragnarok
    if message.content.startswith('@currentwar'):
        await update_war_info(2)
        await send_current_war(2, message)
    if message.content.startswith('@timeleft'):
        await update_war_info(2)
        await send_time_remaining(2, message)


async def check_war_time():
    """
    This function checks every hour if it is time to send the war-info message
    and sends the message if it is
    :return: None
    """
    global main_channel
    await discord_client.wait_until_ready()
    main_channel = discord_client.get_channel(int(os.getenv('CHANNEL')))
    while not discord_client.is_closed():
        if await time_to_send():
            await main_channel.send(embed=get_warning_message())
        await asyncio.sleep(3600)  # Checks every hour (3600sec)


async def time_to_send():
    """
    This function checks the time until the war ends and tells if it is time
    to send the war-info message
    :return: true if betwen 3-4 hours remaining false otherwise
    """
    global war
    await update_war_info(0)
    if war:
        time_remaining = war.end_time.seconds_until / 60
        hours = int(time_remaining / 60)
        if hours == 3:
            return True
    return False


def register(username, user_id):
    """
    This registers an account in the system and backs it up to file
    :param username: username from in game to link
    :param user_id: discord id that is trying to register the username
    :return: None
    """
    linked_accounts[username] = user_id
    backup_registration()


def unregister(username):
    """
    This removes a given username from the registry if one exists and
    backs up the updated registry to file
    :param username: username to be removed from the registry
    :return: None
    """
    try:
        linked_accounts.pop(username)
    except Exception:
        print("Unregister: Invalid key")
    backup_registration()


def backup_registration():
    """
    This function outputs the contents of linked_accounts to a json
    file to allow for multiple sessions
    :return: None
    """
    with open("accounts.json", 'w') as file:
        json.dump(linked_accounts, file)


def load_registration():
    """
    This loads the registration from file on program start
    :return: None
    """
    global linked_accounts
    if os.path.exists('accounts.json'):
        linked_accounts = json.load(open('accounts.json', "r"))


def get_warning_message():
    """
    This builds the warning message of the remaining attacks and war status tagging
    discord accounts of usernames that appear and are registered
    :return: None
    """
    global war
    if war.is_cwl:
        total_attacks = war.team_size
    else:
        total_attacks = war.team_size * 2
    our_attackers = []
    attacks = 0
    for attack in war.attacks:
        if attack.attacker.clan.name == clan_names[0]:
            our_attackers.append(attack.attacker.name)
            attacks += 1
    message = 'Our war with ' + war.opponent.name + ' is ending in less than 4 hours...\nWe are currently ' + war.status + ' and have used (' + str(attacks) + '/' + str(total_attacks) +') attacks, the following player have remaining attacks.\n'
    member_list = []
    for member in war.clan.members:
        member_list.append(member.name)
    for name in member_list:
        attacks_completed = our_attackers.count(name)
        try:
            user_id = '\n<@%s>' % str(linked_accounts[name])
        except Exception:
            user_id = ''
        if war.is_cwl:
            if attacks_completed == 0:
                message += (name + ' - 1 remaining.' + user_id + '\n')
        else:
            if attacks_completed == 0:
                message += (name + ' - 2 remaining.' + user_id + '\n')
            elif attacks_completed == 1:
                message += (name + ' - 1 remaining.' + user_id + '\n')

    embed = discord.Embed(title="The war is ending soon...", description=message, color=0x607d8b)
    embed.set_thumbnail(url='https://cdn.freelogovectors.net/wp-content/uploads/2019/01/clash_of_clans_logo.png')
    return embed


async def update_war_info(tag):
    """
    This changes the war info to a given clans info based on the tag given
    :param tag: 0 = ToValhalla, 1 = ValhallaRising, 2 = Ragnarok
    :return: None
    """
    global war
    try:
        war = await coc_client.get_current_war(clan_tags[tag])
    except coc.PrivateWarLog:
        # CLAN IS NOT IN CWL
        print("Clan was private log")
    if not war:
        war = await coc_client.get_current_war(clan_tags[tag], cwl_round=coc.WarRound.current_preparation)
    if war.league_group and len(war.league_group.rounds) == 7:
        war = await coc_client.get_current_war(clan_tags[tag], cwl_round=coc.WarRound.current_preparation)


async def send_time_remaining(tag, message):
    """
    This sends the time remaining message for a given clan
    :param tag: tag of clan to display war info from
    :param message: message that contains the command given
    :return: None
    """
    global war
    if war:
        time_remaining = war.end_time.seconds_until / 60
        minutes = int(time_remaining % 60)
        hours = int(time_remaining / 60)
        await message.channel.send("{0} has {1} hours and {2} minutes remaining in war against {3}.".format(
            clan_names[tag], hours, minutes, war.opponent.name))
    else:
        await message.channel.send(
            "The war is in a strange CWL state...")


async def send_registry(user_message):
    """
    This sets a message containing the registry to the chat
    :param user_message: message that contains the command given
    :return: None
    """
    message = "Currently {0} accounts have been registered!\n".format(len(linked_accounts))
    for name in linked_accounts:
        message += "{0} - <@{1}>\n".format(name, linked_accounts[name])
    message += "To register your account type /register <Account Name>.\n"
    message += "Note that the name MUST be identical to your in game name.\n"
    await user_message.channel.send(message)


async def send_current_war(tag, message):
    """
    This sends the current war info for a given clan
    :param tag: tag of the clan to display information for
    :param message: message that the command was given in
    :return: None
    """
    global war
    if war:
        name = war.opponent.name
        used = 0
        attacks = ''
        for attack in war.attacks:
            if attack.attacker.clan.name == clan_names[tag]:
                used += 1
            if war.is_cwl:
                attacks = str(used) + '/' + str(war.team_size)
            else:
                attacks = str(used) + '/' + str(war.team_size * 2)
        await message.channel.send(
            '{0}\'s current war is against {1}. We have used {2} attacks and are currently {3}.'.format(clan_names[tag],
                                                                                                        name, attacks,
                                                                                                        war.status))
    else:
        await message.channel.send(
            "The war is in a strange CWL state..."
        )

# This starts the discord client
discord_client.run(os.getenv('TOKEN'))
