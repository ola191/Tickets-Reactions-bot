import asyncio
import datetime
from typing import Optional
import discord
from discord.ui import Button, View
from discord.ext import commands
from discord import ButtonStyle, app_commands, Color, TextChannel, Member, Interaction
from utils.embeds import create_error_embed
from utils.error_handler import handle_command_exception
from db.database import add_ticket_category, fetch_admin_role_ids, fetch_config, fetch_ticket_categories, insert_config, update_config, add_admin_role, delete_admin_role

class Config(commands.GroupCog, name="config"):
    def __init__(self, client):
        self.client = client
        self.status = True

    async def _check_permissions(self, interaction: discord.Interaction) -> bool:
        server_id = interaction.guild.id
        user_id = interaction.user.id

        if user_id == interaction.guild.owner_id:
            return True

        admin_role_ids = fetch_admin_role_ids(server_id)
        for role in interaction.user.roles:
            if role.id in admin_role_ids:
                return True

        return False

    @app_commands.command(name="set", description="Set a configuration option for the server")
    async def set_config(self, interaction: Interaction, log_channel: Optional[TextChannel] = None, admin_user: Optional[Member] = None):
        try:
            try:
                server_id = interaction.guild.id
                config_data = fetch_config(server_id)

                if config_data is None:
                    insert_config(server_id, [admin_user.id] if admin_user else [], log_channel.id if log_channel else None)
                    embed = discord.Embed(title="Configuration Set", description="Configuration options have been successfully set.", color=discord.Color.green())
                    await interaction.response.send_message(embed=embed)
                    return

                admin_roles, current_log_channel_id, ticket_categories = config_data

                if admin_user:
                    embed = discord.Embed(
                        title="Confirm Admin Role Replacement",
                        description=f"Are you sure you want to replace all admin users with {admin_user.mention}?",
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
                        admin_roles = [admin_user.id]
                        embed = discord.Embed(
                            title="Admin Roles Updated",
                            description=f"All admin roles have been replaced with {admin_user.mention}.",
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
                        update_config(server_id, admin_roles, current_log_channel_id, None)
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

                update_config(server_id, admin_roles, current_log_channel_id, None)

                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.followup.send(embed=embed)

            except Exception as e:
                await handle_command_exception(interaction, self.client, "An error occurred while setting the configuration.", e)
        except Exception as e:
                print(f"eee {e}")
                
    @app_commands.command(name="view", description="View the current server configuration")
    async def view_config(self, interaction: discord.Interaction):
        config_data = ""
        try:
            if not await self._check_permissions(interaction):
                await interaction.response.send_message(embed=create_error_embed("You don't have permissions to view this configuration."))
                return

            server_id = interaction.guild.id
            config_data = fetch_config(server_id)
            if config_data is None:
                embed = discord.Embed(
                    title="No Configuration Found",
                    description="No configuration exists for this server.",
                    color=discord.Color.from_rgb(100, 150, 255)
                )
                await interaction.response.send_message(embed=embed)
                return

            admin_users_ids, log_channel_id, ticket_categories = config_data
            admin_users_str = ", ".join([f"<@{user_id}>" for user_id in admin_users_ids]) if admin_users_ids else "None"
            
            tickets_categories_str = ", ".join([f"{category}" for category in ticket_categories]) if ticket_categories else "None"
            
            embed = discord.Embed(
                title="Server Configuration",
                color=discord.Color.from_rgb(100, 150, 255)
            )
            embed.add_field(name="Log Channel", value=f"<#{log_channel_id}>" if log_channel_id else "Not set", inline=False)
            embed.add_field(name="Admin Users", value=admin_users_str, inline=False)
            embed.add_field(name="Tickets Categories", value=tickets_categories_str, inline=False)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            print(config_data)
            await handle_command_exception(interaction, self.client, "An error occurred while viewing the configuration.", e)

    @app_commands.command(name="add", description="Add admin and ticket category")
    async def add(self, interaction: Interaction, admin_user: Optional[Member], ticket_category: Optional[str]):
        try:
            if not await self._check_permissions(interaction):
                not_access_embed = create_error_embed("You don't have permissions to add admin roles.")
                await interaction.response.send_message(embed=not_access_embed)
                return

            server_id = interaction.guild.id
            
            if admin_user:
                admin_users = fetch_admin_role_ids(server_id)

                if admin_user.id not in admin_users:
                    admin_users.append(admin_user.id)
                    update_config(server_id, admin_users, None, None)
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Admin User Added",
                        description=f"User {admin_user.mention} has been added to the list of admins.",
                        color=discord.Color.green()
                    ))
                else:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="User Is Already Admin",
                        description=f"User {admin_user.mention} is already an admin.",
                        color=discord.Color.red()
                    ))
                return

            if ticket_category:
                existing_categories = fetch_ticket_categories(server_id)

                discord_category = discord.utils.get(interaction.guild.categories, name=ticket_category)

                if discord_category and discord_category.id not in existing_categories:
                    add_ticket_category(server_id, discord_category.id)
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Ticket Category Added",
                        description=f"Category **{discord_category.name}** has been added to the database.",
                        color=discord.Color.green()
                    ))
                elif not discord_category:
                    new_category = await interaction.guild.create_category(ticket_category)
                    add_ticket_category(server_id, new_category.id)
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Ticket Category Created and Added",
                        description=f"Category **{new_category.name}** has been created and added to the list of categories.",
                        color=discord.Color.green()
                    ))
                else:
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Category Already Exists",
                        description=f"Category **{discord_category.name}** already exists in the database.",
                        color=discord.Color.red()
                    ))
                return

            await interaction.response.send_message(embed=create_error_embed("Please provide a valid user or category to add."))
        except Exception as e:
            await handle_command_exception(interaction, self.client, "An error occurred while adding the admin user or category.", e)
        
    @app_commands.command(name="remove", description="Remove an admin role")
    async def remove_admin_role(self, interaction: Interaction, admin_user: discord.Member, ticket_category: Optional[str] = None):
        try:
            if not await self._check_permissions(interaction):
                await interaction.response.send_message(embed=create_error_embed("You don't have permissions to remove admin roles."))
                return

            server_id = interaction.guild.id
            admin_roles = fetch_admin_role_ids(server_id)

            if admin_user.id in admin_roles:
                admin_roles.remove(admin_user.id)
                update_config(server_id, admin_roles, None)
                await interaction.response.send_message(embed=discord.Embed(
                    title="Admin Role Removed",
                    description=f"Role {admin_user.mention} has been removed from the list of admin roles.",
                    color=discord.Color.green()
                ))
            else:
                await interaction.response.send_message(embed=discord.Embed(
                    title="Role Not Admin",
                    description=f"Role {admin_user.mention} is not an admin role.",
                    color=discord.Color.red()
                ))

        except Exception as e:
            await handle_command_exception(interaction, self.client, "An error occurred while removing the admin role.", e)

async def setup(client):
    if Config(client).status:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Config.__name__}\033[0;0m] loaded : Status [\033[1;32mEnable\033[0;0m]")
        await client.add_cog(Config(client))
    else:
        print(f"[{datetime.datetime.now()}] [\033[1;33mCONSOLE\033[0;0m]: Cog [\033[1;33m{Config.__name__}\033[0;0m] loaded : Status [\033[1;31mUnable\033[0;0m]")
