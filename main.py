import discord
import coc 
import os

discord_client = discord.Client()
coc_client = coc.login(
    os.getenv('EMAIL'),
    os.getenv('PASS'),
    key_names="Made with coc.py",
    client=coc.Client
)
war = coc_client.get_current_war('#2YQ2RLCC8')

@discord_client.event
async def on_ready():
  print("We have logged in as {0.user}".format(discord_client))
  print(war.league_group)
  

@discord_client.event
async def on_message(message):
  if(message.author == discord_client.user):
    return
  if message.content.startswith('$timeleft'):
    war = coc_client.get_current_war('#2YQ2RLCC8')
    end_time = war.end_time
    time_remaining = war.end_time.seconds_until
    time_remaining = time_remaining / 60
    minutes = time_remaining % 60
    hours = time_remaining / 60
    await message.channel.send("{0} hours and {1} minutes remaining in war".format(hours, minutes))

discord_client.run(os.getenv('TOKEN'))
