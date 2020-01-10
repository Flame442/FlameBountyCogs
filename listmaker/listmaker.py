import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.chat_formatting import pagify
from tabulate import tabulate


class ListMaker(commands.Cog):
	"""Make lists to store data."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			lists = {}
		)
		
	@commands.group()
	async def listmaker(self, ctx):
		"""Group command for ListMaker."""
		pass
		
	@listmaker.command()
	async def create(self, ctx, list_name, *column_names):
		"""
		Create a new list.
		
		Specify the list name first and the name of each column after.
		Wrap any names that require spaces in quotes.
		
		Example:
		`[p]listmaker create "My friends" name age`
		"""
		async with self.config.lists() as lists:
			if list_name in lists:
				await ctx.send('That list name is already taken.')
				return
			lists[list_name] = {
				'author': ctx.author.id,
				'columns': column_names,
				'data': []
			}
		await ctx.send(f'List `{list_name}` created.')
		
	@listmaker.command()
	async def add(self, ctx, list_name, *values):
		"""
		Add a row of data to a list.
		
		Specify the list name first and the data for each column after.
		Wrap anything that requires spaces in quotes.
		
		Example:
		`[p]listmaker add "My friends" "Robert Smith" 26`
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if lists[list_name]['author'] != ctx.author.id:
				await ctx.send('You do not own that list.')
				return
			if len(values) != len(lists[list_name]['columns']):
				await ctx.send('The number of columns provided does not match the number of columns in the list.')
				return
			lists[list_name]['data'].append(values)
		await ctx.send('Data added.')
	
	@listmaker.command()
	async def remove(self, ctx, list_name, row_number: int):
		"""
		Remove a row of data from a list.
		
		Specify the list name first and the row number after.
		Wrap the list name in quotes if it requires spaces.
		
		Example:
		`[p]listmaker remove "My friends" 3`
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if lists[list_name]['author'] != ctx.author.id:
				await ctx.send('You do not own that list.')
				return
			if row_number <= 0:
				await ctx.send('The row number must be greater than 0.')
				return
			if row_number > len(lists[list_name]['data']):
				await ctx.send('The row number cannot be greater than the number of rows.')
				return
			del lists[list_name]['data'][row_number - 1]
		
		await ctx.send('Data removed.')
	
	@listmaker.command()
	async def show(self, ctx, list_name):
		"""
		View the data of a list.
		
		Wrap the list name in quotes if it requires spaces.
		
		Example:
		`[p]listmaker show "My friends"`
		"""
		lists = await self.config.lists()
		if list_name not in lists:
			await ctx.send('That list does not exist.')
			return
		data = lists[list_name]['data']
		msg = tabulate(lists[list_name]['data'], headers=lists[list_name]['columns'])
		paged = pagify(msg)
		box_paged = (f'```{x}```' for x in paged)
		await ctx.send_interactive(box_paged)
	
	@listmaker.command()
	async def delete(self, ctx, list_name):
		"""
		Delete a list.
		
		This deletes the list and all of its contents permanently.
		Wrap the list name in quotes if it requires spaces.
		
		Example:
		`[p]listmaker delete "My friends"`
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if lists[list_name]['author'] != ctx.author.id:
				await ctx.send('You do not own that list.')
				return
			del lists[list_name]
		await ctx.send(f'List {list_name} deleted.')
	
	@listmaker.command()
	async def list(self, ctx):
		"""
		List the existing listmaker lists.
		
		Also shows the user id of the author of each list.
		"""
		lists = await self.config.lists()
		if not lists:
			await ctx.send('There are currently no lists.')
			return
		data = [[name, lists[name]['author']] for name in lists]
		msg = tabulate(data, headers=['List Name', 'Author ID'])
		paged = pagify(msg)
		box_paged = (f'```{x}```' for x in paged)
		await ctx.send_interactive(box_paged)
		
