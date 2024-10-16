import discord
from discord.ext import commands
from discord import app_commands

class ModalUi(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(title="サンプルモーダル")
        self.input = discord.ui.TextInput(
            label="入力フィールド",
            default=interaction.user.name,
            style=discord.TextStyle.short
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"入力された値: {self.input.value}")

class ModalDemo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def open_modal(self, interaction: discord.Interaction):
        modal = ModalUi(interaction)
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(ModalDemo(bot))