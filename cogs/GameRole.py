import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")

import discord
from discord import app_commands
from discord.ext import commands

GAME_ROLE_MIN_NAME = "#game_role_min"
GAME_ROLE_MAX_NAME = "#game_role_max"
DEBUG = "debug"

class GameRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_role_change(self, interaction: discord.Interaction, role: discord.Role, members: str, add_role: bool):
        min_priority = discord.utils.get(interaction.guild.roles, name=GAME_ROLE_MIN_NAME)
        max_priority = discord.utils.get(interaction.guild.roles, name=GAME_ROLE_MAX_NAME)
        debug = discord.utils.get(interaction.guild.roles, name=DEBUG)

        is_game_role = min_priority.position < role.position < max_priority.position

        is_role_member = role in interaction.user.roles             # 実行者がロールを持っているか
        is_admin = False
        if not debug in interaction.user.roles: # デバッグが有効の場合調べない
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
    await bot.add_cog(GameRole(bot))