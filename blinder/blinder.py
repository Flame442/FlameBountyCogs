import discord
from redbot.core import commands
from redbot.core import Config
from redbot.core import checks
from redbot.core.utils.chat_formatting import humanize_list


class Blinder(commands.Cog):
	"""Create custom roles that remove certain roles and hide channels from users."""
	def __init__(self, bot):
		self.bot = bot
		self.config = Config.get_conf(self, identifier=145519400223506432)
		self.config.register_guild(
			blinders = {}
		)
		self.config.register_member(
			enabled = [],
			owned_roles = []
		)
	
	@commands.guild_only()
	@commands.group()
	async def blinder(self, ctx):
		"""Group command for blinder."""
		pass
	
	@checks.guildowner()
	@blinder.command()
	async def add(self, ctx, role: discord.Role, remove_roles: commands.Greedy[discord.Role]=[]):
		"""
		Add a role to be managed by blinder.
		
		Specify the role to be managed first.
		Specify any roles that should be removed when this role is applied after.
		Surround each role in quotes if its name requires a space.
		"""
		async with self.config.guild(ctx.guild).blinders() as blinders:
			if str(role.id) in blinders:
				await ctx.send('That role is already managed by blinder.')
				return
			remove_roles = [r.id for r in remove_roles]
			blinders[role.id] = remove_roles
		await ctx.send('Role added.')
	
	@checks.guildowner()
	@blinder.command()
	async def edit(self, ctx, role: discord.Role, remove_roles: commands.Greedy[discord.Role]=[]):
		"""
		Edit what roles are removed by a managed role.
		
		Specify the role to be edited first.
		Specify any roles that should be removed when this role is applied after.
		Surround each role in quotes if its name requires a space.
		"""
		async with self.config.guild(ctx.guild).blinders() as blinders:
			if str(role.id) not in blinders:
				await ctx.send('That role is not managed by blinder.')
				return
			remove_roles = [r.id for r in remove_roles]
			blinders[role.id] = remove_roles
		await ctx.send('Role edited.')
	
	@checks.guildowner()
	@blinder.command()
	async def toggleall(self, ctx, role: discord.Role):
		"""
		Set every role in the guild to be removed when this role is applied.
		
		Surround the role in quotes if its name requires a space.
		"""
		async with self.config.guild(ctx.guild).blinders() as blinders:
			if str(role.id) not in blinders:
				await ctx.send('That role is not managed by blinder.')
				return
			remove_roles = [r.id for r in ctx.guild.roles[1:] if str(r.id) not in blinders]
			blinders[role.id] = remove_roles
		await ctx.send('Role edited.')
	
	@checks.guildowner()
	@blinder.command()
	async def remove(self, ctx, role: discord.Role):
		"""
		Stop a role from being managed by blinder.
		
		Surround the role in quotes if its name requires a space.
		"""
		async with self.config.guild(ctx.guild).blinders() as blinders:
			if str(role.id) not in blinders:
				await ctx.send('That role is not managed by blinder.')
				return
			del blinders[str(role.id)]
		await ctx.send('Role removed.')
	
	@checks.guildowner()
	@blinder.command(name='list')
	async def list_roles(self, ctx):
		"""List the roles currently managed by blinder."""
		blinders = await self.config.guild(ctx.guild).blinders()
		msg = ''
		for role_id in blinders:
			role = ctx.guild.get_role(int(role_id))
			if role is None:
				role = f'<unknown role {role_id}>'
			msg += f'[{role}]\n'
			for rem_role_id in blinders[role_id]:
				role = ctx.guild.get_role(rem_role_id)
				if role is None:
					role = f'<unknown role {rem_role_id}>'
				msg += f'{role}\n'
			msg += '\n'
		if not msg:
			await ctx.send('Blinder is currently not managing any roles.')
			return
		await ctx.send(f'Roles currently managed by blinder:\n```ini\n{msg.rstrip()}```')
	
	@blinder.command()
	async def enable(self, ctx, role: discord.Role):
		"""
		Enable a blinder for yourself.
		
		Surround the role in quotes if its name requires a space.
		"""
		result = await self._enable(ctx.author, role)
		return await ctx.send(result)
		
	@checks.guildowner()
	@blinder.command()
	async def forceenable(self, ctx, member: discord.Member, role: discord.Role):
		"""
		Enable a blinder for a particular member.
		
		Surround the member and role in quotes if their name requires a space.
		"""
		result = await self._enable(member, role)
		return await ctx.send(result)
	
	async def _enable(self, member, role):
		"""Helper method to enable a role for a specific person."""
		if not member.guild.me.guild_permissions.manage_roles:
			return 'I do not have permission to manage roles in this server.'
		blinders = await self.config.guild(member.guild).blinders()
		enabled = await self.config.member(member).enabled()
		if str(role.id) not in blinders:
			return 'That role is not managed by blinder.'
		if role in member.roles:
			return 'That role is already enabled.'
		if role.id in enabled:
			return 'That role is already enabled.'
		if role > member.guild.me.top_role:
			return 'That role is higher than my highest role.'
		await member.add_roles(role, reason='Blinder')
		rem_roles = blinders[str(role.id)]
		to_remove = []
		failed = []
		for r in member.roles:
			if r.id in rem_roles:
				if member.guild.me.top_role > r:
					to_remove.append(r)
				else:
					failed.append(r)
		try:
			await member.remove_roles(*to_remove, reason='Blinder')
		except discord.errors.Forbidden:
			return 'Encountered an unexpected discord.errors.Forbidden removing roles, canceling'
		to_remove = [r.id for r in to_remove]
		async with self.config.member(member).owned_roles() as owned_roles:
			for r in to_remove:
				if r not in owned_roles:
					owned_roles.append(r)
		async with self.config.member(member).enabled() as enabled:
			enabled.append(role.id)
		msg = 'Successfully enabled the role.'
		if failed:
			msg += (
				'\n\nThe following roles could not be managed '
				f'because they are higher than my highest role:\n`{humanize_list(list(failed))}`'
			)
		return msg
	
	@blinder.command()
	async def disable(self, ctx, role: discord.Role):
		"""
		Disable a blinder for yourself.
		
		Surround the role in quotes if its name requires a space.
		"""
		result = await self._disable(ctx.author, role)
		return await ctx.send(result)
	
	@checks.guildowner()
	@blinder.command()
	async def forcedisable(self, ctx, member: discord.Member, role: discord.Role):
		"""
		Disable a blinder for a particular member.
		
		Surround the member and role in quotes if their name requires a space.
		"""
		result = await self._disable(member, role)
		return await ctx.send(result)
	
	async def _disable(self, member, role):
		"""Helper method to disable a role for a specific person."""
		if not member.guild.me.guild_permissions.manage_roles:
			return 'I do not have permission to manage roles in this server.'
		enabled = await self.config.member(member).enabled()
		blinders = await self.config.guild(member.guild).blinders()
		if str(role.id) not in blinders:
			return 'That role is not managed by blinder.'
		if role not in member.roles:
			return 'That role is not enabled.'
		if role.id not in enabled:
			return 'That role is not enabled.'
		if role > member.guild.me.top_role:
			return 'That role is higher than my highest role.'
		await member.remove_roles(role, reason='Blinder')
		all_stored = set()
		async with self.config.member(member).enabled() as enabled:
			enabled.remove(role.id)
			for a in enabled:
				for b in blinders[str(a)]:
					all_stored.add(b)
		async with self.config.member(member).owned_roles() as owned_roles:
			add_roles = [r for r in blinders[str(role.id)] if r not in all_stored and r in owned_roles]
			for r in add_roles:
				if r in owned_roles:
					owned_roles.remove(r)
		to_add = []
		failed = []
		for r in member.guild.roles:
			if r.id in add_roles:
				if member.guild.me.top_role > r:
					to_add.append(r)
				else:
					failed.append(r)
		try:
			await member.add_roles(*to_add, reason='Blinder')
		except discord.errors.Forbidden:
			return 'Encountered an unexpected discord.errors.Forbidden adding roles, canceling'
		msg = 'Successfully disabled the role.'
		if failed:
			msg += (
				'\n\nThe following roles could not be managed '
				f'because they are higher than my highest role:\n`{humanize_list(list(failed))}`'
			)
		return msg
