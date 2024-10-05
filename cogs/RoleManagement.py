import discord
from discord import app_commands
from discord.ext import commands

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_role_change(self, interaction: discord.Interaction, role: discord.Role, members: str, add_role: bool):
        top_role_name = role.name + "-TOP"
        top_role = discord.utils.get(interaction.guild.roles, name=top_role_name)
        role_member = discord.utils.get(interaction.guild.roles, name=role.name)

        is_role_member = role in interaction.user.roles             # 実行者がロールを持っているか
        is_game_role = top_role in interaction.guild.roles          # ゲーム内役職用のロールか(TOPロールの場合は-TOP-TOPとなるため除外される)
        is_admin = interaction.user.guild_permissions.manage_roles  # ロール管理権限を持っているか

        if (not is_role_member or not is_game_role) and not is_admin:
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
            return

        member_list = []
        for member_mention in members.split():
            try:
                member_id = int(member_mention.strip('<@!>'))
                member = await interaction.guild.fetch_member(member_id)
                if member:
                    member_list.append(member)
            except ValueError:
                continue

        if not member_list:
            await interaction.response.send_message("有効なメンバーが指定されていません。", ephemeral=True)
            return

        processed_members = []
        for member in member_list:
            if add_role and role not in member.roles:
                await member.add_roles(role)
                processed_members.append(member.mention)
            elif not add_role and role in member.roles:
                await member.remove_roles(role)
                processed_members.append(member.mention)

        action = "付与" if add_role else "削除"
        if processed_members:
            result = f"{role.mention} ロールを{action}しました\n> {action}されたメンバー：" + " ".join(processed_members)
        else:
            result = f"指定されたメンバーは既にロールが{action}されています"

        await interaction.response.send_message(result)

    @app_commands.command(name="addrole", description="対象にロールを追加します")
    @app_commands.describe(
        role="付与するロール",
        members="ロールを付与する対象（スペース区切りでメンションを入力）"
    )
    async def addrole(self, interaction: discord.Interaction, role: discord.Role, members: str):
        await self.process_role_change(interaction, role, members, add_role=True)

    @app_commands.command(name="removerole", description="対象からロールを削除します")
    @app_commands.describe(
        role="削除するロール",
        members="ロールを削除する対象（スペース区切りでメンションを入力）"
    )
    async def removerole(self, interaction: discord.Interaction, role: discord.Role, members: str):
        await self.process_role_change(interaction, role, members, add_role=False)

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))