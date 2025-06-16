from typing import Literal, Optional

from discord import Object, HTTPException
from discord.ext import commands

from aabot.main import AABot

def convert_cog_string(cog: str):
	if not cog.startswith('aabot.cogs.'):
		cog = 'aabot.cogs.' + cog
	return cog

class CogCommands(commands.Cog, name='Cog Commands'):
	'''These are the developer ctx commands to handle other cogs'''

	def __init__(self, bot: AABot):
		self.bot = bot

	async def cog_check(self, ctx):  
		'''
		The default check for this cog whenever a command is used. Returns True if the command is allowed.
		'''
		return ctx.author.id == self.bot.owner_id

	@commands.command(aliases=['rl'])
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
				if extension == 'cogs.admin_ctx' or extension == 'cogs.timer':
					continue
				count += 1
				await self.bot.unload_extension(extension)
			await ctx.send(f'Unloaded {count}/{length} extentions')
			return

		cog = convert_cog_string(cog)
		if cog.lower() == 'cogs.admin_ctx': # don't unload the dev commands accidently
			return
		elif cog not in extensions:
			await ctx.send("Cog is not loaded!")
			return
		
		await self.bot.unload_extension(cog)
		await ctx.send(f"`{cog}` has successfully been unloaded.")
	
	@commands.command()
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
	async def sync(
		self,
		ctx: commands.Context, 
		guilds: commands.Greedy[Object], 
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
			except HTTPException:
				pass
			else:
				ret += 1

		await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

async def setup(bot: AABot):
	await bot.add_cog(CogCommands(bot))