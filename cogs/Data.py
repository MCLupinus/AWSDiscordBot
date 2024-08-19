import discord
from discord import app_commands
from discord.ext import commands
import json
import os

JSON_FILE_NAME = 'config.json'

class DataJson(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # jsonデータを読み込み。見つからなければ作成
    def load_or_create_json(self):
        data = {}
        if not os.path.exists(JSON_FILE_NAME):
            print(f"{JSON_FILE_NAME}を作成します...")
            data = {
                str(guild.id): {
                } for guild in self.bot.guilds
                }
            self.save_json(data)
        else:
            with open(JSON_FILE_NAME, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"既存の{JSON_FILE_NAME}を読み込みました。")

        return data

    # Jsonを保存
    def save_json(self, data):
        with open(JSON_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"{JSON_FILE_NAME}を保存しました。")

    # BOT起動時にチェック
    @commands.Cog.listener()
    async def on_ready(self):
        self.load_or_create_json()

    # BOTが新しいサーバーに参加した時にJsonに追加
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        data = self.load_or_create_json()
        if str(guild.id) not in data:
            data[str(guild.id)] = {
            }
            self.save_json(data)
        print(f"{guild.name} (ID: {guild.id}) のデータを{JSON_FILE_NAME}に追加しました。")

async def setup(bot):
    await bot.add_cog(DataJson(bot))