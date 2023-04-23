from .lovecalc import LoveCalc

async def setup(bot):
	await bot.add_cog(LoveCalc(bot))
