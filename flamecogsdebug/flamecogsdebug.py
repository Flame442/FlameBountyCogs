import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
import traceback

COGS = (
'Battleship', 'Blinder', 'Deepfry', 'DynamicChannelList', 'GameRoles',
'GiftAway', 'Hangman', 'Hider', 'LastPing', 'ListMaker', 'LoveCalc',
'Monopoly', 'OnlineStats', 'PartyGames', 'Quotes', 'SimpleEmbed',
'Stocks', 'TellMe', 'WordStats',
)


class FlameCogsDebug(commands.Cog):
	"""Debug tools for FlameCogs."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_global(
			postChannel = None
		)
	
	async def is_flame_or_owner(ctx):
		return (await ctx.bot.is_owner(ctx.author)) or ctx.author.id == 145519400223506432
	
	@commands.check(is_flame_or_owner)
	@commands.group()
	async def fcd(self, ctx):
		"""Group command for debugging FlameCogs."""
		pass
	
	@fcd.command()
	async def setchannel(self, ctx, channel: discord.TextChannel):
		"""Set the channel that FlameCogs debug messages are posted to."""
		await self.config.postChannel.set(channel.id)
		await ctx.tick()
	
	@commands.Cog.listener()
	async def on_flamecogs_game_error(self, game, error):
		channel = await self.config.postChannel()
		channel = self.bot.get_channel(channel)
		if not channel:
			return
		stack = ''.join(traceback.TracebackException.from_exception(error).format())
		msg = (
			f'<@!145519400223506432>\n'
			f'```ini\n[Error in a FlameCogs game!]\n'
			f'Game    = {game.__class__.__name__}\n'
			f'Guild   = {game.ctx.guild.name}\n'
			f'Channel = {game.ctx.channel.name}\n```'
			f'```py\n{stack}\n'
		)
		await channel.send(msg[:1997] + '```')
