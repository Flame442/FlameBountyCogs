import discord
from redbot.core import commands
import random


class LoveCalc(commands.Cog):
	"""Calculate the love between two people."""
	def __init__(self, bot):
		self.bot = bot
	
	@commands.command()
	async def lovecalc(self, ctx, p1: discord.Member, p2: discord.Member=None):
		"""
		Calculate the love between two people.
		
		If only one person is provided, the invoker will be used.
		"""
		if p2 is None:
			p2 = ctx.author
		state = random.getstate()
		new_seed = str(p1.id + p2.id)
		random.seed(new_seed)
		love = random.randint(0, 101)
		random.setstate(state)
		love_dict = {
			0: '\N{BROKEN HEART}',
			1: '\N{HEAVY BLACK HEART}',
			2: '\N{SPARKLING HEART}',
			3: '\N{HEART WITH RIBBON}',
			4: '\N{GROWING HEART}\N{GROWING HEART}\N{GROWING HEART}'
		}
		await ctx.send(
			f'{love_dict[love//25]} **{p1.display_name}** and **{p2.display_name}** '
			f'are {love}% compatible! {love_dict[love//25]}'
		)
