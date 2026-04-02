# =====================================================================
# タイトル: HD自作エンジン Webアプリ版 (Ver 3.1 カスタマイズ＆UI最適化版)
# =====================================================================
import streamlit as st
import io
import contextlib
import swisseph as swe
import datetime
import collections
import os
import urllib.request

# =====================================================================
# ▼▼▼ 1. UI・デザインのカスタマイズ設定 ▼▼▼
# （文字の大きさや区切り線は、ここを変更するだけで一括で変わります）
# =====================================================================
# Streamlitのページ設定
st.set_page_config(page_title="HD System Spec", page_icon="💻", layout="wide")

# 区切り線のデザイン（圧を減らしてスッキリと）
DIVIDER = "-" * 35 

# 天体の表示順と日本語名
PLANET_ORDER = [
    "Sun", "Earth", "Moon", "NorthNode", "SouthNode", 
    "Mercury", "Venus", "Mars", "Jupiter", "Saturn", 
    "Uranus", "Neptune", "Pluto", "Chiron"
]

PLANET_JP = {
    "Sun": "太陽", "Earth": "地球", "Moon": "月", 
    "NorthNode": "ノースノード", "SouthNode": "サウスノード",
    "Mercury": "水星", "Venus": "金星", "Mars": "火星", 
    "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星", 
    "Neptune": "海王星", "Pluto": "冥王星", "Chiron": "キロン"
}

# =====================================================================
# ▼▼▼ スマホの画面で自動折り返しさせるための魔法 ▼▼▼
# =====================================================================
st.markdown("""
<style>
pre {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
}
</style>
""", unsafe_allow_html=True)

# 圧を抑えた小さめのタイトル
st.markdown("### 💻 SYSTEM SPECIFICATION REPORT")
st.markdown("<span style='font-size: 0.9em; color: gray;'>生体システムのハードウェア仕様＆OS特性を解析します。</span>", unsafe_allow_html=True)

# =====================================================================
# ▼▼▼ 2. サイドバー: 入力インターフェース ▼▼▼
# =====================================================================
st.sidebar.header("▼ 誕生日情報の入力 (JST)")

input_date = st.sidebar.date_input("生年月日", datetime.date(1971, 12, 20))

st.sidebar.markdown("出生時刻")
col1, col2 = st.sidebar.columns(2)
HOUR = col1.selectbox("時", range(24), index=9)
MINUTE = col2.selectbox("分", range(60), index=1)

YEAR = input_date.year
MONTH = input_date.month
DAY = input_date.day

# =====================================================================
# ▼▼▼ 3. 計算エンジン・スコア設定 ▼▼▼
# =====================================================================
CUSTOM_WEIGHTS = {
    "Sun": 35.0, "Earth": 35.0, "Moon": 10.0, "Mercury": 4.5, "Venus": 4.0, 
    "Mars": 3.5, "Jupiter": 3.0, "Saturn": 2.0, "Uranus": 1.5, "Neptune": 1.0, "Pluto": 0.5,
    "NorthNode": 0.0, "SouthNode": 0.0, "Chiron": 0.0
}
DORMANT_MULTIPLIER = 0.3 
FORCED_GATES = set()

# --- 天文暦データのセットアップ ---
ephe_dir = './ephe_data'
os.makedirs(ephe_dir, exist_ok=True)
files = ['sepl_18.se1', 'semo_18.se1', 'seas_18.se1']
base_url = 'https://github.com/aloistr/swisseph/raw/master/ephe/'
for f in files:
    if not os.path.exists(os.path.join(ephe_dir, f)): 
        urllib.request.urlretrieve(base_url+f, os.path.join(ephe_dir, f))
swe.set_ephe_path(ephe_dir)

