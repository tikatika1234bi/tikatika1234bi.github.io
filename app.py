from flask import Flask, jsonify, request
import threading
import time
import json
import base64
from flask_cors import CORS  # CORS対応を追加

app = Flask(__name__)
CORS(app)  # GitHub Pagesからのリクエストを許可

# ゲーム状態の管理
game_state = {
    "energy": 0, "metal": 0, "gas": 0, "crystal": 0, "money": 0,
    "click_value": 1, "auto_drones": 0, "drone_cost": 10,
    "tech_level": 1, "tech_cost": 50, "prestige_bonus": 1.0,
    "metal_rate": 0, "gas_rate": 0, "crystal_rate": 0,
    "spaceships": 0, "spaceship_cost_metal": 50, "spaceship_cost_gas": 30,
    "relic_power": 0, "relic_cost": 100,
    "metal_upgrade_cost": 100, "gas_upgrade_cost": 200, "crystal_upgrade_cost": 300,
    "crystal_relics": 0, "crystal_relic_cost": 100
}

# 自動生産のバックグラウンド処理
def auto_production():
    while True:
        bonus = game_state["prestige_bonus"] * (1 + game_state["crystal_relics"] * 0.05)
        game_state["energy"] += game_state["auto_drones"] * bonus
        game_state["metal"] += game_state["metal_rate"] * bonus
        game_state["gas"] += game_state["gas_rate"] * bonus
        game_state["crystal"] += game_state["crystal_rate"] * bonus
        game_state["money"] += game_state["spaceships"] * 2
        time.sleep(1)

threading.Thread(target=auto_production, daemon=True).start()

# ゲーム状態を取得
@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(game_state)

# エネルギークリック
@app.route('/click', methods=['POST'])
def click():
    game_state["energy"] += game_state["click_value"] * game_state["prestige_bonus"]
    return '', 204

# ドローン購入
@app.route('/buy_drone', methods=['POST'])
def buy_drone():
    if game_state["energy"] >= game_state["drone_cost"]:
        game_state["energy"] -= game_state["drone_cost"]
        game_state["auto_drones"] += 1
        game_state["drone_cost"] = int(game_state["drone_cost"] * 1.5)
    return '', 204

# 技術研究
@app.route('/research_tech', methods=['POST'])
def research_tech():
    if game_state["energy"] >= game_state["tech_cost"]:
        game_state["energy"] -= game_state["tech_cost"]
        game_state["tech_level"] += 1
        game_state["click_value"] += 1
        game_state["tech_cost"] = int(game_state["tech_cost"] * 2)
    return '', 204

# プレステージ（銀河リセット）
@app.route('/prestige', methods=['POST'])
def prestige():
    bonus = game_state["tech_level"] * 0.1 + 1
    game_state.update({
        "energy": 0, "metal": 0, "gas": 0, "crystal": 0, "money": 0,
        "click_value": 1, "auto_drones": 0, "drone_cost": 10, "tech_cost": 50,
        "metal_rate": 0, "gas_rate": 0, "crystal_rate": 0,
        "spaceships": 0, "spaceship_cost_metal": 50, "spaceship_cost_gas": 30,
        "relic_power": 0, "relic_cost": 100,
        "metal_upgrade_cost": 100, "gas_upgrade_cost": 200, "crystal_upgrade_cost": 300,
        "crystal_relics": 0, "crystal_relic_cost": 100,
        "prestige_bonus": bonus  # ボーナスを保持
    })
    return '', 204

# 資源生産アップグレード
@app.route('/upgrade_metal', methods=['POST'])
def upgrade_metal():
    if game_state["energy"] >= game_state["metal_upgrade_cost"]:
        game_state["energy"] -= game_state["metal_upgrade_cost"]
        game_state["metal_rate"] += 1
        game_state["metal_upgrade_cost"] = int(game_state["metal_upgrade_cost"] * 1.5)
    return '', 204

@app.route('/upgrade_gas', methods=['POST'])
def upgrade_gas():
    if game_state["energy"] >= game_state["gas_upgrade_cost"]:
        game_state["energy"] -= game_state["gas_upgrade_cost"]
        game_state["gas_rate"] += 1
        game_state["gas_upgrade_cost"] = int(game_state["gas_upgrade_cost"] * 1.5)
    return '', 204

@app.route('/upgrade_crystal', methods=['POST'])
def upgrade_crystal():
    if game_state["energy"] >= game_state["crystal_upgrade_cost"]:
        game_state["energy"] -= game_state["crystal_upgrade_cost"]
        game_state["crystal_rate"] += 1
        game_state["crystal_upgrade_cost"] = int(game_state["crystal_upgrade_cost"] * 1.5)
    return '', 204

# 宇宙船建造
@app.route('/build_spaceship', methods=['POST'])
def build_spaceship():
    if game_state["metal"] >= game_state["spaceship_cost_metal"] and game_state["gas"] >= game_state["spaceship_cost_gas"]:
        game_state["metal"] -= game_state["spaceship_cost_metal"]
        game_state["gas"] -= game_state["spaceship_cost_gas"]
        game_state["spaceships"] += 1
        game_state["spaceship_cost_metal"] = int(game_state["spaceship_cost_metal"] * 1.5)
        game_state["spaceship_cost_gas"] = int(game_state["spaceship_cost_gas"] * 1.5)
    return '', 204

# レリック購入（お金）
@app.route('/buy_relic', methods=['POST'])
def buy_relic():
    if game_state["money"] >= game_state["relic_cost"]:
        game_state["money"] -= game_state["relic_cost"]
        game_state["relic_power"] += 1
        game_state["relic_cost"] = int(game_state["relic_cost"] * 2)
    return '', 204

# クリスタルレリック生成
@app.route('/create_crystal_relic', methods=['POST'])
def create_crystal_relic():
    if game_state["crystal"] >= game_state["crystal_relic_cost"] and game_state["relic_power"] >= 1:
        game_state["crystal"] -= game_state["crystal_relic_cost"]
        game_state["relic_power"] -= 1
        game_state["crystal_relics"] += 1
        game_state["crystal_relic_cost"] = int(game_state["crystal_relic_cost"] * 1.5)
    return '', 204

# セーブコード発行
@app.route('/save', methods=['GET'])
def save():
    state_json = json.dumps(game_state)
    save_code = base64.b64encode(state_json.encode()).decode()
    return jsonify({"code": save_code})

# セーブコードからロード
@app.route('/load', methods=['POST'])
def load():
    data = request.get_json()
    try:
        save_code = data["code"]
        state_json = base64.b64decode(save_code).decode()
        loaded_state = json.loads(state_json)
        game_state.update(loaded_state)
    except Exception as e:
        print(f"ロードエラー: {e}")
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
