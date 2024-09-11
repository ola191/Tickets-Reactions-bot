import datetime
from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.GroupCog, name="help"):
    def __init__(self, client):
        self.client = client
        self.status = True

    @app_commands.command(name="commands", description="Displays possible commands for the bot")
    async def commands(self, interaction: discord.Interaction):
        em = discord.Embed(
            title="**ProjectBot Help**",
            color=discord.Color.purple()
        )
        em.set_thumbnail(
            url=self.client.user.avatar.url
        )
        
        commands = [com for com in self.client.tree.walk_commands() if isinstance(com, app_commands.Command)]
        groups = [com for com in self.client.tree.walk_commands() if isinstance(com, app_commands.Group)]
        
        general_commands = []
        grouped_commands = {}

        for command in commands:
            if command.parent:
                if command.parent.name not in grouped_commands:
                    grouped_commands[command.parent.name] = []
                grouped_commands[command.parent.name].append(command)
            else:
                general_commands.append(command)

        def format_command_with_args(cmd):
            args = "  ".join([f"`<{param.name}>`" for param in cmd.parameters])
            if args:
                return f"{cmd.name} {args}"
            return f"/{cmd.name}"

        if general_commands:
            em.add_field(name="> General Commands", value="", inline=False)
            for cmd in general_commands:
                cmd_with_args = format_command_with_args(cmd)
                em.add_field(name=cmd_with_args, value=cmd.description if cmd.description else "No description provided.", inline=False)

        for group in groups:
            group_cmds = grouped_commands.get(group.name, [])
            if group_cmds:
                em.add_field(name=f"** \n/{group.name}**", value="", inline=False)
                for cmd in group_cmds:
                    cmd_with_args = format_command_with_args(cmd)
                    em.add_field(name=cmd_with_args, value=cmd.description if cmd.description else "No description provided.", inline=False)
        
        em.set_footer(text="Support Server - https://discord.gg/2eqhnRPeyU \nProjectBot made with ❤️ by Olcia")

        await interaction.response.send_message(embed=em)

async def setup(client):
    if Help(client).status:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Help.__name__}\033[0;0m] loaded : Status [\033[1;32mEnable\033[0;0m]")
        await client.add_cog(Help(client))
    else:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Help.__name__}\033[0;0m] loaded : Status [\033[1;31mUnable\033[0;0m]")