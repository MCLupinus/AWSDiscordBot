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
from discord.utils import get
from Database import Database

# 定数宣言
PRIORITY_RESPONSE = "priority_response" # 優先対応キー名
PRIORITY_ROLES = "roles"                # 優先対応の対象ロールキー名
PRIORITY_CATEGORY = "category"          # 優先対応の移動カテゴリーキー名
INVOICE = "invoice"                     # 請求書キー名
INVOICE_ITEM = "item"                   # 請求書の内容キー名
INVOICE_AMOUNT = "amount"               # 請求書の金額キー名

class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Database("config.json")

    # 優先対応するロールを設定する
    async def set_priority_role(self, interaction, target):
        role_list = []
        for role in target.split():
            try:
                role_id = int(role.strip('<@&>'))
                print(role_id)
                priority_role = interaction.guild.get_role(role_id)
                if priority_role:
                    role_list.append(priority_role.id)
                else:
                    print("不明なロール: " + role)
            except ValueError:
                print("Error: 不明なロール: " + role)
                continue
        
        # ロールIDを保存するデータ作成
        if role_list:
            return role_list
        else:
            return None

    # 優先対応の対象を設定する
    @app_commands.command(name="op_priority", description="優先対応するロールを設定します")
    @app_commands.describe(
        option="優先対応設定の指定",
        target="優先対応を適用する対象"
    )
    @app_commands.choices(option=[
        discord.app_commands.Choice(name="Role", value="roles"),
        discord.app_commands.Choice(name="Category", value="category")
    ])
    @commands.has_any_role('管理者', 'Discord対応')
    async def priority(self, interaction: discord.Interaction, option: str, target: str = None):        
        # 時間がかかる場合があるため一旦送信する
        await interaction.response.defer(ephemeral=True)

        # targetが空だったら空のデータを作成する
        if target == None:
            self.config.set_value(str(interaction.guild_id), PRIORITY_RESPONSE, option, value=None)

            await interaction.followup.send(f"{target}を初期化しました")
            return

        result = []
        # ロールの設定
        if option == PRIORITY_ROLES:
            result = await self.set_priority_role(interaction, target)

            # 出力
            # 該当するロールが見つからない場合は優先対応を削除
            if result:
                role_mention = []
                for role in result:
                    role_mention.append(interaction.guild.get_role(role).mention)
                await interaction.followup.send("次のロールを優先対応として扱うよう設定しました\n" + " ".join(role_mention))
            else:
                await interaction.followup.send("ロールが見つからなかったため優先対応するロールを削除しました", ephemeral=True)

        elif option == PRIORITY_CATEGORY:
            category_id = int(target)
            if get(interaction.guild.categories, id=category_id):
                result = category_id
                await interaction.followup.send(f"{interaction.guild.get_channel(category_id).name}カテゴリーを優先対応の移動先へ設定しました", ephemeral=True)
            else:
                result = None
                await interaction.followup.send("指定されたIDのカテゴリーは見つかりませんでした", ephemeral=True)

        self.config.set_value(str(interaction.guild_id), PRIORITY_RESPONSE, option, value=result)

    # 請求書のリストを作成する
    @app_commands.command(name="addinvoice", description="請求する金額を計算するためのリストに内容を追加します")
    @app_commands.describe(
        tag="請求書の識別タグ",
        item="追加する請求内容",
        amount="請求額"
    )
    async def add_invoice(self, interaction: discord.Interaction, tag: str, item: str, amount: float):
        # タグを小文字に変換
        tag = tag.lower()

        try:
            data = DataJson.get_data(self, interaction.guild_id)
        except ValueError as e:
            await interaction.response.send_message(e, ephemeral=True)
        
        data[str(interaction.guild_id)].setdefault(INVOICE, {})

        # tagが存在するか確認してログに書き込む
        if tag in data[str(interaction.guild_id)][INVOICE]:
            item_list = data[str(interaction.guild_id)][INVOICE][tag][INVOICE_ITEM]
            amount_list = data[str(interaction.guild_id)][INVOICE][tag][INVOICE_AMOUNT]
            result_log = f"{tag}に以下の内容を追加しました\n"
        else:
            item_list = []
            amount_list = []
            data[str(interaction.guild_id)][INVOICE].setdefault(tag, {})
            result_log = f"新しく{tag}を作成し、以下の内容を追加しました\n"
        
        ### この時点で{tag}は確実に存在する

        # 請求内容と請求額を追加する
        if item in item_list:
            # アイテムの要素番号取得
            i = item_list.index(item)
            # データを上書き
            item_list[i] = item
            amount_list[i] = amount
        else:
            # 無ければ追加する
            item_list.append(item)
            amount_list.append(amount)

        # jsonに保存する
        data[str(interaction.guild_id)][INVOICE][tag][INVOICE_ITEM] = item_list
        data[str(interaction.guild_id)][INVOICE][tag][INVOICE_AMOUNT] = amount_list
        try:
            DataJson.save_json(self, data)
        except:
            print("データの保存中にエラーが発生しました")
            await interaction.response.send_message("実行中にエラーが発生しました", ephemeral=True)
            return
        
        if amount <= -1:
            # -1より小さければ値引き額として保存
            result_log += f"値引き内容 : {item}\n値引き額 : {int(amount * -1)}円"
        elif amount < 1:
            # -1より大きく1より小さければ割引きとして保存
            result_log += f"割引き内容 : {item}\n割引き : {int(amount * 100)}%"
        else:
            result_log += f"請求内容：{item}\n値段：{int(amount)}円"

        await interaction.response.send_message(result_log, ephemeral=True)

    @app_commands.command(name="removeinvoice", description="請求する金額を計算するためのリストから内容を削除します")
    @app_commands.describe(
        tag="請求書の識別タグ",
        item="削除する請求内容",
    )
    async def remove_invoice(self, interaction: discord.Interaction, tag: str, item: str):
        # タグを小文字に変換
        tag = tag.lower()
        
        try:
            data = DataJson.get_data(self, interaction.guild_id)
        except ValueError as e:
            await interaction.response.send_message(e, ephemeral=True)
        
        item_list = []
        amount_list = []
        
        if tag in data[str(interaction.guild_id)][INVOICE]:
            item_list = data[str(interaction.guild_id)][INVOICE][tag][INVOICE_ITEM]
            amount_list = data[str(interaction.guild_id)][INVOICE][tag][INVOICE_AMOUNT]
        else:
            await interaction.response.send_message(f"{tag}が見つかりませんでした", ephemeral=True)
            return

        try:
            index = item_list.index(item)
            item_list.pop(index)
            amount_list.pop(index)
        except:
            await interaction.response.send_message("実行中にエラーが発生しました", ephemeral=True)

        data[str(interaction.guild_id)][INVOICE][tag][INVOICE_ITEM] = item_list
        data[str(interaction.guild_id)][INVOICE][tag][INVOICE_AMOUNT] = amount_list
        try:
            DataJson.save_json(self, data)
        except:
            print("データの保存中にエラーが発生しました")

        await interaction.response.send_message(f"{tag}から{item}を削除しました", ephemeral=True)

    @app_commands.command(name="defaulttimelimit", description="期限付きロールの通常有効時間を設定します")
    async def default_time_limit(self, interaction: discord.Interaction, grant_role: discord.Role, day:int, hours: int=0, minutes: int=0):
        try:
            data = DataJson.get_data(self, interaction.guild_id)
        except:
            print("データの保存中にエラーが発生しました")
        data[str(interaction.guild_id)]["limited_roles_default"][grant_role.id] = [day, hours, minutes]

        DataJson.save_json(self, data)

async def setup(bot):
    await bot.add_cog(Setting(bot))