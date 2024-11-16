import discord
from discord.ext import commands
import os

# メイン
TOKEN = os.getenv("UNGURA_DISCORD_TOKEN")

# 設定
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.voice_states = True

IGNORE_LIST = ["Calculator.py"]

if TOKEN is None:
    raise ValueError("[起動プロセス] Discord BOTトークンが見つかりません")

class UnguraBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="/",
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename in IGNORE_LIST:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"[起動プロセス] {filename}を読み込み")
        # インタラクションをシンクする。ギルドコマンドなので即時反映。
        await bot.tree.sync()

    async def on_ready(self):
        print("[起動プロセス] BOTが起動しました")

bot = UnguraBot()
bot.run(TOKEN)