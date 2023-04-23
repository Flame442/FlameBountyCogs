from .flamecogsdebug import FlameCogsDebug

async def setup(bot):
	await bot.add_cog(FlameCogsDebug(bot))
