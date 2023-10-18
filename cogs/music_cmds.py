import discord
from discord import app_commands
from discord.ext import commands

import character as chars
from enum import Enum

url = 'https://cdn-mememori.akamaized.net/asset/MementoMori/Raw/MusicPlayer/'

class MusicLanguage(Enum):
    US = 'US'
    JP = 'JP'

# TODO move to common package as this is duplicate
class IdTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> int:
        try:
            id = int(value)
        except ValueError:
            id = chars.find_id_from_name(value)
        return id

class MusicCog(commands.Cog, name = 'Music Cog'):
    '''
    Test implementation of music bot
    '''
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    async def joinvc(self, interaction: discord.Interaction):
        """Joins a voice channel"""
        if (voice := interaction.user.voice):
            await voice.channel.connect()
            await interaction.response.send_message('Connected')
        else:
            await interaction.response.send_message("You must be in a voice channel",
                                                    ephemeral=True)

    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    async def leavevc(self, interaction: discord.Interaction):
        """Leaves a voice channel"""
        voice_client = interaction.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
            await interaction.response.send_message('Disonnected')
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.",
                                                    ephemeral=True)


    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    @app_commands.describe(
        character='The name or id of the character',
        language='EN or JP'
        )
    async def playlament(
         self, 
         interaction: discord.Interaction,
         character: app_commands.Transform[int, IdTransformer],
         language: MusicLanguage):
        '''
        Plays a lament (Test)
        '''
        song = f'CHR_000{character:03}_SONG_{language.value}.mp3'
        music_url = url+song
        voice_client: discord.VoiceClient = interaction.guild.voice_client
        
        if voice_client.is_connected():
            source = discord.FFmpegPCMAudio(music_url, executable="ffmpeg")
            source.read()
            voice_client.play(source, after=None)
            await interaction.response.send_message(f'Playing {song}')
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.",
                                                    ephemeral=True)
            
        
async def setup(bot):
	await bot.add_cog(MusicCog(bot))
        