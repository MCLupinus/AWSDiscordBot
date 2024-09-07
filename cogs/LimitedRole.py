import discord
from discord import app_commands
from discord.ext import commands
from .Load import DataJson
import datetime
import pytz

class LimitedRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timelimit", description="特定のユーザーに期限付きロールの設定をします")
    @commands.has_any_role('管理者', 'Discord対応')
    async def time_limit_role(self, interaction: discord.Interaction, option: str, give_role: discord.Role, eligibility: discord.Member | discord.Role, day:int=0, hours: int=0, minutes: int=0):
        # 時間がかかる場合があるため一旦送信する
        await interaction.response.defer(ephemeral=True)

        try:
            data = DataJson.get_data(self, interaction.guild_id)
        except ValueError as e:
            await interaction.followup.send(e, ephemeral=True)
        
        # もし時間指定がなければデフォルトの時間を採用する
        if not day and not hours and not minutes:
            try:
                date = data[str(interaction.guild_id)]["limited_roles_default"][give_role.id]

            except:
                await interaction.followup.send("デフォルトの日付が正しく設定されていません", ephemeral=True)
                return
        else:
            date = [day, hours, minutes]

        utc_now = datetime.datetime.now(pytz.utc)

        # 指定された時間後のUTC時間を計算 (例: 1日後)
        target_time = utc_now + datetime.timedelta(days=date[0], hours=date[1], minutes=date[2])

        # eligibilityがメンバーの場合
        if isinstance(eligibility, discord.Member):
            await eligibility.add_roles(give_role)
            data[str(interaction.guild_id)]["members"][str(eligibility.id)]["count"] += 1
            data[str(interaction.guild_id)]["members"][str(eligibility.id)]["duration"] = target_time
            await interaction.response.send_message(f"{eligibility.mention} に {give_role.mention} を付与しました。{target_time.astimezone(pytz.utc)} まで有効です。")

        # eligibilityがロールの場合
        elif isinstance(eligibility, discord.Role):
            for member in interaction.guild.members:
                if eligibility in member.roles:
                    await member.add_roles(give_role)
                    data[str(interaction.guild_id)]["members"][str(member.id)]["count"] += 1
                    data[str(interaction.guild_id)]["members"][str(member.id)]["duration"] = target_time
            await interaction.response.send_message(f"{eligibility.mention} のメンバー全員に {give_role.mention} を付与しました。{target_time.astimezone(pytz.utc)} まで有効です。")

        DataJson.save_json(self, data)

async def setup(bot):
    await bot.add_cog(LimitedRole(bot))