import asyncio
import datetime
import discord
from discord.ui import Button, View
from discord.ext import commands
from discord import app_commands, Color
from utils.embeds import create_error_embed
import sqlite3
from typing import Optional
from utils.error_handler import handle_command_exception
from discord import app_commands, Embed, Color, TextChannel, Member, ButtonStyle, Interaction, ui

class Config(commands.GroupCog, name="config"):
    def __init__(self, client):
        self.client = client
        self.status = True
        self.db_connection = sqlite3.connect('db/mydatabase.db')
        self.db_cursor = self.db_connection.cursor()

    async def _check_permissions(self, interaction: discord.Interaction):
        server_id = interaction.guild.id
        user_id = interaction.user.id

        if user_id == interaction.guild.owner_id:
            return True

        self.db_cursor.execute('''SELECT admin_role_ids FROM config WHERE server_id = ?''', (server_id,))
        admin_role_ids = self.db_cursor.fetchone()

        if admin_role_ids is None:
            return False

        admin_role_ids = eval(admin_role_ids[0]) if admin_role_ids[0] else []

        for role in interaction.user.roles:
            if role.id in admin_role_ids:
                return True

        return False

    @app_commands.command(name="set", description="Set a configuration option for the server")
    async def set_config(self, interaction: Interaction, log_channel: Optional[TextChannel] = None, admin_role: Optional[Member] = None):
        try:
            server_id = interaction.guild.id
            self.db_cursor.execute('''SELECT admin_role_ids, log_channel_id FROM config WHERE server_id = ?''', (server_id,))

            data = self.db_cursor.fetchone()

            if data is None:
                self.db_cursor.execute('''INSERT INTO config (server_id, admin_role_ids, log_channel_id) VALUES (?, ?, ?)''', 
                                      (server_id, f'[{admin_role.id}]' if admin_role else '[]', log_channel.id if log_channel else None))
                embed = discord.Embed(title="Configuration Set", description="Configuration options have been successfully set.", color=discord.Color.green())
                await interaction.response.send_message(embed=embed)
                return

            admin_roles, current_log_channel_id = data
            admin_roles = eval(admin_roles) if admin_roles else []

            if admin_role:
                embed = discord.Embed(
                    title="Confirm Admin Role Replacement",
                    description=f"Are you sure you want to replace all admin roles with {admin_role.mention}?",
                    color=discord.Color.red()
                )

                class ConfirmView(View):
                    def __init__(self):
                        super().__init__(timeout=60.0)
                        self.value = None

                    @discord.ui.button(label="Yes", style=ButtonStyle.green)
                    async def yes_button(self, button: Button, interaction: Interaction):
                        self.value = True
                        self.stop()

                    @discord.ui.button(label="No", style=ButtonStyle.red)
                    async def no_button(self, button: Button, interaction: Interaction):
                        self.value = False
                        self.stop()

                view = ConfirmView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                
                await view.wait()

                if view.value is None:
                    embed = discord.Embed(
                        title="Operation Timed Out",
                        description="You took too long to respond. No changes have been made.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
                    return

                if view.value:
                    admin_roles = [admin_role.id]
                    embed = discord.Embed(
                        title="Admin Roles Updated",
                        description=f"All admin roles have been replaced with {admin_role.mention}.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="Operation Cancelled",
                        description="No changes have been made to the admin roles.",
                        color=discord.Color.red()
                    )
                await interaction.followup.send(embed=embed)
                if view.value:
                    self.db_cursor.execute('''UPDATE config SET admin_role_ids = ?, log_channel_id = ? WHERE server_id = ?''', 
                                          (str(admin_roles), current_log_channel_id, server_id))
                    self.db_connection.commit()
                return

            if log_channel:
                if current_log_channel_id == log_channel.id:
                    embed = discord.Embed(
                        title="Log Channel Already Set",
                        description=f"Log channel is already set to <#{current_log_channel_id}>.",
                        color=discord.Color.from_rgb(255, 255, 100)
                    )
                elif current_log_channel_id:
                    embed = discord.Embed(
                        title="Log Channel Updated",
                        description=f"Log channel is already set to <#{current_log_channel_id}>. Updated to <#{log_channel.id}>.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="Log Channel Set",
                        description=f"Log channel has been set to <#{log_channel.id}>.",
                        color=discord.Color.green()
                    )
                current_log_channel_id = log_channel.id
            else:
                embed = discord.Embed(
                    title="Configuration Updated",
                    description="Configuration options have been successfully updated.",
                    color=discord.Color.green()
                )

            self.db_cursor.execute('''UPDATE config SET admin_role_ids = ?, log_channel_id = ? WHERE server_id = ?''', 
                                  (str(admin_roles), current_log_channel_id, server_id))
            self.db_connection.commit()

            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await handle_command_exception(interaction, self.bot, self.db_cursor, "An error occurred while setting the configuration.", e)
            
    async def handle_command_exception(interaction, bot, cursor, message, exception):
        embed = discord.Embed(title="Error", description=message, color=Color.red())
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)
        print(exception)


    @app_commands.command(name="view", description="View the current server configuration")
    async def view_config(self, interaction: discord.Interaction):
        try:
            if not await self._check_permissions(interaction):
                await interaction.response.send_message(embed=create_error_embed("You don't have permissions to view this configuration."))
                return

            server_id = interaction.guild.id
            self.db_cursor.execute('''SELECT admin_role_ids, log_channel_id FROM config WHERE server_id = ?''', (server_id,))
            data = self.db_cursor.fetchone()

            if data is None:
                embed = discord.Embed(
                    title="No Configuration Found",
                    description="No configuration exists for this server.",
                    color=discord.Color.from_rgb(100, 150, 255)
                )
                await interaction.response.send_message(embed=embed)
                return

            admin_role_ids, log_channel_id = data
            admin_role_ids = eval(admin_role_ids) if admin_role_ids else []
            admin_roles_str = ", ".join([f"<@{user_id}>" for user_id in admin_role_ids]) if admin_role_ids else "None"

            embed = discord.Embed(
                title="Server Configuration",
                color=discord.Color.from_rgb(100, 150, 255)
            )
            embed.add_field(name="Log Channel", value=f"<#{log_channel_id}>" if log_channel_id else "Not set", inline=False)
            embed.add_field(name="Admin Roles", value=admin_roles_str, inline=False)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while viewing the configuration.",
                e
            )

    @app_commands.command(name="add", description="Add an admin user")
    async def add_config(self, interaction: discord.Interaction, admin_user: Optional[discord.Member] = None):
        try:
            if not await self._check_permissions(interaction):
                await interaction.response.send_message(embed=create_error_embed("You don't have permissions to use this command."))
                return

            server_id = interaction.guild.id
            self.db_cursor.execute('''SELECT admin_role_ids FROM config WHERE server_id = ?''', (server_id,))

            data = self.db_cursor.fetchone()

            if data is None:
                self.db_cursor.execute('''INSERT INTO config (server_id, admin_role_ids, log_channel_id) VALUES (?, ?, ?)''', (server_id, f'[{admin_user.id}]', None))
                embed = discord.Embed(
                    title="Admin User Added",
                    description=f"Admin user {admin_user.mention} has been successfully added.",
                    color=Color.green()
                )
            else:
                admin_users = eval(data[0]) if data[0] else []

                if admin_user:
                    if admin_user.id in admin_users:
                        embed = discord.Embed(
                            title="User Already Admin",
                            description=f"{admin_user.mention} is already an admin.",
                            color=Color.red()
                        )
                    else:
                        admin_users.append(admin_user.id)
                        self.db_cursor.execute('''UPDATE config SET admin_role_ids = ? WHERE server_id = ?''', (str(admin_users), server_id))
                        self.db_connection.commit()
                        
                        embed = discord.Embed(
                            title="Admin User Added",
                            description=f"Admin user {admin_user.mention} has been successfully added.",
                            color=Color.green()
                        )
                else:
                    embed = discord.Embed(
                        title="No User Provided",
                        description="No user was provided to add.",
                        color=Color.red()
                    )

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while adding the admin user.",
                e
            )

    @app_commands.command(name="del", description="Delete an admin user")
    async def del_config(self, interaction: discord.Interaction, admin_user: Optional[discord.Member] = None):
        try:
            if not await self._check_permissions(interaction):
                await interaction.response.send_message(embed=create_error_embed("You don't have permissions to use this command."))
                return

            server_id = interaction.guild.id
            self.db_cursor.execute('''SELECT admin_role_ids FROM config WHERE server_id = ?''', (server_id,))

            data = self.db_cursor.fetchone()

            if data is None:
                embed = discord.Embed(
                    title="No Configuration Found",
                    description="No configuration exists for this server.",
                    color=Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

            admin_users = eval(data[0]) if data[0] else []

            if admin_user:
                if admin_user.id in admin_users:
                    admin_users.remove(admin_user.id)
                    self.db_cursor.execute('''UPDATE config SET admin_role_ids = ? WHERE server_id = ?''', (str(admin_users), server_id))
                    self.db_connection.commit()
                    
                    embed = discord.Embed(
                        title="Admin User Deleted",
                        description=f"Admin user {admin_user.mention} has been successfully removed.",
                        color=Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="User Not an Admin",
                        description=f"{admin_user.mention} is not an admin.",
                        color=Color.red()
                    )
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while deleting the admin user.",
                e
            )

    @app_commands.command(name="clear", description="Clear all admin users and log channel")
    async def clear_config(self, interaction: discord.Interaction):
        try:
            if not await self._check_permissions(interaction):
                await interaction.response.send_message(embed=create_error_embed("You don't have permissions to use this command."))
                return

            server_id = interaction.guild.id
            self.db_cursor.execute('''UPDATE config SET admin_role_ids = ?, log_channel_id = ? WHERE server_id = ?''', ('[]', None, server_id))

            self.db_connection.commit()

            embed = discord.Embed(title="Configuration Cleared", description="All admin users and the log channel have been cleared.", color=Color.green())
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await handle_command_exception(
                interaction,
                self.client,
                self.db_cursor,
                "An error occurred while clearing the configuration.",
                e
            )

async def setup(client):
    if Config(client).status:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Config.__name__}\033[0;0m] loaded : Status [\033[1;32mEnable\033[0;0m]")
        await client.add_cog(Config(client))
    else:  
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Config.__name__}\033[0;0m] loaded : Status [\033[1;31mUnable\033[0;0m]")