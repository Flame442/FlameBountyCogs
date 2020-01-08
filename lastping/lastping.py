import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import time


class LastPing(commands.Cog):
	"""View how long servers have lasted without a mass mention."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_guild(
			lastPing = None,
			lastUpdate = None,
			autoUpdateMessage = None
		)
		self.cache = {}

	@commands.command()
	async def lastping(self, ctx):
		"""View how long this server has lasted without a mass mention."""
		now = time.time()
		lastPing = await self.config.guild(ctx.guild).lastPing()
		if lastPing is None:
			await ctx.send('I have never seen a mass mention in this server.')
			return
		delta = now - lastPing
		await ctx.send(self.build_string(delta))
		
	@commands.group(invoke_without_command=True)
	@checks.guildowner()
	async def lastpingauto(self, ctx):
		"""Create an auto updating message that shows how long this server has lasted without a mass mention."""
		data = await self.config.guild(ctx.guild).all()
		if data['autoUpdateMessage']:
			await ctx.send('One already exists.')
			return
		now = time.time()
		if data['lastPing']:
			delta = now - data['lastPing']
			message = await ctx.send(self.build_string(delta))
		else:
			message = await ctx.send('I have never seen a mass mention in this server.')
		await self.config.guild(ctx.guild).lastUpdate.set(now)
		await self.config.guild(ctx.guild).autoUpdateMessage.set([message.channel.id, message.id])
	
	@lastpingauto.command()
	async def remove(self, ctx):
		"""Remove the current auto updating message."""
		await self.config.guild(ctx.guild).autoUpdateMessage.set(None)
		await ctx.send('Done.')
	
	def build_string(self, delta):
		"""Build the string for messages based on a time delta."""
		return f'This server has lasted **{int(delta//86400)}** days without a mass mention.'
	
	async def run_update(self, guild):
		"""Updates the auto update message for a particular guild."""
		now = time.time()
		message_data = self.cache[guild.id]['autoUpdateMessage']
		if not message_data:
			return
		cid, mid = message_data[0], message_data[1]
		channel = guild.get_channel(cid)
		if not channel:
			return
		try:
			message = await channel.fetch_message(mid)
		except Exception:
			return
		lastPing = self.cache[guild.id]['lastPing']
		if not lastPing:
			return
		delta = now - lastPing
		try:
			await message.edit(self.build_string(delta))
		except Exception:
			pass
		self.cache[guild.id]['lastUpdate'] = now
		await self.config.guild(guild).lastUpdate.set(now)

	@commands.Cog.listener()
	async def on_message(self, message):
		# either @everyone or @here is in the message AND it did end up mentioning
		if not message.guild:
			return
		now = time.time()
		if message.guild.id not in self.cache:
			data = await self.config.guild(message.guild).all()
			self.cache[message.guild.id] = {
				'lastPing': data['lastPing'],
				'lastUpdate': data['lastUpdate'],
				'autoUpdateMessage': data['autoUpdateMessage']
			}
		if not message.mention_everyone:
			lu = self.cache[message.guild.id]['lastUpdate']
			if lu and lu // 86400 != now // 86400:
				self.run_update(message.guild)
			return
		await self.config.guild(message.guild).lastPing.set(now)
		await self.run_update(message.guild)