# --- HDマスターデータ ---
GATE_SEQUENCE = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
CENTER_GATES = {"Head": {64, 61, 63}, "Ajna": {47, 24, 4, 17, 43, 11}, "Throat": {62, 23, 56, 31, 8, 33, 20, 16, 35, 12, 45}, "G": {7, 1, 13, 25, 46, 2, 15, 10}, "Heart": {21, 51, 26, 40}, "Sacral": {34, 5, 14, 29, 59, 9, 3, 42, 27}, "Splenic": {48, 57, 44, 50, 32, 28, 18}, "SolarPlexus": {36, 22, 37, 6, 49, 55, 30}, "Root": {58, 38, 54, 53, 60, 52, 19, 39, 41}}
MOTOR_CENTERS = {"Sacral", "Heart", "SolarPlexus", "Root"}
CENTER_JP = {"Head": "ヘッド", "Ajna": "アジュナ", "Throat": "喉", "G": "G", "Heart": "ハート", "Sacral": "仙骨", "Splenic": "Spleen", "SolarPlexus": "太陽神経叢", "Root": "ルート"}
CHANNELS = {
    "Head_Ajna": [(64,47,"64-47"), (61,24,"61-24"), (63,4,"63-4")], "Ajna_Throat": [(17,62,"17-62"), (43,23,"43-23"), (11,56,"11-56")],
    "Throat_G": [(31,7,"31-7"), (8,1,"8-1"), (33,13,"33-13"), (10,20,"10-20")], "Throat_Heart": [(45,21,"45-21")],
    "Throat_SolarPlexus": [(35,36,"35-36"), (12,22,"12-22")], "Throat_Splenic": [(16,48,"16-48"), (20,57,"20-57")],
    "Throat_Sacral": [(20,34,"20-34")], "G_Heart": [(25,51,"25-51")], "G_Sacral": [(5,15,"5-15"), (46,29,"46-29"), (2,14,"2-14"), (10,34,"10-34")],
    "G_Splenic": [(10,57,"10-57")], "Heart_SolarPlexus": [(40,37,"40-37")], "Heart_Splenic": [(26,44,"26-44")],
    "Sacral_SolarPlexus": [(6,59,"6-59")], "Sacral_Splenic": [(50,27,"50-27"), (34,57,"34-57")],
    "Sacral_Root": [(53,42,"53-42"), (3,60,"3-60"), (9,52,"9-52")], "SolarPlexus_Root": [(19,49,"19-49"), (39,55,"39-55"), (41,30,"41-30")],
    "Splenic_Root": [(18,58,"18-58"), (28,38,"28-38"), (32,54,"32-54")]
}
CROSS_NAMES = {
    1:("the Sphinx","Self-Expression","Defiance"), 2:("the Sphinx","the Driver","Defiance"), 3:("Laws","Mutation","Wishes"), 4:("Explanation","Formulization","Revolution"),
    5:("Consciousness","Habits","Separation"), 6:("Eden","Conflict","the Plane"), 7:("the Sphinx","Interaction","Masks"), 8:("Contagion","Contribution","Uncertainty"),
    9:("Planning","Focus","Identification"), 10:("the Vessel of Love","Behavior","Prevention"), 11:("Eden","Ideas","Education"), 12:("Eden","Articulation","Education"),
    13:("the Sphinx","the Listener","Masks"), 14:("Contagion","Empowering","Uncertainty"), 15:("the Vessel of Love","Extremes","Prevention"), 16:("Planning","Experimentation","Identification"),
    17:("Service","Opinions","Upheaval"), 18:("Service","Correction","Upheaval"), 19:("the Four Ways","Need","Refinement"), 20:("the Sleeping Phoenix","Awakening","Duality"),
    21:("Tension","Control","Effort"), 22:("Rulership","Grace","Informing"), 23:("Explanation","Assimilation","Dedication"), 24:("the Four Ways","Rationalization","Incarnation"),
    25:("the Vessel of Love","Innocence","Healing"), 26:("Rulership","the Trickster","Confrontation"), 27:("the Unexpected","Caring","Alignment"), 28:("the Unexpected","Risks","Alignment"),
    29:("Contagion","Commitment","Industry"), 30:("Contagion","Fates","Industry"), 31:("the Unexpected","Influence","the Alpha"), 32:("Maya","Conservation","Limitation"),
    33:("the Four Ways","Retreat","Refinement"), 34:("the Sleeping Phoenix","Power","Duality"), 35:("Consciousness","Experience","Separation"), 36:("Eden","Crisis","the Plane"),
    37:("Planning","Bargains","Migration"), 38:("Tension","Opposition","Dedication"), 39:("Tension","Provocation","Effort"), 40:("Planning","Denial","Migration"),
    41:("the Unexpected","Fantasy","the Alpha"), 42:("Maya","Growth","Limitation"), 43:("Explanation","Insight","Dedication"), 44:("the Four Ways","Alertness","Incarnation"),
    45:("Rulership","the Gatherer","Confrontation"), 46:("the Vessel of Love","Serendipity","Healing"), 47:("Rulership","Oppression","Informing"), 48:("Tension","Depth","Endeavor"),
    49:("Explanation","Principles","Revolution"), 50:("Laws","Values","Wishes"), 51:("Penetration","Shock","the Clarion"), 52:("Service","Stillness","Demands"),
    53:("Penetration","Beginnings","Cycles"), 54:("Penetration","Ambition","Cycles"), 55:("the Sleeping Phoenix","Moods","Spirit"), 56:("Laws","Stimulation","Distraction"),
    57:("Penetration","Intuition","the Clarion"), 58:("Service","Vitality","Demands"), 59:("the Sleeping Phoenix","Strategy","Spirit"), 60:("Laws","Limitation","Distraction"),
    61:("Maya","Thinking","Obscuration"), 62:("Maya","Detail","Obscuration"), 63:("Consciousness","Doubts","Dominion"), 64:("Consciousness","Confusion","Dominion")
}

