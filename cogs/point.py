import discord
from discord import app_commands
from discord.ext import commands
from .Data import DataJson

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="point", description="ユーザーにポイントを追加")
    @commands.has_any_role('管理者', 'Discord対応')
    async def point(self, interaction: discord.Interaction, member: discord.Member, point: int):
        # データの取得
        data = DataJson.load_or_create_json(self)
        if not str(interaction.guild_id) in data:
            await interaction.response.send_message("このサーバーのデータが見つかりませんでした\n`/reload`を試してください", ephemeral=True)
            return

        try:
            data[str(interaction.guild_id)]["members"][str(member.id)]["point"] += point
        except:
            await interaction.response.send_message("データが見つかりませんでした", ephemeral=True)

        DataJson.save_json(self, data)
        
        await interaction.response.send_message(f"{point}ポイント追加しました\n現在{data[str(interaction.guild_id)]["members"][str(member.id)]["point"]}ポイント", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Points(bot))