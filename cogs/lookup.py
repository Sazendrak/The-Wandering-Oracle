import discord
from discord.ext import commands
from discord import app_commands
import json

class LookupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # In memory storage for user toggles: {user_id: True/False}
        self.user_srd_toggles = {}

    @app_commands.command(name="toggle_srd", description="Toggle always-on SRD inclusion for your searches")
    async def toggle_srd(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current_state = self.user_srd_toggles.get(user_id, False)
        new_state = not current_state
        self.user_srd_toggles[user_id] = new_state

        state_str = "ON" if new_state else "OFF"
        await interaction.response.send_message(f"Your SRD inclusion toggle is now {state_str}.", ephemeral=True)

    def format_embed(self, item, source_type: str):
        name = item.get("name", "Unknown")
        desc = item.get("description", "No description provided.")

        # Truncate description if too long
        if len(desc) > 2000:
            desc = desc[:1997] + "..."

        if source_type == "homebrew":
            # Server thematic color (e.g., Purple/Blue)
            embed = discord.Embed(title=name, description=desc, color=discord.Color.blurple())
            embed.set_footer(text="[Approved Homebrew]")
            # Add url if available
            if item.get("source_url"):
                embed.url = item["source_url"]
        else:
            # Gray/Neutral color for SRD
            embed = discord.Embed(title=name, description=desc, color=discord.Color.light_grey())
            embed.set_footer(text="[Official SRD Content]")

        # Add other common fields if available
        if "type" in item:
            embed.add_field(name="Type", value=item["type"], inline=True)
        if "rarity" in item:
            embed.add_field(name="Rarity", value=item["rarity"], inline=True)

        return embed

    @app_commands.command(name="lookup", description="Search for an item, spell, or feature")
    @app_commands.describe(
        query="The name of what you are searching for",
        include_srd="Expand search to include official SRD content (Overrides your toggle)"
    )
    async def lookup(self, interaction: discord.Interaction, query: str, include_srd: bool = False):
        user_id = interaction.user.id

        # Determine effective SRD inclusion
        # "The srd argument should cause the always on toggle to be treated as in for the single query."
        effective_srd = include_srd or self.user_srd_toggles.get(user_id, False)

        # Access DataManager from bot
        dm = self.bot.data_manager

homebrew_results = dm.search_homebrew(query)

srd_results = []
if effective_srd or not homebrew_results:
    srd_results = dm.search_srd(query)

        if not homebrew_results and not srd_results:
            await interaction.response.send_message("No results found in either Homebrew or SRD archives.", ephemeral=True)
            return

        embeds = []
        messages = []

        if homebrew_results:
            # Add at most 5 results to avoid embed limits
            for res in homebrew_results[:5]:
                embeds.append(self.format_embed(res, "homebrew"))

            if effective_srd and srd_results:
                for res in srd_results[:5]:
                    embeds.append(self.format_embed(res, "srd"))
        else:
            # No homebrew, but there are SRD results
            if not effective_srd:
                # explicit feedback logic:
                msg = "No matches were found in the server archives, however I've found entries in the Official SRD. Enable SRD inclusion to view them."
                await interaction.response.send_message(msg, ephemeral=True)
                return
            else:
                for res in srd_results[:5]:
                    embeds.append(self.format_embed(res, "srd"))

        if embeds:
            # Send up to 10 embeds in a single response
            await interaction.response.send_message(embeds=embeds[:10])
        else:
            await interaction.response.send_message("Unexpected error: No embeds generated.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LookupCog(bot))