# =====================================================================
# ▼▼▼ 4. 計算・出力ロジック ▼▼▼
# =====================================================================
def get_gate_and_line(lon):
    offset = (lon - 302.0 + 360.0) % 360.0
    return GATE_SEQUENCE[int(offset/5.625)], int((offset%5.625)/(5.625/6))+1

def calculate_design_jd(jd_b, sun_lon):
    target = (sun_lon - 88.0 + 360.0) % 360.0
    jd_guess = jd_b - 89.5
    for _ in range(20):
        pos, _ = swe.calc_ut(jd_guess, swe.SUN); diff = (pos[0]-target+360.0)%360.0
        if diff > 180: diff -= 360.0
        jd_guess -= diff / 0.9856
        if abs(diff) < 0.00001: break
    return jd_guess

def get_chart_data(y, m, d, h, mi):
    utc = datetime.datetime(y, m, d, h, mi) - datetime.timedelta(hours=9)
    jd_b = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute/60.0)
    sun_pos, _ = swe.calc_ut(jd_b, swe.SUN); jd_d = calculate_design_jd(jd_b, sun_pos[0])
    data = []
    planets = {swe.SUN: "Sun", swe.MOON: "Moon", swe.TRUE_NODE: "NorthNode", swe.MERCURY: "Mercury", swe.VENUS: "Venus", swe.MARS: "Mars", swe.JUPITER: "Jupiter", swe.SATURN: "Saturn", swe.URANUS: "Uranus", swe.NEPTUNE: "Neptune", swe.PLUTO: "Pluto", swe.CHIRON: "Chiron"}
    for is_red, jd in [(True, jd_d), (False, jd_b)]:
        col = "Red" if is_red else "Black"
        for p_id, p_name in planets.items():
            pos, _ = swe.calc_ut(jd, p_id); g, l = get_gate_and_line(pos[0])
            data.append({"planet": p_name, "color": col, "gate": g, "line": l})
            if p_name == "Sun": eg, el = get_gate_and_line((pos[0]+180)%360); data.append({"planet": "Earth", "color": col, "gate": eg, "line": el})
            if p_name == "NorthNode": sg, sl = get_gate_and_line((pos[0]+180)%360); data.append({"planet": "SouthNode", "color": col, "gate": sg, "line": sl})
    return data, jd_d

