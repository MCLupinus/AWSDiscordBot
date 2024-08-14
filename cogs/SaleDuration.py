import discord
from discord import app_commands
from discord.ext import commands
import json
import os

SAVE_FILE = "bot_data.json"

class DurationSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sale_duration", description="セールのデフォルト期間を設定します")
    @app_commands.describe(duration="デフォルトの期間（時間単位、0.5-720）")
    @commands.has_permissions(administrator=True)
    @commands.has_any_role('管理者', 'Discord対応')
    async def set_default_duration(self, interaction: discord.Interaction, duration: float):
        await interaction.response.defer(ephemeral=True)

        try:
            if duration < 0.5 or duration > 720:
                await interaction.followup.send("時間は0.5時間（約30分）から720時間（30日）の間で指定してください。", ephemeral=True)
                return

            self.save_default_duration(duration)

            await interaction.followup.send(f"デフォルトの期間を{duration}時間に設定しました。", ephemeral=True)

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            await interaction.followup.send("コマンドの実行中にエラーが発生しました。", ephemeral=True)

    def save_default_duration(self, duration):
        data = {}
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
        data['default_duration'] = duration
        # 既存のセール時間データを保持
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)

async def setup(bot):
    await bot.add_cog(DurationSettings(bot))