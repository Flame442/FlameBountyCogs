from .globalban import GlobalBan

async def setup(bot):
	await bot.add_cog(GlobalBan(bot))