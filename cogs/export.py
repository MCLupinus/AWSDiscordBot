import discord
from discord import app_commands
from discord.ext import commands

class Export(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="export", description="チャンネル内の全ての座標をまとめます")
    @commands.has_any_role('管理者', 'Discord対応')
    async def export(self, interaction: discord.Interaction):

        vector_str = ""
        # 全てを文字列化
        async for message in interaction.channel.history(limit=None):
            vector_str += "\n" + message.content
        
        # 文字列編集
        vector_str = vector_str.replace(" ", "")
        vector_str = vector_str.replace("\n\n", "\n")

        # 改行で分割して各行を取得
        vectors = vector_str.strip().split('\n')

        # 各行をコンマで分割して2次元リストに変換
        except_text = []
        try:
            positions = [list(map(float, row.split(','))) for row in vectors]
            print(positions)
        except ValueError as e:
            # 想定しない文字を表示
            for char in vector_str:
                if char in  {',', ' ', '-', '.', '\n'}:
                    continue
                if not char.isdigit():
                    except_text.append(char)
                    
        if not len(except_text) == 0:
            await interaction.response.send_message(f"次の文字は無効です{except_text}", ephemeral=True)
            return

        result = ""
        for i in range(len(vectors)):
            result += f"""
    {{
		coords = vec3({positions[i][0]}, {positions[i][1]}, {positions[i][2]}),
		target = {{
			loc = vec3({positions[i][0]}, {positions[i][1]}, {positions[i][2]}),
			length = 1.2,
			width = 1.6,
			heading = 0,
			minZ = 29.49,
			maxZ = 32.09,
			label = '宝箱を開く'
		}},
		name = 'treasure{i}',
		label = '宝箱',
		owner = false,
		slots = 1,
		weight = 7000000,
	}},
"""
            

        with open("stashes.txt", "w", encoding="utf-8") as file:
            file.write(result)
        
        # ファイルを送信
        with open("stashes.txt", "rb") as file:
            await interaction.response.send_message("ファイルをエクスポートしました", file=discord.File(file, "stashes.txt"), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Export(bot))