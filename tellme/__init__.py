from .tellme import TellMe

def setup(bot):
	bot.add_cog(TellMe(bot))
