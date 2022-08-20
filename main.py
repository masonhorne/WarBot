import dotenv
import os
import warbot


# Load API keys from environment variables
dotenv.load_dotenv()
# Initialize the WarBot with the credentials from environment for COC API
bot = warbot.WarBot(os.getenv('EMAIL'), os.getenv('PASS'), os.getenv('CHANNEL'))
# Start WarBot with Discord API token
bot.run(os.getenv('TOKEN'))

