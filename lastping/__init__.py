from .lastping import LastPing

async def setup(bot):
	await bot.add_cog(LastPing(bot))
