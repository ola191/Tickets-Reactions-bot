import logging
import datetime
import os
import asyncio
import sys
from typing import Literal, Optional

import sqlite3
import json

import discord
from discord.ext import commands
from discord import Color

from utils.embeds import create_embed, create_error_embed, create_success_embed

with open('config.json', 'r') as f:
    config = json.load(f)
    token = config["token"]
    guildId = config["GuildId"]

MY_GUILD = discord.Object(id=guildId)


async def change_bot_status(guild_count, total_member):
    await client.wait_until_ready() 
    while not client.is_closed():
        await client.change_presence(activity=discord.Game(name="docs : nomartnotes.xyz"))
        await asyncio.sleep(4)
        await client.change_presence(activity=discord.Game(name="{} members in {} servers".format(total_member, guild_count)))
        await asyncio.sleep(4)

class MyBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix='!', intents=intents)
        self.remove_command("help")

    def create_tables(self, guild_id):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                project_id INTEGER,
                name TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                priority TEXT,
                status TEXT,
                assigned_to TEXT,
                authorized_to_change TEXT,
                start_date TEXT,
                due_date TEXT,
                progress_status TEXT,
                users_notes TEXT,
                comments TEXT,
                UNIQUE(server_id, project_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                ticket_id INTEGER,
                name TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                priority TEXT,
                status TEXT,
                assigned_to TEXT,
                authorized_to_change TEXT,
                start_date TEXT,
                due_date TEXT,
                progress_status TEXT,
                owner TEXT,
                comments TEXT,
                UNIQUE(server_id, ticket_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                react_id INTEGER,
                category TEXT,
                react_type TEXT,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                UNIQUE(server_id, react_id)
            )
        ''')

    async def setup_database(self):
        self.conn = sqlite3.connect('db/mydatabase.db')
        self.cursor = self.conn.cursor()
        print(f"[{datetime.datetime.now()}] [\033[1;35mCONSOLE\033[0;0m]: Database [\033[1;35mSQLite\033[0;0m] setup.") 

        try:
            for guild in self.guilds:
                self.create_tables(guild.id)
            print(f"[{datetime.datetime.now()}] [\033[1;35mCONSOLE\033[0;0m]: tables [\033[1;35mSQLite\033[0;0m] created.")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] [\033[f91mERROR\033[0;0m]: {e}")
        
        # self.conn.commit()

    async def setup_hook(self):
        await load_all_cogs()
        
        try:
            animation = ["\\", "|", "/", "-"]
            animation_index = 0
            sys.stdout.write(f"[{datetime.datetime.now()}] [\033[37mCONSOLE\033[0;0m]: Synchronizing slash commands...")
            sys.stdout.flush()
            
            animation_task = asyncio.create_task(self.animate_sync(animation, animation_index))
            
            await self.tree.sync()
            
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass
            
            sys.stdout.write(f"\r[{datetime.datetime.now()}] [\033[1;36mCONSOLE\033[0;0m]: Slash commands synchronized with guilds    \n")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"[{datetime.datetime.now()}] [\033[91mERROR\033[0;0m]: {e}")

    async def animate_sync(self, animation, index):
        while True:
            sys.stdout.write(f"\r[{datetime.datetime.now()}] [\033[37mCONSOLE\033[0;0m]: Synchronizing slash commands {animation[index]}")
            sys.stdout.flush()
            index = (index + 1) % len(animation)
            await asyncio.sleep(0.2)


    async def close(self):
        await super().close()
        # self.conn.close()


async def load_all_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

intents = discord.Intents.all()
client = MyBot(intents=intents)

@client.event
async def on_ready():
    try:
        await client.setup_database()
        botName = "tickets&reactions"
        print(f"[{datetime.datetime.now()}] [\033[1;32mCONSOLE\033[0;0m]: {botName} ready")
        
        log_channel = client.get_channel(1012379305843626105)
        now = datetime.datetime.now(datetime.timezone.utc)
        embed = create_success_embed(f"{botName} ready")
        guild_count = len(client.guilds)
        total_members = sum(guild.member_count for guild in client.guilds)
        client.loop.create_task(change_bot_status(guild_count, total_members))
        await log_channel.send(embed=embed)
    except BaseException as error:
        print('An exception occurred: {}'.format(error))

@client.command()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}") 
        return
    
    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
    
@client.event
async def on_guild_join(guild):
    try:
        print(f"[{datetime.datetime.now()}] [\033[1;35mCONSOLE\033[0;0m]: Tables created for guild:  [\033[1;35m{guild.name}\033[0;0m] - [\033[1;35m{guild.id}\033[0;0m] .")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] [\033[91mCONSOLE\033[0;0m]: An error occurred while creating tables for guild:  [\033[1;35m{guild.name}\033[0;0m] - [\033[1;35m{guild.id}\033[0;0m] : {e}")

client.run(token, log_handler=None)