def print_master_report(data, jd_d, y, m, d, h, mi):
    dv = swe.revjul(jd_d)
    dj = datetime.datetime(int(dv[0]), int(dv[1]), int(dv[2]), int(dv[3]), int((dv[3]%1)*60)) + datetime.timedelta(hours=9)
    print(f"黒(Pers): {y}/{m}/{d} {h:02d}:{mi:02d}\n<span style='color:#FF4B4B; font-weight:bold;'>赤(Design): {dj.strftime('%Y/%m/%d %H:%M')} (JST)</span>\n")

    core_g = set([x["gate"] for x in data if x["planet"] != "Chiron"]) | FORCED_GATES
    
    def get_defined_centers(test_gates):
        on_c = set()
        for r, cs in CHANNELS.items():
            c1, c2 = r.split('_')
            for g1, g2, cid in cs:
                if g1 in test_gates and g2 in test_gates:
                    on_c.update([c1, c2])
        return on_c
        
    def get_islands_for_gates(test_gates, defined_centers):
        adj = collections.defaultdict(list)
        for r, cs in CHANNELS.items():
            c1, c2 = r.split('_')
            for g1, g2, cid in cs:
                if g1 in test_gates and g2 in test_gates:
                    adj[c1].append(c2)
                    adj[c2].append(c1)
        isls = []
        visited = set()
        for c in defined_centers:
            if c not in visited:
                isl = set()
                q = [c]
                while q:
                    curr = q.pop(0)
                    if curr not in visited:
                        visited.add(curr)
                        isl.add(curr)
                        q.extend([n for n in adj[curr] if n in defined_centers and n not in visited])
                isls.append(isl)
        return isls

    initial_on_c = get_defined_centers(core_g)
    initial_islands = get_islands_for_gates(core_g, initial_on_c)
    on_c = initial_on_c 

    if len(initial_islands) == 0: definition_type = "Reflector (None)"
    elif len(initial_islands) == 1: definition_type = "Single Definition"
    elif len(initial_islands) == 2: definition_type = "Split Definition"
    elif len(initial_islands) == 3: definition_type = "Triple Split Definition"
    else: definition_type = "Quadruple Split Definition"

    b_gates_1 = []
    b_gates_2 = []
    
    if len(initial_islands) > 1:
        for g in range(1, 65):
            if g not in core_g:
                test_gates = core_g | {g}
                test_on_c = get_defined_centers(test_gates)
                if len(test_on_c) == len(initial_on_c):
                    test_islands = get_islands_for_gates(test_gates, test_on_c)
                    if len(test_islands) > 0 and len(test_islands) < len(initial_islands):
                        b_gates_1.append(g)
                        
        if not b_gates_1:
            missing = [g for g in range(1, 65) if g not in core_g]
            for i in range(len(missing)):
                for j in range(i+1, len(missing)):
                    g1, g2 = missing[i], missing[j]
                    test_gates = core_g | {g1, g2}
                    test_on_c = get_defined_centers(test_gates)
                    if len(test_on_c) == len(initial_on_c):
                        test_islands = get_islands_for_gates(test_gates, test_on_c)
                        if len(test_islands) > 0 and len(test_islands) < len(initial_islands):
                            b_gates_2.append((min(g1, g2), max(g1, g2)))

    motor_to_throat = False
    connected_motors = set()
    if "Throat" in on_c:
        adj = collections.defaultdict(list)
        for r, cs in CHANNELS.items():
            c1, c2 = r.split('_')
            for g1, g2, cid in cs:
                if g1 in core_g and g2 in core_g:
                    adj[c1].append(c2)
                    adj[c2].append(c1)
        
        v_throat = set()
        queue = ["Throat"]
        while queue:
            curr = queue.pop(0)
            if curr not in v_throat:
                v_throat.add(curr)
                if curr in MOTOR_CENTERS:
                    motor_to_throat = True
                    connected_motors.add(curr)
                queue.extend([n for n in adj[curr] if n not in v_throat])

    if "Sacral" in on_c: type_str = "Manifesting Generator" if motor_to_throat else "Generator"
    else:
        if motor_to_throat: type_str = "Manifestor"
        elif len(on_c) > 0: type_str = "Projector"
        else: type_str = "Reflector"

    def calc_gate_score(gate, planet):
        c = next((k for k, v in CENTER_GATES.items() if gate in v), None)
        if c in MOTOR_CENTERS:
            return (CUSTOM_WEIGHTS.get(planet, 0) / 2.0) * (1.0 if c in on_c else DORMANT_MULTIPLIER)
        return 0.0

    raw_s = sum([calc_gate_score(x["gate"], x["planet"]) for x in data if x["planet"] != "Chiron"])

    print(DIVIDER)
    print(f"🔋 自発エネルギー密度: {raw_s:.1f} / 100")
    if connected_motors:
        motors_jp = "・".join([CENTER_JP.get(m, m) for m in connected_motors])
        print(f"💡 喉に連動するモーター: {motors_jp}")
    print(DIVIDER)

    # ▼ 天体リストの出力（順番と改行デザインの反映） ▼
    for p in PLANET_ORDER:
        r = next((x for x in data if x["planet"]==p and x["color"]=="Red"), None)
        b = next((x for x in data if x["planet"]==p and x["color"]=="Black"), None)
        if r and b:
            rs = calc_gate_score(r["gate"], p) if p != "Chiron" else 0.0
            bs = calc_gate_score(b["gate"], p) if p != "Chiron" else 0.0
            
