# Clash of Clans Bot - *WarBot*

**WarBot** is a Clash of Clans Discord bot that alerts users of attacks remaining in war

By: **Mason Horne**

## Images

Here's an example of the commands and features:

![](https://i.imgur.com/1QT8ySg.png)

![](https://i.imgur.com/7vOUT9M.png)

![](https://i.imgur.com/MgBFUJW.png)




## Notes

Currently supports 2 different commands for each clan!
- [x] (!/$/@) timeleft returns the remaining time in the current war
- [x] (!/$/@) currentwar returns information about the current war taking place
- [x] Receive a notification 4 hours before the end of war containing who has remaining attacks
- [x] Ability to register your discord account to your in game name for push notifications through discord

## Hosting

- [x] Previously the bot was hosted through Repl.it. This was done by creating a Flask web server and using Uptime Robot to ping the server every hour.
- [x] Currently the bot is being hosted on a Raspberry Pi 4. Which is set to launch the script on boot and await internet connection before connecting to Discord.
## License

    Copyright 2021 Mason Horne

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
