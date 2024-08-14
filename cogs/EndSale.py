import discord
from discord import app_commands
from discord.ext import commands
import json
import os

SALE_CHANNEL = "💎有料プラン-セール中"
DEFAULT_CHANNEL = "💎有料プラン"
SAVE_FILE = "bot_data.json"

class EndSale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sale_end", description="チャンネルの権限を強制的に元に戻し、チャンネル２に追加します")
    @app_commands.describe(
        target="権限を変更する対象（ユーザーまたはロール）"
    )
    @commands.has_permissions(administrator=True)
    @commands.has_any_role('管理者', 'Discord対応')
    async def end_sale(self, interaction: discord.Interaction, target: discord.Member | discord.Role):
        await interaction.response.defer(ephemeral=True)

        try:
            channel1 = discord.utils.get(interaction.guild.channels, name=SALE_CHANNEL)
            channel2 = discord.utils.get(interaction.guild.channels, name=DEFAULT_CHANNEL)

            if not channel1 or not channel2:
                await interaction.followup.send("指定されたチャンネルが見つかりません。", ephemeral=True)
                return

            affected_members = []

            if isinstance(target, discord.Member):
                await self.reset_member_permissions(target, channel1, channel2)
                affected_members.append(target)
                await self.remove_sale_data(target)
            elif isinstance(target, discord.Role):
                for member in interaction.guild.members:
                    if target in member.roles:
                        await self.reset_member_permissions(member, channel1, channel2)
                        affected_members.append(member)
                        await self.remove_sale_data(member)

            if affected_members:
                await interaction.followup.send(
                    f"{target.mention}" + (f"のメンバー{len(affected_members)}人" if isinstance(target, discord.Role) else "") +
                    f"のチャンネル権限を元に戻し、チャンネル２に追加しました。", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(f"{target.mention}の権限は変更されていませんでした。", ephemeral=True)

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            await interaction.followup.send("コマンドの実行中にエラーが発生しました。", ephemeral=True)

    async def reset_member_permissions(self, member: discord.Member, channel1: discord.TextChannel, channel2: discord.TextChannel):
        # チャンネル1の権限を削除
        await channel1.set_permissions(member, overwrite=None)
        
        # チャンネル2に追加（権限を付与）
        await channel2.set_permissions(member, read_messages=True, send_messages=False)
        
        # チャンネル2のメンバーリストに追加
        if isinstance(channel2, discord.TextChannel):
            try:
                await channel2.edit(overwrites={
                    **channel2.overwrites,
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=False)
                })
            except discord.errors.Forbidden:
                print(f"チャンネル2 ({channel2.name}) にメンバー {member.name} を追加する権限がありません。")

    async def remove_sale_data(self, member: discord.Member):
        sale_time = self.load_sale_time()
        if member.guild.id in sale_time and member.id in sale_time[member.guild.id]:
            del sale_time[member.guild.id][member.id]
            self.save_sale_time(sale_time)
            print(f"{member.name}のセールデータを削除しました。")

    def load_sale_time(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): {int(uk): uv for uk, uv in v.items()} for k, v in data.items() if k != 'default_duration'}
        return {}

    def save_sale_time(self, sale_time):
        data = {}
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
        
        sale_time_data = {str(k): {str(uk): uv for uk, uv in v.items()} for k, v in sale_time.items()}
        data.update(sale_time_data)
        
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)

async def setup(bot):
    await bot.add_cog(EndSale(bot))