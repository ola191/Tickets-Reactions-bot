import datetime
from typing import Literal

import discord
from discord.ext import commands
from discord import app_commands
from discord import Color

from utils.embeds import create_error_embed

import sqlite3

from typing import Optional, Literal

from utils.error_handler import handle_command_exception

class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, client):
        self.client = client
        self.status = True
        
        self.db_connection = sqlite3.connect('db/mydatabase.db')
        self.db_cursor = self.db_connection.cursor()

    @app_commands.command(name="create", description="Create a new ticket")
    async def create(self, interaction: discord.Interaction, title: Optional[str] = None, description: Optional[str] = None):
        try:
            server_id = interaction.guild.id
            ticket_id = self._generate_ticket_id()
            user_id = interaction.user.id
            creation_date = datetime.datetime.utcnow().isoformat()
            
            self.db_cursor.execute('''
                SELECT admin_role_ids, log_channel_id FROM config WHERE server_id = ?
            ''', (server_id,))
                                    
            data = self.db_cursor.fetchone()
            
            if data is None:
                embed = create_error_embed(f"No configuration found for this server. Please configure the bot. Use command /help config.")
                await interaction.response.send_message(embed=embed)
            else:
                admin_role_ids, log_channel_id = data

                missing_fields = []

                if not admin_role_ids or admin_role_ids == "null" or admin_role_ids == "[]":
                    missing_fields.append("Admin roles")

                if not log_channel_id:
                    missing_fields.append("Log channel")

                if missing_fields:
                    missing_fields_str = ", ".join(missing_fields)
                    embed = create_error_embed(f"The following settings are missing: {missing_fields_str}. Please set them up.")
                    await interaction.response.send_message(embed=embed)
                    return
            
            self.db_cursor.execute("INSERT INTO tickets (server_id, ticket_id, title, description, created_at, assigned_to) VALUES (?, ?, ?, ?, ?, ?)", (server_id, ticket_id, title or "No title", description or "No description", creation_date, user_id))
            self.db_connection.commit()
            
            embed = discord.Embed(title="New Ticket Created", description=f"Your ticket has been created successfully. Ticket ID: {ticket_id}", color=Color.green(),)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while creating the ticket.", e
            )
            
    @app_commands.command(name="view", description="View your tickets")
    async def view(self, interaction: discord.Interaction):
        try:
            server_id = interaction.guild.id
            user_id = interaction.user.id
            
            self.db_cursor.execute('''
                SELECT ticket_id, title, description, created_at, status FROM tickets
                WHERE server_id = ? and assigned_to = ?
            ''', (server_id, user_id,))
            tickets = self.db_cursor.fetchall()

            if tickets:
                embed = discord.Embed(title="Tickets", color=Color.teal())
                for ticket in tickets:
                    ticket_id, title, description, created_at, status = ticket
                    embed.add_field(
                        name=f"Ticket #{ticket_id}",
                        value=f"Title: {title}\nDescription: {description}\nCreated on: {created_at}\nStatus: {status}",
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="No Tickets Found",
                    description="There are no tickets for this server.",
                    color=Color.red()
                )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while viewing tickets.", e
            )

    @app_commands.command(name="close", description="Close a ticket")
    async def close(self, interaction: discord.Interaction, ticket_id: int):
        try:
            server_id = interaction.guild.id
            user_id = interaction.user.id
            
            self.db_cursor.execute('''
                                    SELECT assigned_to FROM tickets WHERE server_id = ? AND ticket_id = ?
                                    ''', (server_id, ticket_id,))
                                    
            assigned_to = self.db_cursor.fetchone()[0]
            
            if assigned_to != user_id:
                embed = discord.Embed(
                    title="Failure",
                    description="You are not assigned to this ticket.",
                    color=Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            self.db_cursor.execute('''
                UPDATE tickets
                SET status = 'closed'
                WHERE server_id = ? AND ticket_id = ? and assigned_to = ?
            ''', (server_id, ticket_id, user_id,))
            self.db_connection.commit()

            if self.db_cursor.rowcount > 0:
                embed = discord.Embed(
                    title="Ticket Closed",
                    description=f"Ticket #{ticket_id} has been closed.",
                    color=Color.green()
                )
            else:
                embed = discord.Embed(
                    title="Failure",
                    description="This ticket does not exist or cannot be closed.",
                    color=Color.red()
                )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while closing the ticket.", e
            )
            
    def _generate_ticket_id(self):
        try:
            self.db_cursor.execute('SELECT MAX(ticket_id) FROM tickets')
            max_id = self.db_cursor.fetchone()[0]
            return (max_id or 0) + 1
        except Exception as e:
            print(f"Error generating ticket ID: {e}")
            return None
        
async def setup(client):
    if Tickets(client).status:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Tickets.__name__}\033[0;0m] loaded : Status [\033[1;32mEnable\033[0;0m]")
        await client.add_cog(Tickets(client))
    else:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Tickets.__name__}\033[0;0m] loaded : Status [\033[1;31mUnable\033[0;0m]")