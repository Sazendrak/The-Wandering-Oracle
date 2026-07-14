import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

from data_loader import DataManager

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize and attach DataManager
bot.data_manager = DataManager()

@bot.event
async def setup_hook():
    bot.data_manager.load_all_data()
    print("Data loaded successfully.")

    await bot.load_extension("cogs.lookup")
    print("Loaded lookup cog.")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_BOT_TOKEN is not set in the environment.")
