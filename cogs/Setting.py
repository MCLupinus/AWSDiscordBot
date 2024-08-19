import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from .Data import DataJson

class Setting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    async def priority(self, interaction: discord.Interaction,option: str, target: str = None):        
        # 時間がかかる場合があるため一旦送信する
        await interaction.response.defer(ephemeral=True)

        data = DataJson.load_or_create_json(self)

        # データが見つからなければエラー
        if not str(interaction.guild_id) in data:
            await interaction.followup.send("このサーバーのデータが見つかりませんでした\n`/uncut`を試してください", ephemeral=True)
            return

        # targetが空だったら空のデータを作成する
        if target == None:
            null_data = {
                "priority_response": {
                    option: None
                }
            }

            data = DataJson.load_or_create_json(self)
            data[str(interaction.guild_id)] = null_data
            DataJson.save_json(self, data)
            await interaction.followup.send(f"{target}を初期化しました")

        result = []
        # ロールの設定
        if option == "roles":
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

        elif option == "category":
            category_id = int(target)
            if get(interaction.guild.categories, id=category_id):
                result = category_id
                await interaction.followup.send(f"{interaction.guild.get_channel(category_id).name}カテゴリーを優先対応の移動先へ設定しました", ephemeral=True)
            else:
                result = None
                await interaction.followup.send("指定されたIDのカテゴリーは見つかりませんでした", ephemeral=True)

        data[str(interaction.guild_id)].setdefault("priority_response", {})
        data[str(interaction.guild_id)]["priority_response"][option] = result
        DataJson.save_json(self, data)

async def setup(bot):
    await bot.add_cog(Setting(bot))