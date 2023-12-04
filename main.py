import dotenv
import os
from src import warbot

# Load API keys from environment variables
dotenv.load_dotenv()
# Initialize the WarBot with the credentials from environment for COC API
bot = warbot.WarBot()
# Start WarBot with Discord API token
bot.run(os.getenv('TOKEN'))

