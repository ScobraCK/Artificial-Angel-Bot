# https://replit.com/@ArihanthChiruvo/keepalivepy?v=1#cogs/cog_example.py
# First test of cogs

import discord
from discord.ext import commands
from load_env import MY_GUILD, LOG_CHANNEL
from typing import Optional, Literal
from guilddb import update_rankings
from timezones import get_cur_time

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

	@commands.command(aliases=['rl'])
	@commands.guild_only()
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
	
	@commands.command(aliases=['ul'])
	@commands.guild_only()
	async def unload(self, ctx, cog):
		'''
		Unload a cog.
		'''
		extensions = self.bot.extensions
		
		if cog == 'all':  # Lets you reload all cogs at once
			count = 0
			length = len(extensions)-1
			for extension in list(extensions):
				print(extension)
				if extension == 'cogs.dev_cmds':
					continue
				count += 1
				await self.bot.unload_extension(extension)
			await ctx.send(f'Unloaded {count}/{length} extentions')
			return

		cog = convert_cog_string(cog)
		if cog.lower() == 'cogs.dev_cmds': # don't unload the dev commands accidently
			return
		elif cog not in extensions:
			await ctx.send("Cog is not loaded!")
			return
		
		await self.bot.unload_extension(cog)
		await ctx.send(f"`{cog}` has successfully been unloaded.")
	
	@commands.command()
	@commands.guild_only()
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

	@commands.command()
	@commands.guild_only()
	async def reload_data(
		self,
		ctx: commands.Context):
		'''
		Reloads all master data
		'''
		self.bot.masterdata.reload_all()
		await ctx.send(f"Reloaded all data")

	@commands.command()
	@commands.guild_only()
	async def update_group(
		self,
		ctx: commands.Context):
		'''
		Updates world groups
		'''
		group_iter = self.bot.masterdata.get_MB_iter('WorldGroupMB')
		try:
			self.bot.gdb.update_group(group_iter)
			await ctx.send(f"Updated world groups")
		except Exception as e:
			await ctx.send(f"Failed to update: {e}")

	@commands.command()
	@commands.guild_only()
	async def update_ranking(
		self,
		ctx: commands.Context):
		'''
		Updates guild rankings
		'''
		ch = self.bot.get_channel(LOG_CHANNEL)
		msg = get_cur_time() + '\n'
		msg += update_rankings(self.bot.gdb) 
		embed = discord.Embed(description=msg)

		await ch.send(embed=embed)

	@commands.command()
	@commands.guild_only()
	async def force_leave_vc(self, ctx: commands.Context):
		'''
		Force leaves bot from all VC
		'''
		clients = self.bot.voice_clients
		for client in clients:
			await client.disconnect()


async def setup(bot):
	await bot.add_cog(DevCommands(bot), guild=MY_GUILD)