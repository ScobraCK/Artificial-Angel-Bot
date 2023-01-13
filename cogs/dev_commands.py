# https://replit.com/@ArihanthChiruvo/keepalivepy?v=1#cogs/cog_example.py
# First test of cogs

import discord
from discord.ext import commands
from load_env import MY_GUILD
from typing import Optional, Literal

def convert_cog_string(cog: str):
	if not cog.startswith('cogs.'):
		cog = 'cogs.' + cog
	return cog

class DevCommands(commands.Cog, name='Dev Commands'):
	'''These are the developer commands'''

	def __init__(self, bot):
		self.bot: commands.Bot = bot

	async def cog_check(self, ctx):  
		'''
		The default check for this cog whenever a command is used. Returns True if the command is allowed.
		'''
		return ctx.author.id == self.bot.owner_id

	@commands.command(  # Decorator to declare where a command is.
		name='reload',  # Name of the command, defaults to function name.
		aliases=['rl']  # Aliases for the command.
	)  
	async def reload(self, ctx, cog):
		'''
		Reloads a cog.
		'''
		extensions = self.bot.extensions  # A list of the bot's cogs/extensions.
		if cog == 'all':  # Lets you reload all cogs at once
			count = 0
			for extension in list(extensions):
				count += 1
				await self.bot.reload_extension(extension)
			await ctx.send(f'Reloaded {count}/{len(extensions)} extentions')
		else:
			cog = convert_cog_string(cog)
			if cog in extensions:
				await self.bot.reload_extension(cog)
				await ctx.send('Done')  # Sends a message where content='Done'
			else:
				await ctx.send('Unknown Cog')  # If the cog isn't found/loaded.
	
	@commands.command(name="unload", aliases=['ul']) 
	async def unload(self, ctx, cog):
		'''
		Unload a cog.
		'''
		extensions = self.bot.extensions
		cog = convert_cog_string(cog)
		if cog not in extensions:
			await ctx.send("Cog is not loaded!")
			return
		await self.bot.unload_extension(cog)
		await ctx.send(f"`{cog}` has successfully been unloaded.")
	
	@commands.command(name="load")
	async def load(self, ctx, cog):
		'''
		Loads a cog.
		'''
		cog = convert_cog_string(cog)
		try:
			await self.bot.load_extension(cog)
			await ctx.send(f"`{cog}` has successfully been loaded.")

		except commands.errors.ExtensionNotFound:
			await ctx.send(f"`{cog}` does not exist!")

	@commands.command(name="listcogs", aliases=['lc'])
	async def listcogs(self, ctx):
		'''
		Returns a list of all enabled commands.
		'''
		base_string = "```css\n"  # Gives some styling to the list (on pc side)
		base_string += "\n".join([str(cog) for cog in self.bot.extensions])
		base_string += "\n```"
		await ctx.send(base_string)

	# sync message command copied from @AbstractUmbra's gist post
	@commands.command()
	@commands.guild_only()
	async def sync(
		self,
		ctx: commands.Context, 
		guilds: commands.Greedy[discord.Object], 
		spec: Optional[Literal["~", "*", "^"]] = None) -> None:

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


async def setup(bot):
	await bot.add_cog(DevCommands(bot), guild=MY_GUILD)
