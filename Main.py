import discord
from discord.ext import commands
import os

# メイン
TOKEN = os.getenv("UNGURA_DISCORD_TOKEN")

# 設定
discord.Intents.default().members = True

IGNORE_LIST = ["StartSale.py", "Calculator.py", "EndSale.py", "export.py", "LimitedRole.py", "Load.py", "point.py", "RoleManagement.py", "SaleDuration.py", "StartSale.py"]

if TOKEN is None:
    raise ValueError("[起動プロセス] Discord BOTトークンが見つかりません")

class MyBot(commands.Bot):
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

bot = MyBot()
bot.run(TOKEN)