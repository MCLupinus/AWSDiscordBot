import os
import sys
if __name__ == "__main__":
    os.chdir(".")
    sys.path.append(os.getcwd())
    
    # main.pyを実行
    os.system(f"{sys.executable} main.py")

import discord
from discord import app_commands
from discord.ext import commands
from Database import Database

class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Database("config.json")

    # 有効化
    @app_commands.command(name="vcTracker_enable", description="VCの管理を有効にします")
    @commands.has_any_role('管理者', 'Discord対応')
    async def enable(self, interaction: discord.Interaction, hours: int, minutes: int, available: int):
        pass

async def setup(bot):
    await bot.add_cog(VCTracker(bot))