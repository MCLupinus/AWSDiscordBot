import json
import os

class Database():
    def __init__(self, file_name):
        self.file_name = file_name

    # jsonを保存する
    def save_json(self, data):
        with open(self.file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[データベースログ] {self.file_name}を保存しました")

    # データをロードする
    # 既に存在する場合はそれを、存在しない場合は新しく作成する
    def load_or_create_json(self):
        data = {}
        if not os.path.exists(self.file_name):
            print(f"[データベースログ] {self.file_name}を作成しました")
            self.save_json(data)
        else:
            with open(self.file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[データベースログ] 既存の{self.file_name}を読み込みました")

        return data

    # 値をいれる
    def set_value(self, *keys, value):
        data = self.load_or_create_json()
        current_data = data
        for key in keys[:-1]:  # 最後のキーを除いて処理
            key = str(key)
            if key not in current_data or current_data[key] is None:
                current_data[key] = {}
                print(f"[データベースログ] {key}を新規作成しました")
            current_data = current_data[key]
        
        # 最後のキーに値を挿入
        last_key = keys[-1]
        current_data[last_key] = value
        print(f"[データベースログ] {last_key}に{value}を代入しました")

        # データ保存
        self.save_json(data)

    def remove_key(self, *keys):
        data = self.load_or_create_json()
        current_data = data
        
        # 最後のキーまで辿る
        for key in keys[:-1]:
            if key not in current_data:
                print(f"[データベースログ] {key}が見つかりません")
                return False
            current_data = current_data[key]
        
        # 最後のキーを削除
        last_key = keys[-1]
        if last_key in current_data:
            del current_data[last_key]
            print(f"[データベースログ] {last_key}を削除しました")
            self.save_json(data)
            return True
        else:
            print(f"[データベースログ] {last_key}が見つかりません")
            return False