import coc
import discord
from src import utility
import asyncio


class WarBot(discord.Client):

    # Default error message when unknown error occurs
    __DEM__ = 'The war is in an unpredicted state...'
    # Variable for ToValhalla key
    __TV__ = 'ToValhalla'
    # Variable for ValhallaRising key
    __VR__ = 'ValhallaRising'
    # Variable for Ragnarok key
    __R__ = 'Ragnarok'
    # Mapping of clan names to clan tags
    __CLANS__ = {'ToValhalla': '#28LGRG92U', 'ValhallaRising': '#2YQ2RLCC8', 'Ragnarok': '#2L2YVRU8V'}

    def __init__(self, coc_email, coc_pass, channel_id, *args, **kwargs):
        """
        Initializes the war bot with provided COC API credentials and channel id for war warning messages
        :param coc_email: email to access COC API
        :param coc_pass: password to access COC API
        :param channel_id: ID of channel to send reminder messages in
        :param args: arguments for discord client
        :param kwargs: arguments for discord client
        """
        # Initialize discord client with arguments
        super().__init__(*args, **kwargs)
        # Set the email and password for the COC Client as class variables
        self.__coc_email = coc_email
        self.__coc_pass = coc_pass
        # Store the channel id as a variable
        self.__channel_id = channel_id
        # Load linked accounts and main channel as class variables
        self.__linked_accounts = utility.load_registration()
        # Set war and main channel as NULL by default
        self.__war = None
        self.__main_channel = None
        # Await internet connection on host device
        utility.await_internet()
        # Log start message and initialize the clash of clans client
        utility.log("Starting Warbot with PID: %d" % utility.pid())
        self.coc_client = coc.login(
            self.__coc_email,
            self.__coc_pass,
            key_names="Made with coc.py",
            client=coc.EventsClient)

    async def update_war_info(self, tag):
        """
        Updates the war info to the current war for the clan name provided
        :param tag: ToValhalla, ValhallaRising, or Ragnarok
        """
        # Log that the war information is being updated
        utility.log('Updated war info for %s' % tag)
        # Set the war to NULL
        self.__war = None
        # Try to gather war information logging if errors occur
        try:
            self.__war = await self.coc_client.get_current_war(self.__CLANS__[tag])
        except coc.PrivateWarLog as exception:
            utility.log("Private War Log")
        except Exception as exception:
            utility.log(type(exception).__name__)
            return
        # Check for special cases with CWL which cause wars to not be caught
        if not self.__war:
            self.__war = await self.coc_client.get_current_war(self.__CLANS__[tag], cwl_round=coc.WarRound.current_preparation)
        if self.__war.league_group and len(self.__war.league_group.rounds) == 7:
            self.__war = await self.coc_client.get_current_war(self.__CLANS__[tag], cwl_round=coc.WarRound.current_preparation)
        # If opponent name is NULL set war to NULL
        if self.__war.opponent.name is None:
            self.__war = None
        # If war resulting in None value, log that no war was found for the clan
        if self.__war is None:
            utility.log('No current war to update to for %s' % tag)

    async def time_to_send(self):
        """
        Checks if the war is ending within the next 3 to 4 hours and returns the result
        :return: True if betwen 3-4 hours remaining in the war false otherwise
        """
        # Update the war information to the proper clan
        await self.update_war_info(self.__TV__)
        utility.log("Time to Send Check")
        # If war is going on, check if it is ending within 3-4 hours and return true if so
        if self.__war:
            time_remaining = self.__war.end_time.seconds_until / 60
            hours = int(time_remaining / 60)
            utility.log("Time to Send Value: %d" % hours)
            utility.log("Evaluation of time_to_send: " + str(hours == 3))
            return hours == 3
        # Otherwise, return false since no war to send
        return False

    def get_warning_message(self):
        """
        Builds the warning message that the war is ending soon tagging discord accounts that
        are registered to COC accounts missing attacks
        :return: Embed containing message to be sent
        """
        # Log that message is being retrived
        utility.log("Retrieving war end warning message")
        # Get proper total based on CWL or not
        if self.__war.is_cwl:
            total_attacks = self.__war.team_size
        else:
            total_attacks = self.__war.team_size * 2
        # Initialize attacks to empty list and attacks at 0
        our_attackers = []
        attacks = 0
        # Loop through all attacks counting our attacks and adding attackers to list
        for attack in self.__war.attacks:
            if attack.attacker.clan.name == clan_names[0]:
                our_attackers.append(attack.attacker.name)
                attacks += 1
        # Initialize message with default statistics at the top
        message = 'Our war with ' + self.__war.opponent.name + ' is ending in less than 4 hours...\nWe are currently ' + self.__war.status + ' and have used (' + str(
            attacks) + '/' + str(total_attacks) + ') attacks, the following player have remaining attacks.\n'
        member_list = []
        # Add all members of clan to list
        for member in self.__war.clan.members:
            member_list.append(member.name)
        # Go through all the names outputting their remaining attacks
        for name in member_list:
            # Count total used
            attacks_completed = our_attackers.count(name)
            # Set user id if present in registration
            try:
                user_id = '<@%s>' % str(self.__linked_accounts[name])
            except Exception:
                user_id = ''
            # If CWL only 1 attack otherwise 2 so output appropriately
            if self.__war.is_cwl:
                if attacks_completed == 0:
                    message += (name + ' - 1 remaining.' + user_id + '\n')
            else:
                if attacks_completed == 0:
                    message += (name + ' - 2 remaining.' + user_id + '\n')
                elif attacks_completed == 1:
                    message += (name + ' - 1 remaining.' + user_id + '\n')
        # Log embed is being created
        utility.log("Adding message to embed")
        embed = discord.Embed(title="The war is ending soon...", description=message, color=0x607d8b)
        # Log image is being added to embed
        utility.log("Adding image to embed")
        embed.set_thumbnail(
            url='https://clashofclans.com/uploaded-images-blog/_134x63_crop_center-center_90/1779622587_1641980234.png?mtime=20220112093714')
        # Return the resulting embed to send
        return embed

    async def check_war_time(self):
        """
        Checks hourly for if war is ending soon, if so sends a warning message to clan
        """
        # While the client is alive continue checking
        while not self.is_closed():
            # If it is time to send, gather the message and send it
            if await self.time_to_send():
                utility.log("Sending war ending soon message")
                if self.__main_channel is None:
                    utility.log("Message attempted to send but main channel was None")
                else:
                    await self.__main_channel.send(embed=self.get_warning_message())
            # Sleep for an hour before checking again
            await asyncio.sleep(3600)  # Checks every hour (3600sec)

    async def register(self, username, user_id, message):
        """
        Registers a discord account to a COC account and saves to memory
        :param username: username from in game to link
        :param user_id: discord id that is trying to register the username
        :param message: message that requested the account linking
        """
        # Add link for the account to the map
        self.__linked_accounts[username] = user_id
        # Backup registration to a file
        utility.backup_registration(self.__linked_accounts)
        # Send a message alerting of successful registration
        await message.channel.send("Sucessfully registered %s to <@%s>" % (username, user_id))

    async def unregister(self, username, message):
        """
        Unregisters a given accounts name and saves to memory
        :param username: username to be removed from the registry
        :param message: message that is requesting to unregister the account
        """
        # Try to remove the user from registry
        try:
            self.__linked_accounts.pop(username)
        except Exception:
            # Log if invalid message was send and notify user
            utility.log("Unregister invalid key (%s)" % username)
            await message.channel.send("No user (%s) to unregister" % username)
            return
        # Otherwise, backup the removal and send a notification that it was successful
        utility.backup_registration(self.__linked_accounts)
        await message.channel.send("Sucessfully unregistered %s" % username)

    async def send_time_remaining(self, tag, message):
        """
        Sends time remaining in war for the requested clan
        :param tag: tag of clan to display war info from
        :param message: message that contains the command given
        """
        # Update the war information to the requested clan
        await self.update_war_info(tag)
        # If war exists, get the time remaining and send it to the channel request was received from
        if self.__war:
            time_remaining = self.__war.end_time.seconds_until / 60
            minutes = int(time_remaining % 60)
            hours = int(time_remaining / 60)
            await message.channel.send("{0} has {1} hours and {2} minutes remaining in war against {3}.".format(
                tag, hours, minutes, self.__war.opponent.name))
        else:
            # Otherwise, log invalid request and send message to chat alerting unable to proceed
            utility.log("Invalid war information requested")
            await message.channel.send(
                self.__DEM__)

    async def send_current_war(self, tag, message):
        """
        Sends information on current war for the requested clan
        :param tag: tag of the clan to display information for
        :param message: message that the request for war information came from
        """
        # Update the war information for the requested clan
        await self.update_war_info(tag)
        # If war exists, begin building its message
        if self.__war:
            # Store the opponent name in variable
            name = self.__war.opponent.name
            # If in preparation, no info to output so just state in preparation phase
            if self.__war.state == 'preparation':
                await message.channel.send(
                    '{0}\'s current war is against {1}. We are currently in the preparation phase.'.format(
                        tag,
                        name))
            else:
                # Otherwise, calculate the attacks used and the total remaining and send the message
                used = 0
                attacks = ''
                for attack in self.__war.attacks:
                    if attack.attacker.clan.name == tag:
                        used += 1
                    if self.__war.is_cwl:
                        attacks = str(used) + '/' + str(self.__war.team_size)
                    else:
                        attacks = str(used) + '/' + str(self.__war.team_size * 2)
                await message.channel.send(
                    '{0}\'s current war is against {1}. We have used {2} attacks and are currently {3}.'.format(
                        tag,
                        name, attacks,
                        self.__war.status))
        else:
            # If invalid war just log invalid and send message notifying cannot proceed
            utility.log("Invalid war information requested")
            await message.channel.send(
                self.__DEM__
            )

    async def send_registry(self, user_message):
        """
        Creates a message detailing the registry and sends to chat
        :param user_message: Message that is requesting the registry
        """
        # Initialize message with size of registry
        message = "Currently {0} accounts have been registered!\n".format(len(self.__linked_accounts))
        # Add all registered accounts to message
        for name in self.__linked_accounts:
            message += "{0} - <@{1}>\n".format(name, self.__linked_accounts[name])
        # Add how to add other accounts to bottom of registry message
        message += "To register your account type $register <Account Name>.\n"
        message += "Note that the name MUST be identical to your in game name.\n"
        # Send the registry message to the channel
        await user_message.channel.send(message)

    async def on_ready(self):
        """
        Initializes the event loop for war ending soon notifications
        """
        # Log that successful login has occurred
        utility.log("We have logged in as {0.user}".format(self))
        # Store the main channel as a variable
        self.__main_channel = self.get_channel(int(self.__channel_id))
        # Create event loop for checking if war is ending soon
        self.loop.create_task(self.check_war_time())

    async def on_message(self, message):
        """
        Handles commands entered by users
        :param message: Message that contains the command
        """
        # If message author is bot, ignore
        if message.author == self.user:
            return
        # Commands dealing w/ registry
        elif message.content.startswith('$unregister'):
            await self.unregister(message.content.split(' ')[1], message)
        elif message.content.startswith('$registry'):
            await self.send_registry(message)
        elif message.content.startswith('$register'):
            await self.register(message.content.split(' ')[1], message.author.id, message)
        # Commands dealing with ToValhalla
        elif message.content.startswith('$currentwar'):
            await self.send_current_war(self.__TV__, message)
        elif message.content.startswith('$timeleft'):
            await self.send_time_remaining(self.__TV__, message)
        # Commands dealing with ValhallaRising
        elif message.content.startswith('!currentwar'):
            await self.send_current_war(self.__VR__, message)
        elif message.content.startswith('!timeleft'):
            await self.send_time_remaining(self.__VR__, message)
        # Commands dealing with Ragnarok
        elif message.content.startswith('@currentwar'):
            await self.send_current_war(self.__R__, message)
        elif message.content.startswith('@timeleft'):
            await self.send_time_remaining(self.__R__, message)
