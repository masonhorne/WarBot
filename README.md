# Clash of Clans Bot - _WarBot_

**WarBot** is a Clash of Clans Discord bot that alerts users of remaining attacks in war.

## Installation

1. For package installation run this command.

   `pip install -r requirements.txt`

2. Create a `.env` file in the root directory with the following variables:

- EMAIL: Email to authenticate with clash of clans API
- PASS: Password for authenticating with clash of clans API
- TOKEN: Token for discord bot
- ATLAS_URI: URI for mongodb atlas connection
- DB_NAME: Name of collection to access in mongo atlas

## Supported Commands

### General Commands

- /register <clan_tag> <clan_symbol>
  - Registers a clan based on the provided clan tag for the current discord server and sets the clans command prefix to the provided symbol.
- /serverinfo
  - Lists all registered clans and users for the current discord server.
- /registry
  - Sends a list of all linked accounts for this discord server.
- /link <account_name>
  - Links a clash of clans account with the provided in game name with the current discord account.
- /unlink <account_name>
  - Unlinks a clash of clans account with the provided in game name from the current discord account.

### Clan Specific Commands

> These use ? to denote the registered clan symbol.

- ?currentwar
  - Sends information about the clans currently active war.
- ?timeleft
  - Sends the time remaining in the clans active war.
- ?configure
  - Registers the current channel as the announcement channel for the clan.
