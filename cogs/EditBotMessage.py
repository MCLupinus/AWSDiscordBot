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
    def __init__(self, message: discord.Message):
        super().__init__(title="メッセージを編集")
        self.message = message
        self.edit_field = discord.ui.TextInput(label="編集メッセージ", style=discord.TextStyle.paragraph, default=message.content)
        self.add_item(self.edit_field)

    async def on_submit(self, interaction: discord.Interaction):
        await self.message.edit(content=self.edit_field)
        await interaction.response.send_message("メッセージを編集しました", ephemeral=True)

class EditBotMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # コンテキストメニューを登録
        self.bot.tree.add_command(edit_message)

    async def cog_unload(self):
        # コンテキストメニューを削除
        self.bot.tree.remove_command(edit_message.name, type=discord.AppCommandType.message)

@app_commands.context_menu(name="[Admin]メッセージを編集")
async def edit_message(interaction: discord.Interaction, message: discord.Message):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
        return
    
    if message.author != interaction.client.user:
        await interaction.response.send_message("このメッセージは編集できません。", ephemeral=True)
        return
    
    await interaction.response.send_modal(EditMessageModal(message))

async def setup(bot):
    await bot.add_cog(EditBotMessage(bot))