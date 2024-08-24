import discord
from discord import app_commands
from discord.ext import commands
from .Data import DataJson
import re

class QuantityModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="数量入力")
        self.view = view
        self.quantity_input = discord.ui.TextInput(
            label="数量",
            placeholder="購入する数量を入力してください",
            default="1",
            min_length=1,
            max_length=5
        )
        self.add_item(self.quantity_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.view.quantity = int(self.quantity_input.value)
            await interaction.response.defer()
        except ValueError:
            await interaction.response.send_message("無効な数量です。正の整数を入力してください。", ephemeral=True)

class CalculatorSelectView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, data: dict[str, dict], tag: str):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.tag = tag
        self.data = data
        self.quantity = 1  # デフォルトの数量
        self.add_item(self.create_select())
        self.add_item(self.create_quantity_button())

    def create_select(self):
        # データが見つからなければエラー
        items = self.data[str(self.interaction.guild_id)]["invoice"][self.tag]["item"]
        amounts = self.data[str(self.interaction.guild_id)]["invoice"][self.tag]["amount"]
        options = []
        for i in range(len(items)):
            if amounts[i] <= -1:
                # 入っている値がマイナスであればその値段引きとする
                options.append(discord.SelectOption(label=items[i], description=f"{amounts[i] * -1}円引き"))
            elif amounts[i] < 1:
                # 入っている値が0以上1未満であればその値段割引とする
                options.append(discord.SelectOption(label=items[i], description=f"{amounts[i] * 100}%引き"))
            else:
                # 通常の値段は請求額とする
                options.append(discord.SelectOption(label=items[i], description=f"請求額：{amounts[i]}円"))
        
        select = discord.ui.Select(placeholder="請求内容を選択", options=options)
        select.callback = self.select_callback
        return select
    
    def create_quantity_button(self):
        button = discord.ui.Button(label="数量を入力", style=discord.ButtonStyle.primary)
        button.callback = self.quantity_button_callback
        return button

    async def quantity_button_callback(self, interaction: discord.Interaction):
        modal = QuantityModal(self)
        await interaction.response.send_modal(modal)

    async def select_callback(self, interaction: discord.Interaction):
        try:
            selected_option = interaction.data["values"][0]
            # 選ばれたものを取得する
            items: list[str] = self.data[str(self.interaction.guild_id)]["invoice"][self.tag]["item"]
            amounts: list[float] = self.data[str(self.interaction.guild_id)]["invoice"][self.tag]["amount"]
            current_value: float = self.data[str(interaction.guild_id)]["members"][str(interaction.user.id)]["calculate"]
            selected_amount = amounts[items.index(selected_option)]
        except:
            await interaction.response.edit_message(content=f"データの取得中にエラーが出ました", view=None)

        # 取得したデータを元に計算する
        if -1 < selected_amount and selected_amount < 1:
            # 1未満の小数であれば割引計算
            current_value -= current_value * selected_amount
        else:
            # 普通の計算をする
            current_value += selected_amount

        # 計算結果を保存
        try:
            self.data[str(interaction.guild_id)]["members"][str(interaction.user.id)]["calculate"] = current_value
            DataJson.save_json(self, self.data)
        except:
            await interaction.response.edit_message(content=f"計算中にエラーが出ました", view=None)

        # 処理結果を編集
        current_message = interaction.message.content
        splited_message = current_message.split("```")
        if selected_amount <= -1:
            # 入っている値がマイナスであればその値段引きとする
            add_message = f"{selected_option}({int(selected_amount * -1)}円引き)\n"
        elif selected_amount < 1:
            # 入っている値が0以上1未満であればその値段割引とする
            add_message = f"{selected_option}({int(selected_amount * 100)}%引き)\n"
        else:
            # 通常の値段は請求額とする
            add_message = f"{selected_option}({int(selected_amount)}円)\n"

        splited_message[1] += add_message
        
        result = f"{splited_message[0]}```{splited_message[1]}```\n## 合計金額 : {int(current_value)}円"

        await interaction.response.edit_message(content=result)

class Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="calc", description="計算機能を選択します")
    async def calc(self, interaction: discord.Interaction, tag: str):
        # データの取得
        data = DataJson.load_or_create_json(self)
        if not str(interaction.guild_id) in data:
            await interaction.followup.send("このサーバーのデータが見つかりませんでした\n`/reload`を試してください", ephemeral=True)
            return
        
        try:
            # 計算結果をリセット
            data[str(interaction.guild_id)]["members"][str(interaction.user.id)]["calculate"] = 0

            view = CalculatorSelectView(interaction, data, tag)
            await interaction.response.send_message(f"{tag}の請求額を計算します\n```請求内容\n```\n## 合計金額 : 0円", view=view, ephemeral=True)
        except:
            await interaction.response.send_message("処理中にエラーが発生しました")
        
async def setup(bot):
    await bot.add_cog(Calculator(bot))