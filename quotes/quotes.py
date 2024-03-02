import discord
from discord.ext.commands.converter import MemberConverter
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, close_menu, DEFAULT_CONTROLS
from typing import Union
import asyncio
import random


class CustomMember(commands.Converter):
	"""Wrapper for discord.Member converter with a different error message."""
	async def convert(self, ctx, value):
		try:
			converter = MemberConverter()
			result = await converter.convert(ctx, value)
		except commands.BadArgument:
			raise commands.BadArgument(
				'Syntax error, see example below:\n'
				'`{p}quote add "This is an example quote." @user`'.format(p=ctx.prefix)
			)
		return result


class Quotes(commands.Cog):
	"""Store and display quotes."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_guild(
			next_index = 1,
			quotes = {}
		)
	
	@commands.guild_only()
	@commands.bot_has_permissions(embed_links=True)
	@commands.group(invoke_without_command=True)
	async def quote(self, ctx, quote_id: Union[discord.Member, int, str]=None):
		"""
		View a quote.
		
		Use the optional parameter quote_id to specify a quote to view or to view a random quote from a specific member.
		If no id is provided, a random quote will be sent.
		"""
		quotes = await self.config.guild(ctx.guild).quotes()
		if not quotes:
			return await ctx.send('There are no saved quotes.')
		if isinstance(quote_id, str):
			return await ctx.send('The quote id must be a number or member.')
		if quote_id is None or isinstance(quote_id, discord.Member):
			embed_list = []
			for index in quotes:
				if quote_id is None or quotes[index]['author'] == quote_id.id:
					embed_list.append(await self._build_quote(ctx, quotes[index], index))
			if not embed_list:
				return await ctx.send('That member does not have any quotes.')
			random.shuffle(embed_list)
			c = DEFAULT_CONTROLS if len(embed_list) > 1 else {"\N{CROSS MARK}": close_menu}
			return await menu(ctx, embed_list, c)
		quote_id = str(quote_id)
		if quote_id not in quotes:
			return await ctx.send('That quote could not be found.')
		quote = quotes[quote_id]
		embed = await self._build_quote(ctx, quote, quote_id)
		await ctx.send(embed=embed)
	
	@quote.command()
	async def add(self, ctx, text: str, author: CustomMember):
		"""Add a new quote."""
		index = await self.config.guild(ctx.guild).next_index()
		await self.config.guild(ctx.guild).quotes.set_raw(index, 'text', value=text)
		await self.config.guild(ctx.guild).quotes.set_raw(index, 'author', value=author.id)
		await ctx.send('Quote added as #{0}.'.format(index))
		await self.config.guild(ctx.guild).next_index.set(index + 1)
	
	@checks.mod()
	@quote.command()
	async def delete(self, ctx, quote_id: str):
		"""Delete an existing quote."""
		if not quote_id.isdigit():
			return await ctx.send('The quote id needs to be a number.')
		async with self.config.guild(ctx.guild).quotes() as quotes:
			if quote_id in quotes:
				del quotes[quote_id]
				return await ctx.send('Quote #{0} was deleted successfully.'.format(quote_id))
		await ctx.send('That quote could not be found.')
	
	@quote.command()
	async def all(self, ctx):
		"""Receive a DM with every quote."""
		quotes = await self.config.guild(ctx.guild).quotes()
		msg = ''
		for index in quotes:
			author = ctx.guild.get_member(quotes[index]['author'])
			if author:
				author = author.display_name
			else:
				author = 'Unknown'
			msg += '{index}. "{quote}" -{author}\n'.format(
				index=index, quote=quotes[index]['text'], author=author
			)
		quote_list = pagify(msg)
		await self.member_send_interactive(ctx, quote_list)
	
	async def _build_quote(self, ctx, quote: dict, index: str):
		"""Creates a pretty embed for the quote."""
		embed = discord.Embed(
			title='Quote #{0}'.format(index),
			description='"{0}"'.format(quote["text"]),
			color=await ctx.embed_color()
		)
		author = ctx.guild.get_member(quote['author'])
		if author is not None:
			embed = embed.set_footer(text=author.display_name, icon_url=author.display_avatar.url)
		return embed

	async def member_send_interactive(self, ctx, messages: list):
		"""
		Functionality of ctx.send_interactive but to a discord.Member
		
		Copied & modified from redbot.core.commands.context
		"""
		messages = tuple(messages)
		ret = []
		for idx, page in enumerate(messages, 1):
			msg = await ctx.author.send(page)
			ret.append(msg)
			n_remaining = len(messages) - idx
			if n_remaining > 0:
				if n_remaining == 1:
					plural = ''
					is_are = 'is'
				else:
					plural = 's'
					is_are = 'are'
				query = await ctx.author.send(
					'There {} still {} message{} remaining. '
					'Type `more` to continue.'.format(is_are, n_remaining, plural)
                )
				try:
					resp = await self.bot.wait_for(
						'message',
						check=lambda m: (
							m.author.id == ctx.author.id
							and m.channel == ctx.author.dm_channel
							and m.content.lower() == 'more'
						),
						timeout=15
					)
				except asyncio.TimeoutError:
					await query.delete()
					break
				else:
					try:
						await query.delete()
					except:
						pass
