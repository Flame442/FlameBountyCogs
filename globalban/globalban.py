import discord
from redbot.core import commands
from redbot.core.utils.mod import get_audit_reason


class GlobalBan(commands.Cog):
    """Global bans."""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.is_owner()
    @commands.command()
    async def globalban(self, ctx, uid: int, reason: str=None):
        """Globally ban a user."""
        no_perms = 0
        higher_role = 0
        other_fail = 0
        success = 0
        reason = get_audit_reason(ctx.author, reason, shorten=True)
        try:
            user = await self.bot.fetch_user(uid)
        except discord.HTTPException:
            await ctx.send("User not found.")
            return
        for guild in self.bot.guilds:
            if not guild.me.guild_permissions.ban_members:
                no_perms += 1
                continue
            member = guild.get_member(uid)
            if member is not None and member.top_role >= guild.me.top_role:
                higher_role += 1
                continue
            try:
                await guild.ban(user, reason=reason)
            except discord.HTTPException:
                other_fail += 1
            else:
                success += 1
        msg = ""
        if success:
            msg += f"Successfully banned the user in **{success}** guilds.\n"
        if no_perms:
            msg += f"I do not have ban perms in **{no_perms}** guilds.\n"
        if higher_role:
            msg += f"The user has a higher role than me in **{higher_role}** guilds.\n"
        if other_fail:
            msg += f"An unknown exception occured in **{other_fail}** guilds.\n"
        if not msg:
            await ctx.send("Couldn't find any guilds? This should not happen...")
            return
        await ctx.send(msg)
    
    @commands.is_owner()
    @commands.command()
    async def globalunban(self, ctx, uid: int, reason: str=None):
        """Globally unban a user."""
        no_perms = 0
        not_banned = 0
        other_fail = 0
        success = 0
        reason = get_audit_reason(ctx.author, reason, shorten=True)
        for guild in self.bot.guilds:
            if not guild.me.guild_permissions.ban_members:
                no_perms += 1
                continue
            try:
                ban_entry = await guild.fetch_ban(discord.Object(uid))
            except discord.NotFound:
                not_banned += 1
                continue
            except discord.HTTPException:
                other_fail += 1
                continue
            try:
                await guild.unban(ban_entry.user, reason=reason)
            except discord.HTTPException:
                other_fail += 1
            else:
                success += 1
        msg = ""
        if success:
            msg += f"Successfully unbanned the user in **{success}** guilds.\n"
        if no_perms:
            msg += f"I do not have ban perms in **{no_perms}** guilds.\n"
        if not_banned:
            msg += f"The user was not banned in **{not_banned}** guilds.\n"
        if other_fail:
            msg += f"An unknown exception occured in **{other_fail}** guilds.\n"
        if not msg:
            await ctx.send("Couldn't find any guilds? This should not happen...")
            return
        await ctx.send(msg)
