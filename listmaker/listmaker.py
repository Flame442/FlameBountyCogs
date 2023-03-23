import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core.utils.chat_formatting import pagify
from tabulate import tabulate
import datetime


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
		
	@listmaker.command(require_var_positional=True)
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
				'data': [],
				#BELOW ARE NOT GUARANTEED TO BE IN A LIST
				'roles': [],
				'sort': None,
				'header': '',
				'last_update': self._date_formatted()
			}
		await ctx.send(f'List `{list_name}` created.')
		
	@listmaker.command(require_var_positional=True)
	async def add(self, ctx, list_name, *values):
		"""
		Add a row of data to a list.
		
		Specify the list name first and the data for each column after.
		Wrap anything that requires spaces in quotes.
		Multiple rows can be added at once by continuing to specify rows.
		
		Example:
		`[p]listmaker add "My friends" "Robert Smith" 26`
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if not self._user_can_access(lists[list_name], ctx.author):
				await ctx.send('You do not have permission to edit that list.')
				return
			req_len = len(lists[list_name]['columns'])
			if len(values) % req_len != 0:
				await ctx.send('The number of columns provided does not match the number of columns in the list.')
				return
			while values:	
				lists[list_name]['data'].append(values[:req_len])
				values = values[req_len:]
			lists[list_name]['last_update'] = self._date_formatted()
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
			if not self._user_can_access(lists[list_name], ctx.author):
				await ctx.send('You do not have permission to edit that list.')
				return
			if row_number <= 0:
				await ctx.send('The row number must be greater than 0.')
				return
			if row_number > len(lists[list_name]['data']):
				await ctx.send('The row number cannot be greater than the number of rows.')
				return
			del lists[list_name]['data'][row_number - 1]
			lists[list_name]['last_update'] = self._date_formatted()
		await ctx.send('Data removed.')
	
	@listmaker.command()
	async def show(self, ctx, list_name, show_index: bool=False):
		"""
		View the data of a list.
		
		Wrap the list name in quotes if it requires spaces.
		Use the parameter `show_index` to enable list indexes.
		
		Example:
		`[p]listmaker show "My friends"`
		"""
		lists = await self.config.lists()
		if list_name not in lists:
			await ctx.send('That list does not exist.')
			return
		if show_index:
			show_index = range(1, len(lists[list_name]['data']) + 1)
		data = lists[list_name]['data']
		if lists[list_name].get('sort', None):
			sort = lists[list_name]['sort']
			if show_index:
				#Sorts both lists by "data"
				data, show_index = zip(*sorted(zip(data, show_index), key=lambda a: a[0][sort[0]], reverse=sort[1]))
			else:
				data = sorted(data, key=lambda a: a[sort[0]], reverse=sort[1])
		msg = tabulate(data, headers=lists[list_name]['columns'], showindex=show_index)
		header = lists[list_name].get('header', '')
		header = header.replace('{date}', lists[list_name].get('last_update', '(Unknown date)'))
		msg = header + '\n' + msg
		paged = pagify(msg)
		box_paged = (f'```\n{x}```' for x in paged)
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
	async def list(self, ctx, show_all: bool=False):
		"""
		List the existing listmaker lists.
		
		Also shows the user id of the author of each list.
		Use the parameter `show_all` to see all lists.
		"""
		lists = await self.config.lists()
		if not lists:
			await ctx.send('There are currently no lists.')
			return
		data = [
			[name, lists[name]['author']] for name in lists
			if lists[name]['author'] == ctx.author.id or show_all
		]
		msg = tabulate(data, headers=['List Name', 'Author ID'])
		paged = pagify(msg)
		box_paged = (f'```{x}```' for x in paged)
		await ctx.send_interactive(box_paged)

	@listmaker.command()
	async def role(self, ctx, list_name, role_id: int):
		"""
		Toggle if a role_id should be allowed to edit a list.
		
		Wrap the list name in quotes if it requires spaces.
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if lists[list_name]['author'] != ctx.author.id:
				await ctx.send('You do not own that list.')
				return
			if 'roles' not in lists[list_name]:
				lists[list_name]['roles'] = [role_id]
				await ctx.send('Added.')
				return
			if role_id in lists[list_name]['roles']:
				lists[list_name]['roles'].remove(role_id)
				await ctx.send('Removed.')
				return
			lists[list_name]['roles'].append(role_id)
		await ctx.send('Added.')

	@listmaker.command()
	async def sort(self, ctx, list_name, column_name=None, reverse: bool=False):
		"""
		Set the list to be sorted by a particular column.
		
		Wrap anything that requires spaces in quotes.
		Use the parameter `reverse` to sort the other way.
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if not self._user_can_access(lists[list_name], ctx.author):
				await ctx.send('You do not have permission to edit that list.')
				return
			if column_name is None:
				lists[list_name]['sort'] = None
				await ctx.send('Sorting disabled.')
				return
			if column_name not in lists[list_name]['columns']:
				await ctx.send('That column could not be found.')
				return
			idx = lists[list_name]['columns'].index(column_name)
			lists[list_name]['sort'] = [idx, reverse]
		await ctx.send(f'The list will now be sorted by column {column_name}.')
			
	@listmaker.command()
	async def header(self, ctx, list_name, text=None):
		"""
		Set the text to be used as a header for a list.
		
		Wrap anything that requires spaces in quotes.
		The text `{date}` will be replaced by the date the list was last updated.
		"""
		async with self.config.lists() as lists:
			if list_name not in lists:
				await ctx.send('That list does not exist.')
				return
			if not self._user_can_access(lists[list_name], ctx.author):
				await ctx.send('You do not have permission to edit that list.')
				return
			if text is None:
				lists[list_name]['header'] = ''
				await ctx.send('Removed the header.')
				return
			lists[list_name]['header'] = text
		await ctx.send(f'The list will now have the header {text}.')

	@staticmethod
	def _user_can_access(lm_list, user):
		"""Determine if a user can edit a list."""
		if lm_list['author'] == user.id:
			return True
		list_roles = lm_list.get('roles', [])
		user_roles = (r.id for r in getattr(user, 'roles', []))
		if any(rid in list_roles for rid in user_roles):
			return True
		return False
	
	@staticmethod
	def _date_formatted():
		"""Returns the current date formatted as YYY-MM-DD"""
		return datetime.datetime.now().strftime('%Y-%m-%d')
