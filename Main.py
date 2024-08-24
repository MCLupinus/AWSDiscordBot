import discord
from discord.ext import commands
import os

# メイン
TOKEN = os.getenv("UNGURA_DISCORD_TOKEN")

IGNORE_LIST = ["StartSale.py", "Calculator.py"]

if TOKEN is None:
    raise ValueError("Discord BOTトークンが見つかりません")

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
                print(f"{filename}を読み込み")
        # インタラクションをシンクする。ギルドコマンドなので即時反映。
        await bot.tree.sync()

    async def on_ready(self):
        print("BOTが起動しました")

bot = MyBot()
bot.run(TOKEN)
