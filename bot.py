import asyncio
import json
import os
import discord
from discord.ext import commands
from db.database import setup_database
from utils.embeds import create_success_embed, create_embed
import datetime
import sys
from discord import Color

with open('config.json', 'r') as f:
    config = json.load(f)

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents, application_id=config["application_id"])

async def change_bot_status(guild_count, total_member):
    await client.wait_until_ready()
    while not client.is_closed():
        await client.change_presence(activity=discord.Game(name="docs : nomartnotes.xyz"))
        await asyncio.sleep(4)
        await client.change_presence(activity=discord.Game(name="{} members in {} servers".format(total_member, guild_count)))
        await asyncio.sleep(4)

async def load_all_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

async def sync_slash_commands():
    try:
        animation = ["\\", "|", "/", "-"]
        animation_index = 0

        sys.stdout.write(f"\r[{datetime.datetime.now()}] [\033[37mCONSOLE\033[0;0m]: Synchronizing slash commands {animation[animation_index]}")
        sys.stdout.flush()

        animation_task = asyncio.create_task(animate_sync(animation, animation_index))

        await client.tree.sync()

        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass

        sys.stdout.write(f"\r[{datetime.datetime.now()}] [\033[1;36mCONSOLE\033[0;0m]: Slash commands synchronized with guilds    \n")
        sys.stdout.flush()
        log_channel = client.get_channel(int(config["log_channel_id"]))
        await log_channel.send(embed=create_embed(title="Info", description="Slash commands synchronized with guilds", color=Color.from_rgb(100,150,255)))
    except Exception as e:
        print(f"[{datetime.datetime.now()}] [\033[91mERROR\033[0;0m]: {e}")

async def animate_sync(animation, index):
    while True:
        sys.stdout.write(f"\r[{datetime.datetime.now()}] [\033[37mCONSOLE\033[0;0m]: Synchronizing slash commands {animation[index]}")
        sys.stdout.flush()
        index = (index + 1) % len(animation)
        await asyncio.sleep(0.2)

@client.event
async def on_ready():
    try:
        await setup_database(client)
        botName = "tickets&reactions"
        print(f"[{datetime.datetime.now()}] [\033[1;32mCONSOLE\033[0;0m]: {botName} ready")
        
        log_channel = client.get_channel(int(config["log_channel_id"]))
        embed = create_success_embed(f"{botName} ready")
        guild_count = len(client.guilds)
        total_members = sum(guild.member_count for guild in client.guilds)
        client.loop.create_task(change_bot_status(guild_count, total_members))
        await log_channel.send(embed=embed)
        await sync_slash_commands()
    except BaseException as error:
        print(f'An exception occurred: {error}')

async def main():
    await load_all_cogs()
    await client.start(config["token"])

if __name__ == "__main__":
    asyncio.run(main())