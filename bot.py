import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def read_json_data(file_name):
    """
    Utility function to read JSON files from the data/avrae directory.
    The data directory is resolved relative to this file (bot.py).
    """
    # Use absolute path from current directory or relative.
    # Usually better to be safe and use relative to bot.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "data", "avrae", file_name)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in {filepath}")
        return None
    except OSError as e:
        print(f"Error reading {filepath}: {e}")
        return None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.command(name='two-status')
async def two_status(ctx):
    """Diagnostic ping command to check status and read data file."""
    data = read_json_data("twr-items-1.json")
    if data is None:
        await ctx.send("Bot is online, but I couldn't find or parse `/data/avrae/twr-items-1.json`.")
    else:
        # Assuming the JSON is a list or dictionary.
        count = len(data) if isinstance(data, (list, dict)) else 1
        await ctx.send(f"Bot is online! Successfully parsed `/data/avrae/twr-items-1.json` containing {count} top-level keys/objects.")

if __name__ == '__main__':
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_BOT_TOKEN is not set in the environment.")
