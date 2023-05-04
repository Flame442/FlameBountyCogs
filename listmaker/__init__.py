from .listmaker import ListMaker

async def setup(bot):
	await bot.add_cog(ListMaker(bot))
