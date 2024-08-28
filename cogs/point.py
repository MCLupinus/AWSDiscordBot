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
        
        await interaction.response.send_message(f"{member.mention}に{point}ポイント追加しました\n現在{data[str(interaction.guild_id)]["members"][str(member.id)]["point"]}ポイント", ephemeral=True)

    @app_commands.command(name="result", description="全ユーザーのポイントを表示します")
    @commands.has_any_role('管理者', 'Discord対応')
    async def result(self, interaction: discord.Interaction):
        data = DataJson.load_or_create_json(self)
        if not str(interaction.guild_id) in data:
            await interaction.response.send_message("このサーバーのデータが見つかりませんでした\n`/reload`を試してください", ephemeral=True)
            return
        
        members_point = []

        try:
            for member in interaction.guild.members:
                point = data[str(interaction.guild_id)]["members"][str(member.id)]["point"]
                members_point.append({"point": point, "mention": member.mention})

        except:
            await interaction.response.send_message("データを取得できませんでした", ephemeral=True)
            return
        
        members_point = sorted(members_point, key=lambda p: p["point"], reverse=True)

        log = "## ポイントが高い順にメンバーを表示します\n"

        for i in range(len(members_point)):
            if members_point[i]["point"] == 0:
                break

            log += f"{i+1}位：{members_point[i]["mention"]} 獲得ポイント：{members_point[i]["point"]}\n"

        await interaction.response.send_message(log)

async def setup(bot):
    await bot.add_cog(Points(bot))