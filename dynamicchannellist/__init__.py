from .dynamicchannellist import DynamicChannelList

def setup(bot):
	bot.add_cog(DynamicChannelList(bot))
