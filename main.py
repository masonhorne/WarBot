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
    host = "http://www.google.com"
    while True:
        try:
            response = urllib.request.urlopen(host)
            return
        except Exception:
            time.sleep(10)
            pass


await_internet()


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
    print("We have logged in as {0.user}".format(discord_client))
    discord_client.loop.create_task(check_war_time())
    load_registration()



@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return
    global war
    if message.content.startswith('/unregister'):
        unregister(message.content.split(' ')[1])
    if message.content.startswith('/registry'):
        await sendRegistry(message)
    if message.content.startswith('/register'):
        register(message.content.split(' ')[1], message.author.id)
    if message.content.startswith('$currentwar'):
        await updateWarInfo(0)
        await sendCurrentWar(0, message)
    if message.content.startswith('$timeleft'):
        await updateWarInfo(0)
        await sendTimeRemaining(0, message)
    if message.content.startswith('!currentwar'):
        await updateWarInfo(1)
        await sendCurrentWar(1, message)
    if message.content.startswith('!timeleft'):
        await updateWarInfo(1)
        await sendTimeRemaining(1, message)
    if message.content.startswith('@currentwar'):
        await updateWarInfo(2)
        await sendCurrentWar(2, message)
    if message.content.startswith('@timeleft'):
        await updateWarInfo(2)
        await sendTimeRemaining(2, message)


async def check_war_time():
    global main_channel
    await discord_client.wait_until_ready()
    main_channel = discord_client.get_channel(int(os.getenv('CHANNEL')))
    while not discord_client.is_closed():
        if await time_to_send():
            await main_channel.send(embed=get_warning_message())
        await asyncio.sleep(3600)  # Checks every hour


async def time_to_send():
    global war
    await updateWarInfo(0)
    if war:
        time_remaining = war.end_time.seconds_until / 60
        hours = int(time_remaining / 60)
        if hours == 3:
            return True
    return False


def register(username, user_id):
    linked_accounts[username] = user_id
    backup_registration()


def unregister(username):
    try:
        linked_accounts.pop(username)
    except Exception:
        print("Unregister: Invalid key")
    backup_registration()

def backup_registration():
    with open("accounts.json", 'w') as file:
        json.dump(linked_accounts, file)


def load_registration():
    global linked_accounts
    if os.path.exists('accounts.json'):
        linked_accounts = json.load(open('accounts.json', "r"))


def get_warning_message():
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
    message = 'Our war with ' + war.opponent.name + ' is ending in less than 4 hours...\nWe are currently ' + war.status + ' and have used (' + attacks + '/' + total_attacks +') attacks, the following player have remaining attacks.\n'
    member_list = []
    for member in war.clan.members:
        member_list.append(member.name)
    for name in member_list:
        attacks_completed = our_attackers.count(name)
        try:
            user_id = '<@%s>' % str(linked_accounts[name])
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


async def updateWarInfo(tag):
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


async def sendTimeRemaining(tag, message):
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


async def sendRegistry(user_message):
    message = "Currently {0} accounts have been registered!\n".format(len(linked_accounts))
    for name in linked_accounts:
        message += "{0} - <@{1}>\n".format(name, linked_accounts[name])
    message += "To register your account type /register <Account Name>.\n"
    message += "Note that the name MUST be identical to your in game name.\n"
    await user_message.channel.send(message)


async def sendCurrentWar(tag, message):
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


discord_client.run(os.getenv('TOKEN'))
