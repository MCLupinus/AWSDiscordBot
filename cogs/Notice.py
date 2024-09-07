import discord
from discord import app_commands
from discord.ext import commands

MONITOR_CHANNEL_ID = 1267690436714168340
TARGET_ROLE_ID = 1256863159160012902
IGNORE_ROLE_ID = 1256863062967717948

class Notice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # BOTのメッセージであれば反応しない
        ignore_role = message.guild.get_role(IGNORE_ROLE_ID)
        if message.author == self.bot.user or message.author in ignore_role.members:
            return
        
        if message.channel.parent_id == MONITOR_CHANNEL_ID:
            role = message.guild.get_role(TARGET_ROLE_ID)
            await message.reply(f"{role.mention}\n{message.author.mention}からの連絡内容を確認してください")

async def setup(bot):
    await bot.add_cog(Notice(bot))