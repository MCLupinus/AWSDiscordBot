import discord
from discord import app_commands
from discord.ext import commands
import json
import os

JSON_FILE_NAME = 'config.json'

class DataJson(commands.Cog):
    def init(self, bot):
        self.bot = bot

    # jsonデータを読み込み。見つからなければ作成
    def load_or_create_json(self):
        data = {}
        if not os.path.exists(JSON_FILE_NAME):
            print(f"{JSON_FILE_NAME}を作成します...")
            data = {
                str(guild.id): {
                } for guild in self.bot.guilds
                }
            self.save_json(data)
        else:
            with open(JSON_FILE_NAME, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"既存の{JSON_FILE_NAME}を読み込みました。")

        return data

    # Jsonを保存
    def save_json(self, data):
        with open(JSON_FILE_NAME, 'w', encoding='utf-8') as f:
             json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"{JSON_FILE_NAME}を保存しました。")

    def get_data(self, guild_id: int):
        data = DataJson.load_or_create_json(self)

        # データが見つからなければエラー
        if not str(guild_id) in data:
            ValueError("このサーバーのデータが見つかりませんでした\n`/reload`を試してください")

        return data

    def update_dict(self, original, target):
        for key, value in original.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target[key], dict):
                self.update_dict(value, target[key])
        return target
    
    def get_origin(self, guild_id: str, member_id: str):
        return {
            guild_id:{
                "members": {
                    member_id: {
                        "limited_roles":{
                            "count": 0,
                            "duration": None
                        },
                        "calculate":0,
                        "API_limit":0,
                        "point":0
                    }
                },
                "limited_roles_default": None,
                "priority_response":{
                    "roles": None,
                    "category": None
                },
                "invoice": {

                }
            }
        }

    # BOT起動時にチェック
    @commands.Cog.listener()
    async def on_ready(self):
        self.load_or_create_json()

    # BOTが新しいサーバーに参加した時にJsonに追加
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        data = self.load_or_create_json()
        if str(guild.id) not in data:
            data[str(guild.id)] = {
            }
            await self.save_json(data)
        print(f"{guild.name} (ID: {guild.id}) のデータを{JSON_FILE_NAME}に追加しました。")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = self.load_or_create_json()
        original_data = self.get_origin(str(member.guild.id), str(member.id))

        updated_data = self.update_dict(original_data, data)

        self.save_json(updated_data)

    @app_commands.command(name="reload", description="BOTの状態を再読み込みします")
    @commands.has_any_role('管理者', 'Discord対応')
    async def reload(self, interaction: discord.Interaction):
        await interaction.response.send_message("再読み込みを開始します...")
        data = self.load_or_create_json()
        for member in interaction.guild.members:
            original_data = self.get_origin(str(interaction.guild_id), str(member.id))

        updated_data = self.update_dict(original_data, data)

        self.save_json(updated_data)
        await interaction.edit_original_response(content="再読み込みしました。")

async def setup(bot):
    await bot.add_cog(DataJson(bot))