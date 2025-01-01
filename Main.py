import discord
from discord.ext import commands
import os
import logging
from Database import Database

LOG_FILE = "bot.log"
# トークンの取得
TOKEN = os.getenv("UNGURA_DISCORD_TOKEN")

# ログファイルを作成
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# データベースからログを取得
context = Database("context.json")

# 設定
#intents = discord.Intents.default()
#intents.message_content = True
#intents.members = True
#intents.guilds = True
#intents.voice_states = True

IGNORE_LIST = ["Calculator.py"]

if TOKEN is None:
    raise ValueError(context.get_value("system_log", "token_not_found"))

class UnguraBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="/",
            intents=discord.Intents.all(),
            help_command=None
        )
        self.logger = logging.getLogger('shared_logger')

    async def setup_hook(self):
        load_file = context.get_value("system_log", "file_load")
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename in IGNORE_LIST:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                self.logger.info(load_file % filename)
        # インタラクションをシンクする。ギルドコマンドなので即時反映。
        await bot.tree.sync()

    async def on_ready(self):
        self.logger.info(context.get_value("system_log", "startup_successful"))

bot = UnguraBot()
bot.run(TOKEN)