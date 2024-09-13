import discord
from utils.embeds import create_error_embed
from db.database import get_log_channel_id

async def handle_command_exception(interaction: discord.Interaction, client: discord.Client, db_cursor, error_message: str, exception: Exception):
    log_channel_id = None
    response = ""
    
    try:
        server_id = interaction.guild.id
        log_channel_id = get_log_channel_id(server_id) 
        response = log_channel_id
        
        if log_channel_id is None:
            embed = create_error_embed("No configuration found for this server. Use /help config for more information.")
            await interaction.response.send_message(embed=embed)
            return

        embed = create_error_embed(f"An error occurred: {error_message} - {exception}")
        log_channel = client.get_channel(int(log_channel_id))

        if log_channel:
            await log_channel.send(embed=embed)
        else:
            embed = create_error_embed("Log channel not found, please set it using /config set log_channel_id <channel_id>.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    except Exception as e:
        print(e)
        print(f"log_channel_id {log_channel_id}, {response}")
        
        embed = create_error_embed("An error occurred while handling the exception. Please try again later.")
        embed_log = create_error_embed(f"Logs: An error occurred while handling the exception. {e}")
        await client.get_channel(int(log_channel_id)).send(embed=embed_log)
        await interaction.response.send_message(embed=embed, ephemeral=True)