import os
import coc
import discord
import asyncio
import shlex
from src import database, utility


class WarBot(discord.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, intents=self._get_intent())
        # Await internet connection on host device
        utility.await_internet()
        # Log start message and initialize clients
        utility.log("Starting Warbot with PID: %d" % utility.pid())
        # Log into the coc client
        self.coc_client = coc.Client()
        self.coc_client.loop = self.loop
        # Initialize the database connection
        self.database = database.Database(os.getenv('ATLAS_URI'), os.getenv('DB_NAME'), os.getenv('COLLECTION_NAME'))

    def _get_intent(self):
        intent = discord.Intents.default()
        intent.message_content = True
        return intent

    async def send_embed(self, message, title, content):
        # Create the embed with the provided content
        embed = discord.Embed(title=title, description=content, color=0x607d8b)
        # Set the thumbnail for the embed
        file = discord.File('WarBotLogo.png', filename='WarBotLogo.png')
        embed.set_thumbnail(url='attachment://WarBotLogo.png')
        # Send the message to the requested channel
        await message.channel.send(embed=embed, file=file)

    async def register_clan(self, message):
        # Handle invalid use cases
        if len(message.content.split(' ')) != 3:
            await self.send_embed(message, "WarBot Clan Registration", "Incorrect Usage: /register <clan tag> <command symbol>")
            return
        server_id = message.guild.id
        _, clan_tag, clan_symbol = message.content.split(' ')
        # Handle invalid input values
        if len(clan_symbol) != 1 or clan_tag[0] != '#':
            await self.send_embed(message, "WarBot Clan Registration", "A clan tag must start with # and command symbol must be a single character.")
            return
        # Verify that the clan exists in clash of clans
        try:
            await asyncio.wait_for(self.coc_client.get_clan(clan_tag), timeout=3)
        except (coc.errors.NotFound, TimeoutError):
            await self.send_embed(message, "WarBot Clan Registration", "A clan wasn't found with this clan tag.")
            return
        # Handle if no data exists for this server
        server = self.database.read_server(server_id)
        if server is None:
            server = database.Server(server_id)
        if utility.find(server.clans, lambda x: x.clan_symbol == clan_symbol):
            await self.send_embed(message, "WarBot Clan Registration", "A clan is already registered with this command symbol.")
            return
        # Update server and store clan
        clan = database.Clan(clan_tag, clan_symbol)
        server.add_clan(clan)
        self.database.write_server(server)
        clan_data = await self.coc_client.get_clan(clan.clan_tag)
        await self.send_embed(message, "WarBot Clan Registration", "Successfully registered %s with command symbol %s" % (clan_data.name, clan.clan_symbol))

    async def send_server_info(self, message):
        # Handle if the server hasn't been registered
        server_id = message.guild.id
        server = self.database.read_server(server_id)
        if server is None:
            await self.send_embed(message, "WarBot Server Info", "This discord server has not been registered with WarBot.\nRegister a clan first with /register <clan tag> <command symbol>.")
            return
        # Build message content for server info and send to channel
        content = 'The following clans are registered with their respective command symbols.\n\n'
        for clan in server.clans:
            clan_data = await self.coc_client.get_clan(clan.clan_tag)
            content += "%s - %s" % (clan_data.name, clan.clan_symbol)
        await self.send_embed(message, "WarBot Server Info", content)

    
    async def send_registry(self, message, server):
        # If no registered users nothing to send
        if len(server.users) <= 0:
            utility.log("Send registry invalid server (%s)" % server.server_id)
            await self.send_embed(message, "WarBot Linked Accounts", "No users have linked accounts on this server!")
            return
        # Initialize message with size of registry
        response = "Currently %d accounts have been registered!\n\n" % len(server.users)
        # Add all registered accounts to message
        for user in server.users:
            response += "%s - <@%s>\n" % (user.account_name, user.user_id)
        # Add how to add other accounts to bottom of registry message
        response += "\nTo link your account type /link <Account Name>.\n"
        response += "Note that the name MUST be identical to your in game name.\n"
        # Send the registry message to the channel
        await self.send_embed(message, "WarBot Linked Accounts", response)

    async def link(self, message, server):
        # Handle invalid uses
        arguments = shlex.split(message.content)
        if len(arguments) != 2:
            await self.send_embed(message, "WarBot Link", "Incorrect Usage: /link <account name>\nNote that if the name contains spaces it will need to be enclosed in quotes.")
            return
        # Parse out needed information to link
        username = arguments[1].replace('"', '')
        user_id = message.author.id
        # Add user to the servers linked accounts 
        server.users += [database.User(user_id, username)]
        # Save the updated server to the database
        self.database.write_server(server)
        # Send a message alerting of successful registration
        await self.send_embed(message, "WarBot Link", "Sucessfully registered %s to <@%s>" % (username, user_id))

    async def unlink(self, message, server):
        arguments = shlex.split(message.content)
        # Handle invalid uses
        if len(arguments) != 2:
            await self.send_embed(message, "WarBot Unlink", "Incorrect Usage: /unlink <account name>\nNote that if the name contains spaces it will need to be enclosed in quotes.")
            return
        # Parse out needed information to unlink
        username = arguments[1].replace('"', '')
        deleted_user = utility.delete(server.users, lambda x: x.account_name == username and x.user_id == message.author.id)
        # Handle if no user existed to unlink
        if not deleted_user:
            utility.log("Unregister invalid key (%s)" % username)
            await self.send_embed(message, "WarBot Unlink", "No user (%s) to unregister for this discord account" % username)
            return
        # Save the updated server to the database
        deleted_user = self.database.write_server(server)
        await self.send_embed(message, "WarBot Unlink", "Sucessfully unregistered %s" % username)


    async def get_war(self, clan):
        # Try to gather war information logging if errors occur
        try:
            # war = asyncio.run(self.coc_client.get_current_war(clan.clan_tag))
            war = await self.coc_client.get_current_war(clan.clan_tag)
        except coc.PrivateWarLog as exception:
            utility.log("Private War Log")
            return None
        except Exception as exception:
            utility.log(type(exception).__name__)
            return None
        # Check for special cases with CWL which cause wars to not be caught
        if not war:
            war = await self.coc_client.get_current_war(clan.clan_tag, cwl_round=coc.WarRound.current_preparation)
        if war.league_group and len(war.league_group.rounds) == 7:
            war = await self.coc_client.get_current_war(clan.clan_tag, cwl_round=coc.WarRound.current_preparation)
        # If opponent name is NULL set war to NULL
        if war.opponent.name is None:
            war = None
        # If war resulting in None value, log that no war was found for the clan
        if war is None:
            utility.log('No current war to update to for %s' % clan.clan_tag)
        else:
            # Log that the war information was updated
            utility.log('Updated war info for %s' % clan.clan_tag)
        return war

    async def send_time_remaining(self, message, clan):
        # Get the war information for the requested clan
        clan_data = await self.coc_client.get_clan(clan.clan_tag)
        war = await self.get_war(clan)
        if not war:
            await self.send_embed(message, "WarBot War Time Remaining", "No war to display information for %s.\nThe clan war log MUST be set to public in order for war info to be displayed." % clan_data.name)
            return
        # If war exists, get the time remaining and send it to the channel request was received from
        time_remaining = war.end_time.seconds_until / 60
        minutes = int(time_remaining % 60)
        hours = int(time_remaining / 60)
        await self.send_embed(message, "WarBot War Time Remaining", "%s has %d hours and %d minutes remaining in war against %s." % (clan_data.name, hours, minutes, war.opponent.name))

    async def send_current_war(self, message, clan):
        # Get the war data for the requested clan
        clan_data = await self.coc_client.get_clan(clan.clan_tag)
        war = await self.get_war(clan)
        if not war:
            await self.send_embed(message, "WarBot Current War", "No war to display information for %s.\nThe clan war log MUST be set to public in order for war info to be displayed." % clan_data.name)
            return
        # If in preparation, no info to output so just state in preparation phase
        if war.state == 'preparation':
            await self.send_embed(message, "WarBot Current War", "%s's current war is against %s. We are currently in the preparation phase." % (clan_data.name, war.opponent.name))
        else:
            # Otherwise, calculate the attacks used and the total remaining and send the message
            used = 0
            attacks = ''
            for attack in war.attacks:
                if attack.attacker.clan.name == clan_data.name: used += 1
                if war.is_cwl: attacks = str(used) + '/' + str(war.team_size)
                else: attacks = str(used) + '/' + str(war.team_size * 2)
            await self.send_embed(message, "WarBot Current War", "%s's current war is against %s. We have used %s attacks and are currently %s." % (clan_data.name, war.opponent.name, attacks, war.status))

    async def configure_clan(self, message, server, clan):
        # Handle invalid uses
        arguments = message.content.split(' ')
        if len(arguments) != 1:
            await self.send_embed(message, "WarBot Configure", "Incorrect Usage: %sconfigure" % clan.clan_symbol)
            return
        # Set the clan announcement channel to the channel the command was sent in
        clan.clan_announcement_channel = message.channel.id
        # Update the clan in the server and write the server to the database
        utility.replace(server.clans,lambda x: x.clan_symbol == clan.clan_symbol, clan)
        self.database.write_server(server)
        # Send a message alerting of successful registration
        clan_data = await self.coc_client.get_clan(clan.clan_tag)
        await self.send_embed(message, "WarBot Configure", "This channel is now the war announcement channel for %s" % clan_data.name)
        return
        


    async def on_message(self, message):
        # If message author is bot, ignore
        if message.author == self.user:
            return

        # Handle registration before trying to match command
        if message.content == '/serverinfo':
            await self.send_server_info(message)
            return
        elif message.content.startswith('/register'):
            await self.register_clan(message)
            return
          
        potential_command = message.content[1:]
        if ' ' in potential_command: potential_command = potential_command.split(' ')[0]
        valid_commands = ['link', 'unlink', 'registry', 'currentwar', 'timeleft', 'configure']
        # Ignore messages that aren't commands
        if len(message.content) <= 0 or message.content[0].isalpha() or message.content[0].isdigit() or potential_command not in valid_commands:
            return

        # Read the server for handling commands
        server = self.database.read_server(message.guild.id)
        # If no server exists, alert user to register a clan
        if server is None:
            await self.send_embed(message, "WarBot Registration", "This discord server has not been registered with WarBot.\nRegister a clan first with /register <clan tag> <command symbol>.")
            return
        # Find the clan that matches the symbol
        symbol = message.content[0]
        clan = utility.find(server.clans, lambda x: x.clan_symbol == symbol)
        # Handle no clan being registered for this symbol
        if not clan:
            # # Commands dealing w/ account linking
            if message.content.startswith('/unlink'):
                await self.unlink(message, server)
            elif message.content.startswith('/registry'):
                await self.send_registry(message, server)
            elif message.content.startswith('/link'):
                await self.link(message, server)
            else:
                # Error case for requesting an command for an unregistered clan
                await self.send_embed(message, "WarBot Registration", "There is no clan registered with WarBot using this symbol on this server.\nRegister a clan first with /register <clan tag> <command symbol>.")
            return

        if message.content[1:].startswith('currentwar'):
            await self.send_current_war(message, clan)
        elif message.content[1:].startswith('timeleft'):
            await self.send_time_remaining(message, clan)
        elif message.content[1:].startswith('configure'):
            await self.configure_clan(message, server, clan)

    async def time_to_send(self, clan):
        # Update the war information to the proper clan
        war = await self.get_war(clan)
        # If war is going on, check if it is ending within 3-4 hours and return true if so
        if war:
            time_remaining = war.end_time.seconds_until / 60
            hours = int(time_remaining / 60)
            return hours == 3
        # Otherwise, return false since no war to send
        return False

    async def get_warning_message(self, server, clan):
        # Log that message is being retrived
        clan_data = await self.coc_client.get_clan(clan.clan_tag)
        war = await self.get_war(clan)
        utility.log("Retrieving war end warning message for %s" % clan_data.name)
        # Get proper total based on CWL or not
        total_attacks = war.team_size if war.is_cwl else war.team_size * 2
        # Initialize attacks to empty list and attacks at 0
        our_attackers = []
        attacks = 0
        # Loop through all attacks counting our attacks and adding attackers to list
        for attack in war.attacks:
            if attack.attacker.clan.name == clan_data.name:
                our_attackers.append(attack.attacker.name)
                attacks += 1
        # Initialize message with default statistics at the top
        message = 'Our war with ' + war.opponent.name + ' is ending in less than 4 hours...\nWe are currently ' + war.status + ' and have used (' + str(
            attacks) + '/' + str(total_attacks) + ') attacks, the following player have remaining attacks.\n'
        member_list = []
        # Add all members of clan to list
        for member in war.clan.members:
            member_list.append(member.name)
        # Go through all the names outputting their remaining attacks
        for name in member_list:
            # Count total used
            attacks_completed = our_attackers.count(name)
            # Set user id if present in registration
            user = utility.find(server.users, lambda x: x.account_name == name)
            if user is None: user_id = ''
            else: user_id = '<@%s>' % user.user_id
            # If CWL only 1 attack otherwise 2 so output appropriately
            if war.is_cwl:
                if attacks_completed == 0:
                    message += (name + ' - 1 remaining. ' + user_id + '\n')
            else:
                if attacks_completed == 0:
                    message += (name + ' - 2 remaining. ' + user_id + '\n')
                elif attacks_completed == 1:
                    message += (name + ' - 1 remaining. ' + user_id + '\n')
        return message

    async def poll_war_announcements(self):
        # Poll while client connection is up
        while not self.is_closed():
            # Read all the servers from the database
            servers = self.database.read_servers()
            for server in servers:
                # For each clan in the servers check if it is time to send the war ending message
                for clan in server.clans:
                    # If no channel is set skip this clan
                    if not clan.has_clan_announcement_channel(): continue
                    # Send the message if the war ends soon
                    if await self.time_to_send(clan):
                        utility.log("Sending war ending soon message for %s in server %s" % (clan.clan_tag, server.server_id))
                        channel = self.get_channel(int(clan.clan_announcement_channel))
                        await channel.send(await self.get_warning_message(server, clan))
            # Sleep for an hour before checking again
            await asyncio.sleep(3600) # Checks every hour (3600sec)

    async def on_ready(self):
        await self.coc_client.login(os.getenv('EMAIL'), os.getenv('PASS'))
        # Log that successful login has occurred
        utility.log("Successfully logged in as %s" % self.user)
        print("Successfully logged in as %s" % self.user)
        # Create event loop for checking if war is ending soon
        await self.loop.create_task(self.poll_war_announcements())