import discord
from redbot.core import commands
from redbot.core import Config


class TellMe(commands.Cog):
	"""Create custom commands with DMs and server messages."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_guild(
			commands = {}
		)
	
	@commands.guild_only()
	@commands.group(invoke_without_command=True)
	async def tellme(self, ctx, command_name):
		"""Run a command."""
		commands = await self.config.guild(ctx.guild).commands()
		if command_name not in commands:
			return await ctx.send_help()
		data = commands[command_name]
		if data['server']:
			await ctx.send(data['server'])
		if data['dm']:
			try:
				await ctx.author.send(data['dm'])
			except discord.errors.Forbidden:
				await ctx.send('I couldn\'t DM you. Make sure I am not blocked and that you allow DMs from server members.')
	
	@tellme.command()
	async def list(self, ctx):
		"""List commands created with tellme."""
		commands = await self.config.guild(ctx.guild).commands()
		if not commands:
			return await ctx.send('There are not any commands in this server.')
		msg = '\n'.join(commands)
		await ctx.send(f'Commands:```\n{msg}```')
	
	@commands.has_permissions(administrator=True)
	@tellme.command()
	async def create(self, ctx, command_name: str):
		"""Create a new command."""
		if command_name in ('dm', 'server', 'create', 'delete'):
			await ctx.send('That command name cannot be used.')
		async with self.config.guild(ctx.guild).commands() as commands:
			if command_name in commands:
				return await ctx.send('That command already exists.')
			commands[command_name] = {'server': None, 'dm': None}
		await ctx.send(
			f'`{command_name}` added.\n'
			f'Set what it will do with `{ctx.prefix}tellme dm {command_name} <text>` '
			f'and `{ctx.prefix}tellme server {command_name} <text>`.'
		)
	
	@commands.has_permissions(administrator=True)
	@tellme.command()
	async def delete(self, ctx, command_name: str):
		"""Delete a command."""
		async with self.config.guild(ctx.guild).commands() as commands:
			if command_name not in commands:
				return await ctx.send('That command does not exist.')
			del commands[command_name]
		await ctx.send(f'`{command_name}` removed.')
	
	@commands.has_permissions(administrator=True)
	@tellme.command()
	async def dm(self, ctx, command_name, *, text=None):
		"""
		Set the message to be sent in dms.
		
		If nothing is passed, it will remove the dm message.
		"""
		async with self.config.guild(ctx.guild).commands() as commands:
			if command_name not in commands:
				return await ctx.send('That command does not exist.')
			commands[command_name]['dm'] = text
		if text:
			return await ctx.send('Text set.')
		await ctx.send('Text removed.')
	
	@commands.has_permissions(administrator=True)
	@tellme.command()
	async def server(self, ctx, command_name, *, text=None):
		"""
		Set the message to be sent in the server.
		
		If nothing is passed, it will remove the server message.
		"""
		async with self.config.guild(ctx.guild).commands() as commands:
			if command_name not in commands:
				return await ctx.send('That command does not exist.')
			commands[command_name]['server'] = text
		if text:
			return await ctx.send('Text set.')
		await ctx.send('Text removed.')
