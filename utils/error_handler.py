import discord
from utils.embeds import create_error_embed
import sqlite3

def get_log_channel(db_cursor, server_id):
    db_cursor.execute('''SELECT log_channel_id FROM config WHERE server_id = ?''', (server_id,))
    return db_cursor.fetchone()

async def handle_command_exception(interaction: discord.Interaction, client: discord.Client, db_cursor: sqlite3.Cursor, error_message: str, exception: Exception):
    server_id = interaction.guild.id
    log_channel_id = get_log_channel(db_cursor, server_id)

    if log_channel_id is None:
        embed = create_error_embed("No configuration found for this server. Use /help config for more information.")
        await interaction.response.send_message(embed=embed)
        return

    embed = create_error_embed(f"An error occurred: {error_message} - {exception}")
    log_channel = client.get_channel(int(log_channel_id[0]))

    if log_channel:
        await log_channel.send(embed=embed)
    else:
        await interaction.response.send_message("Log channel not found, please set it using /config set log_channel_id <channel_id>.", ephemeral=True)
