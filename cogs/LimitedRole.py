import discord
from discord import app_commands
from discord.ext import commands
from .Data import DataJson

class LimitedRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timelimit", description="特定のユーザーに期限付きロールの設定をします")
    @commands.has_any_role('管理者', 'Discord対応')
    async def time_limit_role(self, interaction: discord.Interaction, option: str, grant_role: discord.Role, grant_member: discord.Member | discord.Role, day:int=0, hours: int=0, minutes: int=0):
        # 時間がかかる場合があるため一旦送信する
        await interaction.response.defer(ephemeral=True)

        try:
            data = DataJson.get_data(self, interaction.guild_id)
        except ValueError as e:
            await interaction.followup.send(e, ephemeral=True)
        
        # もし時間指定がなければデフォルトの時間を採用する
        if not day and not hours and not minutes:
            try:
                date = data[str(interaction.guild_id)]["limited_roles_default"][grant_role.id]

            except:
                await interaction.followup.send("デフォルトの日付が正しく設定されていません", ephemeral=True)
        else:
            date = [day, hours, minutes]


    def set_time_limit(self, date):
        pass

async def setup(bot):
    await bot.add_cog(LimitedRole(bot))