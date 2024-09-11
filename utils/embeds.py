import discord
from discord import Color

def create_embed(title: str, description: str, color: Color = Color.default(), fields: dict = None) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    
    if fields:
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)
    
    return embed

def create_error_embed(description: str) -> discord.Embed:
    return create_embed(title="Error", description=description, color=Color.red())

def create_success_embed(description: str) -> discord.Embed:
    return create_embed(title="Success", description=description, color=Color.green())
