import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import pagify
from typing import Union, Optional


class DynamicChannelList(commands.Cog):
	"""Create dynamically updating channel lists."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_guild(
			ignoredCategories = [],
			ignoredChannels = [],
			header = '',
			color = 15158332,
			toUpdate = []
		)
	
	@checks.mod_or_permissions(manage_channels=True)
	@commands.bot_has_permissions(embed_links=True)
	@commands.group(aliases=['dcl'])
	async def dynamicchannellist(self, ctx):
		"""Group command for DynamicChannelList."""
		pass
	
	@dynamicchannellist.command()
	async def generate(self, ctx, channel: Optional[discord.TextChannel]=None, ignoreBlacklist: Optional[bool]=False, role: Optional[discord.Role]=None):
		"""Generate a one-time channel list."""
		if not channel:
			channel = ctx.channel
		embed_list = await self.build_embed(ctx.guild, ignoreBlacklist=ignoreBlacklist, role=role)
		try:
			for embed in embed_list:
				await channel.send(embed=embed)
		except discord.errors.Forbidden:
			await ctx.send('I cannot send messages to that channel.')
	
	@dynamicchannellist.command()
	async def createauto(self, ctx, channel: Optional[discord.TextChannel]=None, ignoreBlacklist: Optional[bool]=False, role: Optional[discord.Role]=None):
		"""Create an automatically updating channel list."""
		if not channel:
			channel = ctx.channel
		embed = await self.build_embed(ctx.guild, ignoreBlacklist=ignoreBlacklist, role=role)
		embed = embed[0]
		try:
			msg = await channel.send(embed=embed)
		except discord.errors.Forbidden:
			await ctx.send('I cannot send messages to that channel.')
		if role:
			role = role.id
		async with self.config.guild(ctx.guild).toUpdate() as toUpdate:
			toUpdate.append({'channel_id': channel.id, 'message_id': msg.id, 'ignoreBlacklist': ignoreBlacklist, 'role_id': role})
	
	@dynamicchannellist.command()
	async def removeauto(self, ctx, message: discord.Message):
		"""
		Remove an automatically updating channel list.
		
		This will not delete the message, only stop it from updating.
		`message` should be a link to the message.
		"""
		value = [message.channel.id, message.id]
		async with self.config.guild(ctx.guild).toUpdate() as toUpdate:
			for value in toUpdate:
				if value['message_id'] == message.id:
					toUpdate.remove(value)
					await ctx.send('Done.')
					return
		await ctx.send('That message is not a dynamic channel list.')
	
	@dynamicchannellist.command()
	async def reloadauto(self, ctx):
		"""Reload all automatically updating channel lists."""
		await self.run_update(ctx.guild)
		await ctx.send('Done.')
	
	@dynamicchannellist.command()
	async def color(self, ctx, color: discord.Color):
		"""Set the color to use for embeds."""
		await self.config.guild(ctx.guild).color.set(color.value)
		await self.run_update(ctx.guild)
		await ctx.send('Color set.')
	
	@dynamicchannellist.command()
	async def header(self, ctx, *, text=None):
		"""Set the header for all embed messages."""
		if text is None:
			text = ''
		await self.config.guild(ctx.guild).header.set(text)
		await self.run_update(ctx.guild)
		await ctx.send('Header set.')
	
	@dynamicchannellist.command(aliases=['categoryignore'])
	async def categoryblacklist(self, ctx, cat: discord.CategoryChannel=None):
		"""
		Toggle if a category is blacklisted from appearing on channel lists.
		
		If no category is provided, the currently blacklisted categories will be listed.
		"""
		async with self.config.guild(ctx.guild).ignoredCategories() as ignoredCategories:
			if cat is None:
				strValues = [str(x) for x in ignoredCategories]
				if strValues:
					return await ctx.send('```\n' + '\n'.join(strValues) + '```')
				return await ctx.send('There are no blacklisted categories.')
			if cat.id in ignoredCategories:
				ignoredCategories.remove(cat.id)
				await ctx.send(f'Category {cat.name} is no longer blacklisted.')
			else:
				ignoredCategories.append(cat.id)
				await ctx.send(f'Category {cat.name} is now blacklisted.')
		await self.run_update(ctx.guild)
				
	@dynamicchannellist.command(aliases=['channelignore'])
	async def channelblacklist(self, ctx, chan: Union[discord.TextChannel, discord.VoiceChannel]=None):
		"""
		Toggle if a channel is blacklisted from appearing on channel lists.
		
		If no channel is provided, the currently blacklisted categories will be listed.
		"""
		async with self.config.guild(ctx.guild).ignoredChannels() as ignoredChannels:
			if chan is None:
				strValues = [str(x) for x in ignoredChannels]
				if strValues:
					return await ctx.send('```\n' + '\n'.join(strValues) + '```')
				return await ctx.send('There are no blacklisted channels.')
			if chan.id in ignoredChannels:
				ignoredChannels.remove(chan.id)
				await ctx.send(f'Channel {chan.name} is no longer blacklisted.')
			else:
				ignoredChannels.append(chan.id)
				await ctx.send(f'Channel {chan.name} is now blacklisted.')
		await self.run_update(ctx.guild)
	
	@staticmethod
	def can_see(role, channel):
		"""Determines if a role can see a channel."""
		#This code *might* fail based on implied perms (admin), not sure.
		overwrite = channel.overwrites_for(role).read_messages
		if overwrite is not None:
			return overwrite
		return role.permissions.read_messages
	
	async def build_embed(self, guild, *, ignoreBlacklist=False, role=None):
		"""Builds a list of embeds with the current settings."""
		msg = ''
		ignoredCategories = await self.config.guild(guild).ignoredCategories()
		ignoredChannels = await self.config.guild(guild).ignoredChannels()
		header = await self.config.guild(guild).header()
		color = await self.config.guild(guild).color()
		color = discord.Color(color)
		for cat, channels in guild.by_category():
			if cat and cat.id in ignoredCategories and not ignoreBlacklist:
				continue
			if cat and role and not self.can_see(role, cat):
				continue
			if cat:
				msg += f'\n**{cat.name.upper()}**\n'
			for chan in channels:
				if chan.id in ignoredChannels and not ignoreBlacklist:
					continue
				if role and not self.can_see(role, chan):
					continue
				msg += f'{chan.mention}'
				if hasattr(chan, 'topic'):
					msg += f' - {chan.topic}'
				msg += '\n'
		msg = msg.strip()
		if header:
			msg = f'{header}\n\n{msg}'
		#split in to chunks
		split = list(pagify(msg, shorten_by=0, page_length=6000))
		return [self.sub_build_embed(m, color) for m in split]
	
	@staticmethod
	def sub_build_embed(msg, color):
		"""Makes the actual embed objects"""
		split = list(pagify(msg, shorten_by=0, page_length=1024))
		desc = split[0]
		if len(split) > 1:
			desc += split[1]
		embed = discord.Embed(
			description=desc,
			color=color
		)
		if len(split) > 2:
			for x in split[2:]:
				embed.add_field(name='\u200B', value=x, inline=False)
		return embed
	
	@commands.Cog.listener()
	async def on_guild_channel_create(self, channel):
		await self.run_update(channel.guild)
	
	@commands.Cog.listener()
	async def on_guild_channel_delete(self, channel):
		await self.run_update(channel.guild)
	
	@commands.Cog.listener()
	async def on_guild_channel_update(self, before, after):
		await self.run_update(after.guild)
	
	@commands.Cog.listener()
	async def on_guild_role_create(self, role):
		await self.run_update(role.guild)
	
	@commands.Cog.listener()
	async def on_guild_role_delete(self, role):
		await self.run_update(role.guild)
	
	@commands.Cog.listener()
	async def on_guild_role_update(self, before, after):
		await self.run_update(after.guild)
	
	async def run_update(self, guild):
		"""Update existing channel lists."""
		main_embed = await self.build_embed(guild)
		main_embed = main_embed[0]
		async with self.config.guild(guild).toUpdate() as toUpdate:
			#begin backwards compatibility
			toRem = []
			toAdd = []
			for value in toUpdate:
				if isinstance(value, list):
					toRem.append(value)
					value = {
						'channel_id': value[0],
						'message_id': value[1],
						'role_id': value[2] if len(value) == 3 else None,
						'ignoreBlacklist': False
					}
					toAdd.append(value)
			if toRem or toAdd:
				for x in toRem:
					toUpdate.remove(x)
				for x in toAdd:
					toUpdate.append(x)
			#end backwards compatibility
			for value in toUpdate:
				if value['role_id']:
					role = guild.get_role(value['role_id'])
					if not role:
						continue
					embed = await self.build_embed(guild, ignoreBlacklist=value['ignoreBlacklist'], role=role)
					embed = embed[0]
				else:
					embed = main_embed
				try:
					msg = await guild.get_channel(value['channel_id']).fetch_message(value['message_id'])
				except Exception:
					continue
				if (
					msg.embeds[0].description != embed.description
					or msg.embeds[0].color != embed.color
					or msg.embeds[0].fields != embed.fields
				):
					try:
						await msg.edit(embed=embed)
					except discord.errors.Forbidden:
						continue
