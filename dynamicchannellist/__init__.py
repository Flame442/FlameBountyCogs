from .dynamicchannellist import DynamicChannelList

async def setup(bot):
	await bot.add_cog(DynamicChannelList(bot))