# スコアが0なら7文字分の空白を埋め、あれば数値を表示して長さを固定
            r_sc = f" [{rs:>4.1f}]" if rs>0 else "       "
            b_sc = f" [{bs:>4.1f}]" if bs>0 else "       "
            
            p_jp = PLANET_JP.get(p, p)
            
            print(f"{p_jp}")
            print(f"<span style='color:#FF4B4B;'>赤 {r['gate']:>2}.{r['line']}{r_sc}</span> ║ 黒 {b['gate']:>2}.{b['line']}{b_sc}\n")
            
    print(DIVIDER)
    print("🏢 センター別 実装モジュール")
    print(DIVIDER)
    center_order = ["Head", "Ajna", "Throat", "G", "Heart", "Sacral", "Splenic", "SolarPlexus", "Root"]
    for c in center_order:
        c_gates = []
        c_score = 0.0
        status = "定義済み" if c in on_c else "未定義"
        for x in data:
            if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]:
                s = calc_gate_score(x["gate"], x["planet"])
                c_score += s
                c_gates.append((x["gate"], x["line"], x["planet"], x["color"], s))
                
        display_center = CENTER_JP.get(c, c)
        
        # センターの表示デザイン反映
        print(f"■ {display_center}")
        print(f"{status} [小計: {c_score:.1f}]")
        
        if not c_gates:
            print("ー 該当なし\n")
        else:
            c_gates_sorted = sorted(c_gates, key=lambda x: x[0])
            for g, line, p, col, s in c_gates_sorted:
                score_str = f" [{s:>4.1f}]" if s > 0 else ""
                p_jp = PLANET_JP.get(p, p)
                
                if col == "Red":
                    print(f"ー <span style='color:#FF4B4B;'>Gate {g:>2}.{line} ({p_jp}/赤){score_str}</span>")
                else:
                    print(f"ー Gate {g:>2}.{line} ({p_jp}/黒){score_str}")
            print("") # ブロック終わりの空行
        
    return type_str, on_c, core_g, data, definition_type, b_gates_1, b_gates_2, initial_islands

TECH_TYPE_STRENGTHS = {
    "Generator": "持続可能なメインエンジン稼働。\n反復タスクによるシステム最適化と、外部トリガーに対する高いレスポンス性能。",
    "Manifesting Generator": "マルチスレッド処理による高速展開。\nプロセスをスキップし最適解を見つけるアジャイル開発的な機動力。",
    "Manifestor": "システム起動のイニシアチブ（実行権限）。\nゼロからの要件定義と、他リソースを稼働させるAPIトリガー発火。",
    "Projector": "システム全体のアーキテクチャ俯瞰。\nリソースの効率的なアロケーションと、他プロセスのデバッグ・チューニング。",
    "Reflector": "環境データ全体のサンプリング。\nシステムの健全性モニタリングと、バイアスなしのフラットな評価。"
}
TECH_CENTER_STRENGTHS = {
    "Head": "新規クエリ発行", "Ajna": "データ解析・モデリング",
    "Throat": "外部システムへのデプロイ", "G": "一貫したルーティング",
    "Heart": "リソースの確約とトランザクション", "Sacral": "高可用性のベースエンジン",
    "Splenic": "リアルタイムのセキュリティ検知", "SolarPlexus": "ディープラーニング",
    "Root": "バッチ実行と圧力"
}
TECH_LINE_MEANINGS = {
    1: "基盤検証・インフラ構築", 2: "独自アルゴリズム", 3: "アジャイル・テスト",
    4: "ネットワーク・API連携", 5: "ソリューション提供", 6: "システム監査・モデリング"
}

