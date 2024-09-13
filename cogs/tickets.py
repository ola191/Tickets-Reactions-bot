import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands, Color

from utils.embeds import create_error_embed
from utils.error_handler import handle_command_exception

from db.database import execute_select, execute_query, generate_ticket_id

class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, client):
        self.client = client
        self.status = True

    @app_commands.command(name="create", description="Create a new ticket")
    async def create(self, interaction: discord.Interaction, title: Optional[str] = None, description: Optional[str] = None):
        try:
            server_id = interaction.guild.id
            ticket_id = generate_ticket_id()
            user_id = interaction.user.id
            creation_date = datetime.datetime.utcnow().isoformat()

            query = "SELECT admin_role_ids, log_channel_id FROM config WHERE server_id = ?"
            data = execute_select(query, (server_id,))

            if not data:
                embed = create_error_embed(f"No configuration found for this server. Please configure the bot. Use command /help config.")
                await interaction.response.send_message(embed=embed)
                return

            admin_role_ids, log_channel_id = data[0]

            missing_fields = []
            if not admin_role_ids or admin_role_ids == "null" or admin_role_ids == "[]":
                missing_fields.append("Admin roles")
            if not log_channel_id:
                missing_fields.append("Log channel")

            if missing_fields:
                embed = create_error_embed(f"The following settings are missing: {', '.join(missing_fields)}. Please set them up.")
                await interaction.response.send_message(embed=embed)
                return

            insert_query = """
                INSERT INTO tickets (server_id, ticket_id, title, description, created_at, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            execute_query(insert_query, (server_id, ticket_id, title or "No title", description or "No description", creation_date, user_id))

            embed = discord.Embed(title="New Ticket Created", description=f"Your ticket has been created successfully. Ticket ID: {ticket_id}", color=Color.green())
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await handle_command_exception(interaction, self.client, None, "An error occurred while creating the ticket.", e)

    @app_commands.command(name="view", description="View your tickets")
    async def view(self, interaction: discord.Interaction):
        try:
            server_id = interaction.guild.id
            user_id = interaction.user.id

            query = "SELECT ticket_id, title, description, created_at, status FROM tickets WHERE server_id = ? and assigned_to = ?"
            tickets = execute_select(query, (server_id, user_id))

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
                embed = discord.Embed(title="No Tickets Found", description="There are no tickets for this server.", color=Color.red())

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await handle_command_exception(interaction, self.client, None, "An error occurred while viewing tickets.", e)

    @app_commands.command(name="close", description="Close a ticket")
    async def close(self, interaction: discord.Interaction, ticket_id: int):
        try:
            server_id = interaction.guild.id
            user_id = interaction.user.id

            query = "SELECT assigned_to FROM tickets WHERE server_id = ? AND ticket_id = ?"
            assigned_to = execute_select(query, (server_id, ticket_id))

            if assigned_to[0][0] != user_id:
                embed = discord.Embed(title="Failure", description="You are not assigned to this ticket.", color=Color.red())
                await interaction.response.send_message(embed=embed)
                return

            update_query = "UPDATE tickets SET status = 'closed' WHERE server_id = ? AND ticket_id = ? and assigned_to = ?"
            rowcount = execute_query(update_query, (server_id, ticket_id, user_id))

            if rowcount > 0:
                embed = discord.Embed(title="Ticket Closed", description=f"Ticket #{ticket_id} has been closed.", color=Color.green())
            else:
                embed = discord.Embed(title="Failure", description="This ticket does not exist or cannot be closed.", color=Color.red())

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await handle_command_exception(interaction, self.client, None, "An error occurred while closing the ticket.", e)

async def setup(client):
    if Tickets(client).status:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Tickets.__name__}\033[0;0m] loaded : Status [\033[1;32mEnable\033[0;0m]")
        await client.add_cog(Tickets(client))
    else:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Tickets.__name__}\033[0;0m] loaded : Status [\033[1;31mUnable\033[0;0m]")
