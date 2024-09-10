import datetime
from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands
from discord import Color

class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, client):
        self.client = client
        self.status = True

    @app_commands.command(name="create", description="new ticket")
    async def commands(self, interaction: discord.Interaction):
        embed = discord.Embed(title="new ticket", description="you have created a new ticket", color=Color.teal(),)
        await interaction.response.send_message(embed=em)

async def setup(client):
    if Tickets(client).status:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Tickets.__name__}\033[0;0m] loaded : Status [\033[1;32mEnable\033[0;0m]")
        await client.add_cog(Tickets(client))
    else:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Tickets.__name__}\033[0;0m] loaded : Status [\033[1;31mUnable\033[0;0m]")