def print_tech_spec_report(type_str, on_centers, gates, data, def_type, b_gates_1, b_gates_2, islands):
    print(DIVIDER)
    print("💻 SYSTEM SPECIFICATION REPORT")
    print("   個人ハードウェア＆OS仕様書")
    print(DIVIDER)
    
    print(f"\n[OS特性]: {type_str}")
    print(f" └ 強み: {TECH_TYPE_STRENGTHS.get(type_str, '未定義')}")
    
    print("\n[アクティブなハードウェアモジュール]")
    if not on_centers: print(" └ すべてのモジュールがクラウド処理として機能。")
    for center in on_centers:
        print(f" └ {CENTER_JP.get(center, center)}: {TECH_CENTER_STRENGTHS.get(center, '')}")
    
    print("\n[システム統合パッチ (ミッシングゲート)]")
    print(f"構成: {def_type}")
    
    if len(islands) <= 1:
        print("🌟 ブリッジ: なし (単一ネットワーク統合済み)")
    else:
        if b_gates_1:
            bg_list = sorted(list(set(b_gates_1)))
            print(f"🌟 統合ブリッジ: {bg_list}")
            for g in bg_list:
                print(f"  - Gate {g:>2} 接続時: 通信ロス消滅、シームレス化。")
        elif b_gates_2:
            combo_strs = [f"[{bg1}, {bg2}]" for bg1, bg2 in b_gates_2]
            print(f"🌟 ワイド統合ブリッジ:\n   {', '.join(combo_strs)}")

    red_counts = {i: 0 for i in range(1, 7)}
    black_counts = {i: 0 for i in range(1, 7)}
    for d in data:
        if d["planet"] != "Chiron":
            if d["color"] == "Red": red_counts[d["line"]] += 1
            else: black_counts[d["line"]] += 1
            
    print("\n[レイヤー別実装割合 (ラインの構成数)]")
    print("Line | <span style='color:#FF4B4B;'>赤</span> | 黒 | 計 | 役割メタファー")
    print("-" * 35)
    for i in range(1, 7):
        tot = red_counts[i] + black_counts[i]
        print(f" L{i}  | <span style='color:#FF4B4B;'>{red_counts[i]:>2}</span> | {black_counts[i]:>2} | {tot:>2} | {TECH_LINE_MEANINGS[i]}")

    p_sun = next(d for d in data if d["planet"] == "Sun" and d["color"] == "Black")
    d_sun = next(d for d in data if d["planet"] == "Sun" and d["color"] == "Red")
    profile = f"{p_sun['line']}/{d_sun['line']}"
    
    print(f"\n[メイン・プロセス]")
    print(f" プロファイル: {profile}")
    print(f" 太陽ゲート  : {p_sun['gate']}")

    all_centers = set(CENTER_GATES.keys())
    off_centers = all_centers - set(on_centers)
    full_open = [c for c in off_centers if len(CENTER_GATES[c] & set(gates)) == 0]
    undefined = [c for c in off_centers if len(CENTER_GATES[c] & set(gates)) > 0]
    
    print("\n[セキュリティ・脆弱性診断 (Not-self)]")
    if not full_open and not undefined:
        print("  該当なし")
    for c in full_open: print(f"  ■ {CENTER_JP.get(c, c)} (フルオープン)\n    DDoS攻撃注意。")
    for c in undefined: print(f"  □ {CENTER_JP.get(c, c)} (未定義)\n    ダミープロセス発火注意。")

# =====================================================================
# ▼▼▼ 5. 実行ボタンと表示用ラッパー ▼▼▼
# =====================================================================
if st.sidebar.button("🚀 システム解析を実行"):
    with st.spinner("システム仕様書を生成中..."):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
            type_str, on_c, core_g, full_data, def_type, b_gates_1, b_gates_2, islands = print_master_report(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE)
            print_tech_spec_report(type_str, on_c, core_g, full_data, def_type, b_gates_1, b_gates_2, islands)

        html_content = f.getvalue()
wrapped_html = f"""
        <div style="
            background-color: #1E1E1E; 
            color: #D4D4D4; 
            padding: 1.5rem; 
            border-radius: 0.5rem; 
            font-family: monospace; 
            white-space: pre-wrap; 
            word-wrap: break-word; 
            line-height: 1.6;
            overflow-x: hidden;
        ">
{html_content}
        </div>
        """
        st.markdown(wrapped_html, unsafe_allow_html=True)
        st.success("解析完了！")
