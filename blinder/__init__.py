from .blinder import Blinder

async def setup(bot):
	await bot.add_cog(Blinder(bot))
