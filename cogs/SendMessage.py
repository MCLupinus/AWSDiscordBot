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

class EditMessageModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="メッセージを送信")
        self.edit_field = discord.ui.TextInput(label="送信するメッセージ", style=discord.TextStyle.paragraph)
        self.add_item(self.edit_field)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.channel.send(content=self.edit_field)

class SendMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="say", description="BOTとしてメッセージを送信する")
    @commands.has_any_role('管理者', 'Discord対応')
    async def say_message(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EditMessageModal())

async def setup(bot):
    await bot.add_cog(SendMessage(bot))