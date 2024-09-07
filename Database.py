import json
import os


class Database():
    def __init__(self, file_name):
        self.file_name = file_name

    # jsonを保存する
    def save_json(self, data):
        with open(self.file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"データベースログ：{self.file_name}を保存")

    # 既に存在する場合はそれを、存在しない場合は新しく作成する
    def load_or_create_json(self):
        data = {}
        if not os.path.exists(self.file_name):
            print(f"データベースログ：{self.file_name}を作成")
            self.save_json(data)
        else:
            with open(self.file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"データベースログ：既存の{self.file_name}を読み込み")

        return data

    def insert_value(self, data, keys, value):
        current_data = data
        for i, key in enumerate(keys):
            # 最後のキーに達したら値を挿入
            if i == len(keys) - 1:
                current_data[key] = value
                print(f"データベースログ：{key}に{value}を挿入")
            else:
                # キーが存在しない場合は空の辞書を作成
                if key not in current_data or current_data[key] is None:
                    current_data[key] = {}
                    print(f"データベースログ：{key}を新規作成")
                # 次の階層へ進む
                current_data = current_data[key]
        
        self.save_json()

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