from .lovecalc import LoveCalc

async def setup(bot):
	bot.add_cog(LoveCalc(bot))
