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
            channel = voice.channel
            if channel.permissions_for(interaction.guild.me).connect:
                if voice_client := interaction.guild.voice_client:
                    await voice_client.move_to(voice.channel)
                    await interaction.response.send_message('Moved Channels')
                else:
                    await voice.channel.connect()
                    await interaction.response.send_message('Connected')
            else:
                await interaction.response.send_message('Bot does not have permission for that channel', ephemeral=True)
        else:
            await interaction.response.send_message("You must be in a voice channel",
                                                    ephemeral=True)

    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    async def leavevc(self, interaction: discord.Interaction):
        """Leaves a voice channel"""
        voice_client: discord.VoiceClient = interaction.guild.voice_client
        if voice_client:
            if voice_client.is_connected():
                await voice_client.disconnect()
                await interaction.response.send_message('Disconnected')
            else:
                voice_client.cleanup()
                await interaction.response.send_message('Disconnected (cleanup)')
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.",
                                                    ephemeral=True)
            
    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    async def stop(self, interaction: discord.Interaction):
        """Stops playing"""
        voice_client: discord.VoiceClient = interaction.guild.voice_client
        if voice_client:
            if voice_client.is_playing():
                voice_client.stop()
                await interaction.response.send_message('Stopped')
            else:
                await interaction.response.send_message('Bot is not playing', ephemeral=True)
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.",
                                                    ephemeral=True)
            
    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    async def pause(self, interaction: discord.Interaction):
        """Pauses playing"""
        voice_client: discord.VoiceClient = interaction.guild.voice_client
        if voice_client:
            if voice_client.is_playing():
                voice_client.pause()
                await interaction.response.send_message('Paused')
            else:
                await interaction.response.send_message('Bot is not playing', ephemeral=True)
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.",
                                                    ephemeral=True)
            
    @app_commands.command()
    @app_commands.checks.bot_has_permissions(connect=True, speak=True)
    async def resume(self, interaction: discord.Interaction):
        """Resumes playing"""
        voice_client: discord.VoiceClient = interaction.guild.voice_client
        if voice_client:
            if voice_client.is_paused():
                voice_client.resume()
                await interaction.response.send_message('Resumed')
            else:
                await interaction.response.send_message('Bot is not paused', ephemeral=True)
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
            if voice_client.is_playing():
                await interaction.response.send_message("The bot is already playing a song. Use /stop to stop playing.", ephemeral=True)
            elif voice_client.is_paused():
                await interaction.response.send_message("The bot is paused while playing. Use /resume or /stop.", ephemeral=True)
            else:
                await interaction.response.defer()                                    
                source = discord.FFmpegPCMAudio(music_url, executable="ffmpeg")
                source.read()
                voice_client.play(source, after=None)
                await interaction.followup.send(f'Playing {song} (Some songs may not exist and currently there are no checks)')
        else:
            await interaction.response.send_message("The bot is not connected to a voice channel.",
                                                    ephemeral=True)
                    
async def setup(bot):
	await bot.add_cog(MusicCog(bot))
        