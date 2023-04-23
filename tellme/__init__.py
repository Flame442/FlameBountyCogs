from .tellme import TellMe

async def setup(bot):
	await bot.add_cog(TellMe(bot))
