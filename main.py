import discord
import coc
import os
from keep_alive import keep_alive
import asyncio


global war
main_channel = None
clan_tags = ['#28LGRG92U', '#2YQ2RLCC8']
clan_names = ['ToValhalla', 'ValhallaRising']
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
    


@discord_client.event
async def on_message(message):
  if (message.author == discord_client.user):
      return
  global war
  if message.content.startswith('$currentwar'):
      await updateWarMain()
      if war:
        name = war.opponent.name
        used = 0
        attacks = ''
        for attack in war.attacks:
          if attack.attacker.clan.name == clan_names[0]:
              used += 1
        if war.is_cwl:
          attacks = str(used) + '/' + str(war.team_size)
        else :
          attacks = str(used) +'/' + str(war.team_size * 2)
        await message.channel.send('{0}\'s current war is against {1}. We have used {2} attacks and are currently {3}.'.format(clan_names[0], name, attacks, war.status))
      else :
        await message.channel.send(
        "The war is in a strange CWL state..."
        )
  if message.content.startswith('$timeleft'):
        await updateWarMain()
        if war:
            time_remaining = war.end_time.seconds_until / 60
            minutes = int(time_remaining % 60)
            hours = int(time_remaining / 60)
            await message.channel.send(
                "{0} has {1} hours and {2} minutes remaining in war against {3}.".format(
                    clan_names[0], hours, minutes, war.opponent.name))
        else:
          await message.channel.send(
          "The war is in a strange CWL state..."
          )
  if message.content.startswith('!currentwar'):
    await updateWarMini()
    if war:
      name = war.opponent.name
      used = 0
      attacks = ''
      for attack in war.attacks:
        if attack.attacker.clan.name == clan_names[1]:
          used += 1
        if war.is_cwl:
          attacks = str(used) + '/' + str(war.team_size)
        else :
          attacks = str(used) +'/' + str(war.team_size * 2)
      await message.channel.send('{0}\'s current war is against {1}. We have used {2} attacks and are currently {3}.'.format(clan_names[1], name, attacks, war.status))
    else :
      await message.channel.send(
        "The war is in a strange CWL state..."
        )
  if message.content.startswith('!timeleft'):
      await updateWarMini()
      if war:
          time_remaining = war.end_time.seconds_until / 60
          minutes = int(time_remaining % 60)
          hours = int(time_remaining / 60)
          await message.channel.send(
              "{0} has {1} hours and {2} minutes remaining in war against {3}.".format(
                    clan_names[1], hours, minutes, war.opponent.name))
      else:
        await message.channel.send(
          "The war is in a strange CWL state..."
          )


async def check_war_time():
  await discord_client.wait_until_ready()
  main_channel = discord_client.get_channel(int(os.getenv('CHANNEL')))
  while not discord_client.is_closed():
    if await time_to_send():
      await main_channel.send(embed=get_warning_message())
    await asyncio.sleep(3600) # Checks every hour

async def time_to_send():
  global war
  await updateWarMain()
  if war:
    time_remaining = war.end_time.seconds_until / 60
    hours = int(time_remaining / 60)
    if hours <= 3 and hours > 2:
      return True
    else:
      return False
  else:
    return False

def get_warning_message():
  global war
  total_attacks = 0
  if war.is_cwl:
    total_attacks = war.team_size
  else:
    total_attacks = war.team_size * 2
  our_attackers = []
  for attack in war.attacks:
    if attack.attacker.clan.name == clan_names[0]:
      our_attackers.append(attack.attacker.name)
  message = 'Our war with ' + war.opponent.name + ' is ending in less than 4 hours...\nWe are currently ' + war.status + ' and the following player have remaining attacks.\n'
  member_list = []
  for member in war.clan.members:
    member_list.append(member.name)
  for name in member_list:
    attacks_completed = our_attackers.count(name)
    if war.is_cwl:
      if attacks_completed == 0:
        message += (name + ' - 1 remaining.\n')
    else:
      if attacks_completed == 0:
        message += (name + ' - 2 remaining.\n')
      elif attacks_completed == 1:
        message += (name + ' - 1 remaining.\n')
  embed = discord.Embed(title="The war is ending soon...", description=message, color=0x607d8b)
  embed.set_thumbnail(url='https://cdn.freelogovectors.net/wp-content/uploads/2019/01/clash_of_clans_logo.png')
  return embed

async def updateWarMain():
  global war
  try:
    war = await coc_client.get_current_war(clan_tags[0])
  except coc.PrivateWarLog:
    #CLAN IS NOT IN CWL
    print("Clan was private log")
  if not war:
      war = await coc_client.get_current_war(clan_tags[0], cwl_round=coc.WarRound.current_preparation)
  if war.league_group and len(war.league_group.rounds) == 7:
    war = await coc_client.get_current_war(clan_tags[0], cwl_round=coc.WarRound.current_preparation )

async def updateWarMini():
  global war
  try:
    war = await coc_client.get_current_war(clan_tags[1])
  except coc.PrivateWarLog:
    #CLAN IS NOT IN CWL
    print("Clan was private log")
  if not war:
      war = await coc_client.get_current_war(clan_tags[1], cwl_round=coc.WarRound.current_preparation)
  if war.league_group and len(war.league_group.rounds) == 7:
    war = await coc_client.get_current_war(clan_tags[1], cwl_round=coc.WarRound.current_preparation )
    


    



keep_alive()
discord_client.run(os.getenv('TOKEN'))
