import datetime
import json
from typing import Optional, List

import discord
from discord.ext import commands
from discord import app_commands, Color

from utils.embeds import create_error_embed
from utils.error_handler import handle_command_exception

from db.database import execute_select, execute_query, fetch_admin_role_ids, fetch_config, generate_ticket_id

class Tickets(commands.GroupCog, name="tickets"):
    def __init__(self, client):
        self.client = client
        self.status = True

    async def autocomplete_category(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        try:
            server_id = interaction.guild.id
            query = "SELECT tickets_categories FROM config WHERE server_id = ?"
            data = execute_select(query, (server_id,))

            if data and data[0]:
                category_ids = json.loads(data[0][0])

                guild = interaction.guild
                categories = [
                    (category.id, category.name)
                    for category in guild.categories
                    if category.id in category_ids and str(category.id).startswith(current)
                ]

                return [
                    app_commands.Choice(name=name, value=str(id))
                    for id, name in categories[:25]
                ]
                
        except Exception as e:
            print(f"Error in autocomplete_category: {e}")
            return []

    async def create_ticket_channel(self, guild: discord.Guild, category_id: int, channel_name: str) -> discord.TextChannel:
        category = discord.utils.get(guild.categories, id=category_id)
        if not category:
            raise ValueError("Category not found")

        channel = await guild.create_text_channel(name=channel_name, category=category)

        permissions = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        admin_role_ids = fetch_admin_role_ids(guild.id)
        
        for admin_role_id in admin_role_ids:
            role = guild.get_role(admin_role_id)
            if role:
                permissions[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        await channel.edit(overwrites=permissions)

        return channel

    @app_commands.command(name="create", description="Create a new ticket")
    @app_commands.describe(title="Title of the ticket", description="Description of the ticket", category="Category of the ticket")
    @app_commands.autocomplete(category=autocomplete_category)
    async def create(self, interaction: discord.Interaction, title: str, description: str, category: str):
        try:
            server_id = interaction.guild.id
            user_id = interaction.user.id
            creation_date = datetime.datetime.utcnow().isoformat()

            data = fetch_config(server_id)
            if not data:
                embed = create_error_embed(f"No configuration found for this server. Please configure the bot. Use command /help config.")
                await interaction.response.send_message(embed=embed)
                return

            admin_role_ids, log_channel_id, tickets_categories = data

            if int(category) not in tickets_categories:
                embed = create_error_embed(f"The category '{category}' does not exist. Please select a valid category.")
                await interaction.response.send_message(embed=embed)
                return

            ticket_id = generate_ticket_id()
            category_name = discord.utils.get(interaction.guild.categories, id=int(category)).name
            channel_name = f"ticket-{ticket_id}"
            # channel_id = interaction.channel.id

            channel = await self.create_ticket_channel(interaction.guild, int(category), channel_name)
            channel_id = channel.id
            insert_query = """
                INSERT INTO tickets (server_id, channel_id, ticket_id, title, description, category, created_at, owner)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            execute_query(insert_query, (server_id, channel_id, ticket_id, title, description, int(category), creation_date, user_id))

            insert_permission_query = """
                INSERT INTO ticket_permissions (ticket_id, user_id, role)
                VALUES (?, ?, 'user')
            """
            execute_query(insert_permission_query, (ticket_id, user_id))

            for admin_role_id in admin_role_ids:
                execute_query(insert_permission_query, (ticket_id, admin_role_id))

            embed = discord.Embed(
                title="New Ticket Created",
                description=f"Your ticket has been created successfully in category **{category_name}**. Ticket ID: {ticket_id}. Channel: {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await handle_command_exception(interaction, self.client, None, "An error occurred while creating the ticket.", e)

    @app_commands.command(name="view", description="View your tickets")
    async def view(self, interaction: discord.Interaction):
        try:
            server_id = interaction.guild.id
            user_id = interaction.user.id

            query = "SELECT ticket_id, title, description, created_at, status FROM tickets WHERE server_id = ? and owner = ?"
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

            query = "SELECT admin_role_ids, log_channel_id, tickets_categories FROM config WHERE server_id = ?"
            data = execute_select(query, (server_id,))

            if not data:
                embed = create_error_embed(f"No configuration found for this server. Please configure the bot. Use command /help config.")
                await interaction.response.send_message(embed=embed)
                return
            
            query = "SELECT owner, channel_id FROM tickets WHERE server_id = ? AND ticket_id = ?"
            result = execute_select(query, (server_id, ticket_id))

            if not result:
                embed = discord.Embed(title="Failure", description="Ticket not found.", color=Color.red())
                await interaction.response.send_message(embed=embed)
                return

            owner_id = result[0][0]
            channel_id = result[0][1]

            if owner_id != user_id:
                embed = discord.Embed(title="Failure", description="You are not assigned to this ticket.", color=Color.red())
                await interaction.response.send_message(embed=embed)
                return

            update_query = "UPDATE tickets SET status = 'closed' WHERE server_id = ? AND ticket_id = ? and owner = ?"
            rowcount = execute_query(update_query, (server_id, ticket_id, user_id))

            if rowcount > 0:
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    try:
                        await channel.delete()
                        embed = discord.Embed(title="Ticket Closed", description=f"Ticket #{ticket_id} has been closed.", color=Color.green())
                    except Exception as e:
                        embed = discord.Embed(title="Failure", description="Failed to delete the channel", color=Color.red())
                else:
                    embed = discord.Embed(title="Failure", description="No channel was found. " + str(channel_id), color=Color.red())
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
