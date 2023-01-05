import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from typing import Optional, Literal

import aabot_embeds
import common
from master_data import MasterData
import character as chars

# testing guild id's
load_dotenv()
MY_GUILD = discord.Object(id=os.getenv('GUILD_ID'))
STORY_GUILD = discord.Object(id=os.getenv('STORY_ID'))

class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents: discord.Intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.masterdata = MasterData()
    
    async def on_ready(self):
        await self.wait_until_ready()
        print('AA is online')


# testing
class IdTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> int:
        try:
            id = int(value)
        except ValueError:
            id = chars.find_id_from_name(value)
        return id

intents=discord.Intents.default()
intents.message_content = True
bot = MyBot(command_prefix='!', intents=intents)

# sync message command I copied from @AbstractUmbra's gist post
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

@bot.tree.command()
@app_commands.describe(
    character='The name or id of the character'
)
async def character(
    interaction: discord.Interaction,
    character: app_commands.Transform[int, IdTransformer]):  # is an id
    '''Searches a characters info'''
    if not chars.check_id(character):
        await interaction.response.send_message(
            f"A character id of `{character}` does not exist.",
            ephemeral=True
        )
    else:
        embed = aabot_embeds.char_info_embed(character, bot.masterdata)
        await interaction.response.send_message(embed=embed)

@bot.tree.command()
async def idlist(interaction: discord.Interaction):
    '''
    Shows character ids
    '''
    embed = aabot_embeds.id_list_embed()
    await interaction.response.send_message(embed=embed)

@bot.tree.command()
@app_commands.describe(
    character='The name or id of the character'
)
async def skill(
    interaction: discord.Interaction,
    character: app_commands.Transform[int, IdTransformer]):
    '''Shows character skills'''
    if not chars.check_id(character):
        await interaction.response.send_message(
            f"A character id of `{character}` does not exist.",
            ephemeral=True
        )
    else:
        char = chars.get_character_info(character, bot.masterdata)

        embeds = [
            aabot_embeds.skill_embed(char, common.Skill_Enum.ACTIVE, bot.masterdata),
            aabot_embeds.skill_embed(char, common.Skill_Enum.PASSIVE, bot.masterdata),
            aabot_embeds.uw_skill_embed(char, bot.masterdata)
        ]
        user = interaction.user
        view = aabot_embeds.Skill_View(user, embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)
        message = await interaction.original_response()
        view.message = message

@bot.tree.command()
async def awakening(interaction: discord.Interaction):
    '''Awakening cost chart'''
    embed=discord.Embed()
    embed.set_image(url=common.awakening)
    await interaction.response.send_message(
        embed=embed
    )

@bot.tree.command()
async def speed(interaction: discord.Interaction):
    '''List character speeds in decreasing order'''
    text, speed_it = aabot_embeds.speed_text(bot.masterdata)
    embed = discord.Embed(
        title='Character Speeds',
        description=text)
    user = interaction.user
    view = aabot_embeds.Speed_View(user, embed, speed_it)

    await interaction.response.send_message(embed=embed, view=view)
    message = await interaction.original_response()
    view.message = message


bot.run(os.getenv('TOKEN'))
