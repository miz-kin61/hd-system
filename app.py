# =====================================================================
# タイトル: HD自作エンジン Webアプリ版 (Ver 3.5 臓器相関データ搭載・最終完全版)
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
# ▼▼▼ 1. 画面・見た目の設定 ▼▼▼
# =====================================================================
st.set_page_config(page_title="体質診断レポート", page_icon="🏥", layout="wide")

DIVIDER = "-" * 35

PLANET_ORDER = [
    "Sun", "Earth", "Moon", "NorthNode", "SouthNode",
    "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron"
]

PLANET_JP = {
    "Sun": "太陽", "Earth": "地球", "Moon": "月",
    "NorthNode": "北の星（ノースノード）", "SouthNode": "南の星（サウスノード）",
    "Mercury": "水星", "Venus": "金星", "Mars": "火星",
    "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星",
    "Neptune": "海王星", "Pluto": "冥王星", "Chiron": "キロン"
}

st.markdown("""
<style>
pre {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("### 🏥 体質・生命力 診断レポート")
st.markdown("<span style='font-size: 0.9em; color: gray;'>生まれ持った体の仕組みと、心身のエネルギーの流れを読み解きます。</span>", unsafe_allow_html=True)

# =====================================================================
# ▼▼▼ 2. 左側メニュー: 情報の入力欄 ▼▼▼
# =====================================================================
st.sidebar.header("▼ 生年月日の入力 (日本時間)")

input_date = st.sidebar.date_input("生年月日", datetime.date(2002,12, 16))

st.sidebar.markdown("生まれた時刻")
col1, col2 = st.sidebar.columns(2)
HOUR = col1.selectbox("時", range(24), index=12)
MINUTE = col2.selectbox("分", range(60), index=30)

YEAR = input_date.year
MONTH = input_date.month
DAY = input_date.day

# =====================================================================
# ▼▼▼ 3. 各種データ・辞書の定義 ▼▼▼
# =====================================================================
CUSTOM_WEIGHTS = {
    "Sun": 35.0, "Earth": 35.0, "Moon": 10.0, "Mercury": 4.5, "Venus": 4.0,
    "Mars": 3.5, "Jupiter": 3.0, "Saturn": 2.0, "Uranus": 1.5, "Neptune": 1.0, "Pluto": 0.5,
    "NorthNode": 0.0, "SouthNode": 0.0, "Chiron": 0.0
}
DORMANT_MULTIPLIER = 0.3
FORCED_GATES = set()

GATE_SEQUENCE = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]

CENTER_GATES = {
    "頭脳": {64, 61, 63}, "思考": {47, 24, 4, 17, 43, 11}, "表現": {62, 23, 56, 31, 8, 33, 20, 16, 35, 12, 45},
    "自己": {7, 1, 13, 25, 46, 2, 15, 10}, "意志": {21, 51, 26, 40}, "生命力": {34, 5, 14, 29, 59, 9, 3, 42, 27},
    "直感": {48, 57, 44, 50, 32, 28, 18}, "感情": {36, 22, 37, 6, 49, 55, 30}, "活力": {58, 38, 54, 53, 60, 52, 19, 39, 41}
}

# センター名の旧キー（内部処理用）→ 新しい日本語名への対応
CENTER_KEY_MAP = {
    "Head": "頭脳", "Ajna": "思考", "Throat": "表現", "G": "自己",
    "Heart": "意志", "Sacral": "生命力", "Splenic": "直感", "SolarPlexus": "感情", "Root": "活力"
}
CENTER_KEY_REVERSE = {v: k for k, v in CENTER_KEY_MAP.items()}

MOTOR_CENTERS = {"生命力", "意志", "感情", "活力"}

# 各中枢に対応する身体の臓器・部位
CENTER_ORGANS = {
    "頭脳": "松果体",
    "思考": "脳下垂体",
    "表現": "甲状腺・副甲状腺",
    "自己": "肝臓・血液",
    "意志": "心臓・胸腺・胆嚢",
    "生命力": "卵巣・精巣",
    "直感": "脾臓・リンパ系",
    "感情": "膵臓・腎臓・神経系",
    "活力": "副腎"
}

CHANNELS = {
    "頭脳_思考": [(64,47,"64-47"), (61,24,"61-24"), (63,4,"63-4")],
    "思考_表現": [(17,62,"17-62"), (43,23,"43-23"), (11,56,"11-56")],
    "表現_自己": [(31,7,"31-7"), (8,1,"8-1"), (33,13,"33-13"), (10,20,"10-20")],
    "表現_意志": [(45,21,"45-21")],
    "表現_感情": [(35,36,"35-36"), (12,22,"12-22")],
    "表現_直感": [(16,48,"16-48"), (20,57,"20-57")],
    "表現_生命力": [(20,34,"20-34")],
    "自己_意志": [(25,51,"25-51")],
    "自己_生命力": [(5,15,"5-15"), (46,29,"46-29"), (2,14,"2-14"), (10,34,"10-34")],
    "自己_直感": [(10,57,"10-57")],
    "意志_感情": [(40,37,"40-37")],
    "意志_直感": [(26,44,"26-44")],
    "生命力_感情": [(6,59,"6-59")],
    "生命力_直感": [(50,27,"50-27"), (34,57,"34-57")],
    "生命力_活力": [(53,42,"53-42"), (3,60,"3-60"), (9,52,"9-52")],
    "感情_活力": [(19,49,"19-49"), (39,55,"39-55"), (41,30,"41-30")],
    "直感_活力": [(18,58,"18-58"), (28,38,"28-38"), (32,54,"32-54")]
}

# 全64の扉（ゲート）の意味 ― 身体・健康診断のことば
GATE_TECH_MEANINGS = {
    1:  "【創造】 独自の生命表現を生み出す力",
    2:  "【受容】 必要なものを自然に引き寄せる磁力",
    3:  "【秩序】 混乱した状態を整え形にする力",
    4:  "【答え】 不調の原因を論理的に見つける力",
    5:  "【待機】 安定したリズムで体を動かす力",
    6:  "【摩擦】 ぶつかりながら境界線を整える力",
    7:  "【役割】 未来の体の在り方を設計する力",
    8:  "【貢献】 独自のビジョンを外へ伝える力",
    9:  "【集中】 細部まで丁寧に注意を向ける力",
    10: "【自己行動】 自分らしさを土台にした生き方",
    11: "【思想】 無数のアイデアを心の中で育てる力",
    12: "【慎重】 適切なタイミングで言葉を発する力",
    13: "【聞く】 過去の記憶を丁寧に聞き取る力",
    14: "【技術】 豊かさを大きく広げる増幅の力",
    15: "【柔軟】 さまざまな環境に自然に溶け込む力",
    16: "【練習】 繰り返しによって精度を高める力",
    17: "【意見】 筋道立てて物事を組み立てる力",
    18: "【修正】 既存の仕組みの問題を見つけ直す力",
    19: "【感知】 必要な環境を察知する感受性",
    20: "【今】 今この瞬間の状況を的確に伝える力",
    21: "【統制】 資源を中心で束ねて管理する力",
    22: "【開放】 感情を優雅に外へ表現する力",
    23: "【同化】 複雑なものをシンプルに伝える力",
    24: "【帰還】 繰り返し内省して最善解を見つける力",
    25: "【純粋な愛】 見返りを求めない愛を広げる力",
    26: "【効率】 少ない力で大きな成果を引き出す力",
    27: "【養育】 他者の体と心を整え支える力",
    28: "【挑戦】 限界まで試して突き抜ける力",
    29: "【肯定】 全力で取り組み完遂する力",
    30: "【体験】 新しい体験への入口を開く力",
    31: "【影響力】 論理的に周囲を導くリーダーの力",
    32: "【継続】 長く受け継がれてきた価値を守る力",
    33: "【振り返り】 過去の記録を整理し蓄える力",
    34: "【力】 自立して動く主エネルギーの馬力",
    35: "【変化】 新しい体験を積み重ねて前進する力",
    36: "【危機突破】 未知の困難を乗り越えて処理する力",
    37: "【絆】 共同体の中で資源を分かち合う力",
    38: "【抵抗】 目的を守るための粘り強い防衛力",
    39: "【刺激】 停滞を突き動かして変化を促す力",
    40: "【孤独】 一人の時間で体を回復させる力",
    41: "【始まり】 新しい取り組みの最初の一歩",
    42: "【完成】 始まったことを最後まで育てる力",
    43: "【洞察】 突然ひらめく独創的な気づきの力",
    44: "【警戒】 過去の記憶から危険を読み取る力",
    45: "【まとめ役】 資源を集め管理する力",
    46: "【体との一致】 物理的な環境と完全に同調する力",
    47: "【解析】 過去の経験に意味を見出す力",
    48: "【深い知恵】 蓄積された知識の奥から引き出す力",
    49: "【刷新】 不要な関係を断ち切り作り直す力",
    50: "【価値観】 全体の安全を守る共通の規範",
    51: "【衝撃】 驚きによって体と心を再起動させる力",
    52: "【静止】 深く集中するための静止の力",
    53: "【開始】 新しい取り組みを動かし始める力",
    54: "【向上心】 上の段階へ自らを押し上げる力",
    55: "【豊かさ】 感情の波を通じて豊かさを育てる力",
    56: "【語り】 体験を物語にして届ける力",
    57: "【直感】 今この瞬間の危険を即座に察知する力",
    58: "【生きがい】 体を整え続ける持続的な生命力",
    59: "【親密さ】 心の壁を越えてつながる力",
    60: "【制限の中で生きる】 制約の中で確実に前進する力",
    61: "【神秘】 未知の真理へ触れようとする力",
    62: "【細部】 細かいところまで正確に記述する力",
    63: "【問い】 論理的な矛盾を見つけ問い直す力",
    64: "【混沌の整理】 整理されていない記憶を受け止める力"
}

# =====================================================================
# ▼▼▼ 4. 天文暦のセットアップ ▼▼▼
# =====================================================================
ephe_dir = './ephe_data'
os.makedirs(ephe_dir, exist_ok=True)
files = ['sepl_18.se1', 'semo_18.se1', 'seas_18.se1']
base_url = 'https://github.com/aloistr/swisseph/raw/master/ephe/'
for f in files:
    if not os.path.exists(os.path.join(ephe_dir, f)):
        urllib.request.urlretrieve(base_url + f, os.path.join(ephe_dir, f))
swe.set_ephe_path(ephe_dir)

# =====================================================================
# ▼▼▼ 5. 計算・出力のロジック ▼▼▼
# =====================================================================
def get_gate_and_line(lon):
    offset = (lon - 302.0 + 360.0) % 360.0
    return GATE_SEQUENCE[int(offset / 5.625)], int((offset % 5.625) / (5.625 / 6)) + 1

def calculate_design_jd(jd_b, sun_lon):
    target = (sun_lon - 88.0 + 360.0) % 360.0
    jd_guess = jd_b - 89.5
    for _ in range(20):
        pos, _ = swe.calc_ut(jd_guess, swe.SUN)
        diff = (pos[0] - target + 360.0) % 360.0
        if diff > 180: diff -= 360.0
        jd_guess -= diff / 0.9856
        if abs(diff) < 0.00001: break
    return jd_guess

def get_chart_data(y, m, d, h, mi):
    utc = datetime.datetime(y, m, d, h, mi) - datetime.timedelta(hours=9)
    jd_b = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60.0)
    sun_pos, _ = swe.calc_ut(jd_b, swe.SUN)
    jd_d = calculate_design_jd(jd_b, sun_pos[0])
    data = []
    planets = {
        swe.SUN: "Sun", swe.MOON: "Moon", swe.TRUE_NODE: "NorthNode",
        swe.MERCURY: "Mercury", swe.VENUS: "Venus", swe.MARS: "Mars",
        swe.JUPITER: "Jupiter", swe.SATURN: "Saturn", swe.URANUS: "Uranus",
        swe.NEPTUNE: "Neptune", swe.PLUTO: "Pluto", swe.CHIRON: "Chiron"
    }
    for is_red, jd in [(True, jd_d), (False, jd_b)]:
        col = "Red" if is_red else "Black"
        for p_id, p_name in planets.items():
            pos, _ = swe.calc_ut(jd, p_id)
            g, l = get_gate_and_line(pos[0])
            data.append({"planet": p_name, "color": col, "gate": g, "line": l})
            if p_name == "Sun":
                eg, el = get_gate_and_line((pos[0] + 180) % 360)
                data.append({"planet": "Earth", "color": col, "gate": eg, "line": el})
            if p_name == "NorthNode":
                sg, sl = get_gate_and_line((pos[0] + 180) % 360)
                data.append({"planet": "SouthNode", "color": col, "gate": sg, "line": sl})
    return data, jd_d

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

def print_master_report(data, jd_d, y, m, d, h, mi):
    dv = swe.revjul(jd_d)
    dj = datetime.datetime(int(dv[0]), int(dv[1]), int(dv[2]), int(dv[3]), int((dv[3] % 1) * 60)) + datetime.timedelta(hours=9)
    print(f"意識（後天）: {y}/{m}/{d} {h:02d}:{mi:02d}\n<span style='color:#FF4B4B; font-weight:bold;'>身体（先天）: {dj.strftime('%Y/%m/%d %H:%M')} (日本時間)</span>\n")

    core_g = set([x["gate"] for x in data if x["planet"] != "Chiron"]) | FORCED_GATES

    initial_on_c = get_defined_centers(core_g)
    initial_islands = get_islands_for_gates(core_g, initial_on_c)
    on_c = initial_on_c

    if len(initial_islands) == 0:
        definition_type = "全感受型（レフレクター）"
    elif len(initial_islands) == 1:
        definition_type = "一体型（シングル定義）"
    elif len(initial_islands) == 2:
        definition_type = "二系統型（スプリット定義）"
    elif len(initial_islands) == 3:
        definition_type = "三系統型（トリプルスプリット）"
    else:
        definition_type = "四系統型（クアドスプリット）"

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
                for j in range(i + 1, len(missing)):
                    g1, g2 = missing[i], missing[j]
                    test_gates = core_g | {g1, g2}
                    test_on_c = get_defined_centers(test_gates)
                    if len(test_on_c) == len(initial_on_c):
                        test_islands = get_islands_for_gates(test_gates, test_on_c)
                        if len(test_islands) > 0 and len(test_islands) < len(initial_islands):
                            b_gates_2.append((min(g1, g2), max(g1, g2)))

    motor_to_throat = False
    connected_motors = set()
    if "表現" in on_c:
        adj = collections.defaultdict(list)
        for r, cs in CHANNELS.items():
            c1, c2 = r.split('_')
            for g1, g2, cid in cs:
                if g1 in core_g and g2 in core_g:
                    adj[c1].append(c2)
                    adj[c2].append(c1)

        v_throat = set()
        queue = ["表現"]
        while queue:
            curr = queue.pop(0)
            if curr not in v_throat:
                v_throat.add(curr)
                if curr in MOTOR_CENTERS:
                    motor_to_throat = True
                    connected_motors.add(curr)
                queue.extend([n for n in adj[curr] if n not in v_throat])

    if "生命力" in on_c:
        type_str = "表現する生命型（マニフェスティング・ジェネレーター）" if motor_to_throat else "生命力型（ジェネレーター）"
    else:
        if motor_to_throat:
            type_str = "行動開始型（マニフェスター）"
        elif len(on_c) > 0:
            type_str = "導き型（プロジェクター）"
        else:
            type_str = "反射型（レフレクター）"

    def calc_gate_score(gate, planet):
        c = next((k for k, v in CENTER_GATES.items() if gate in v), None)
        if c in MOTOR_CENTERS:
            return (CUSTOM_WEIGHTS.get(planet, 0) / 2.0) * (1.0 if c in on_c else DORMANT_MULTIPLIER)
        return 0.0

    raw_s = sum([calc_gate_score(x["gate"], x["planet"]) for x in data if x["planet"] != "Chiron"])

    print(DIVIDER)
    print(f"🔋 自発エネルギー密度: {raw_s:.1f}")
    if connected_motors:
        motors_jp = "・".join(connected_motors)
        print(f"💡 表現と連動している活力の源: {motors_jp}")
    print(DIVIDER)

    for p in PLANET_ORDER:
        r = next((x for x in data if x["planet"] == p and x["color"] == "Red"), None)
        b = next((x for x in data if x["planet"] == p and x["color"] == "Black"), None)
        if r and b:
            rs = calc_gate_score(r["gate"], p) if p != "Chiron" else 0.0
            bs = calc_gate_score(b["gate"], p) if p != "Chiron" else 0.0

            r_sc = f" [{rs:>4.1f}]" if rs > 0 else "       "
            b_sc = f" [{bs:>4.1f}]" if bs > 0 else "       "

            p_jp = PLANET_JP.get(p, p)

            print(f"{p_jp}")
            print(f"<span style='color:#FF4B4B;'>先天 {r['gate']:>2}.{r['line']}{r_sc}</span> ║ 後天 {b['gate']:>2}.{b['line']}{b_sc}\n")

    print(DIVIDER)
    print("🏥 身体の中枢別 エネルギー状態（扉の詳細）")
    print(DIVIDER)
    center_order = ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]
    for c in center_order:
        c_gates = []
        c_score = 0.0
        status = "活性化している" if c in on_c else "感受性が高い（外から影響を受けやすい）"
        for x in data:
            if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]:
                s = calc_gate_score(x["gate"], x["planet"])
                c_score += s
                c_gates.append((x["gate"], x["line"], x["planet"], x["color"], s))

        print(f"■ {c}（{CENTER_ORGANS[c]}）")
        print(f"{status}  [小計: {c_score:.1f}]")

        if not c_gates:
            print("ー 該当する扉なし\n")
        else:
            c_gates_sorted = sorted(c_gates, key=lambda x: x[0])
            for g, line, p, col, s in c_gates_sorted:
                score_str = f" [{s:>4.1f}]" if s > 0 else ""
                p_jp = PLANET_JP.get(p, p)
                mean_str = GATE_TECH_MEANINGS.get(g, "")

                if col == "Red":
                    print(f"ー <span style='color:#FF4B4B;'>扉 {g:>2}.{line} {mean_str} ({p_jp}/先天){score_str}</span>")
                else:
                    print(f"ー 扉 {g:>2}.{line} {mean_str} ({p_jp}/後天){score_str}")
            print("")

    return type_str, on_c, core_g, data, definition_type, b_gates_1, b_gates_2, initial_islands


# 体質タイプ別の特徴
TECH_TYPE_STRENGTHS = {
    "生命力型（ジェネレーター）": "安定した生命力を持ち続けるエンジン体質。\n繰り返しの積み重ねで体と心を最高の状態へ整え、外からの呼びかけへの反応力が高い。",
    "表現する生命型（マニフェスティング・ジェネレーター）": "複数のことを同時にこなす多機能型の体質。\n試行錯誤しながら最短の道を直感で見つける、素早い行動力を持つ。",
    "行動開始型（マニフェスター）": "自分から新しいことを始める力（主導権）がある体質。\nゼロから道を切り開き、他者を動かす働きかけができる。",
    "導き型（プロジェクター）": "全体の流れを高い視点から見渡せる体質。\nエネルギーを効率よく使い、他者の状態を整えることが得意。",
    "反射型（レフレクター）": "周囲の環境全体を映し出すセンサー体質。\n偏りなく全体の健康状態を感じ取り、公平に判断できる。"
}

TECH_CENTER_STRENGTHS = {
    "頭脳": "新しい問いを受け取る力", "思考": "情報を整理して理解する力",
    "表現": "外へ向けて言葉や行動を出す力", "自己": "ぶれない方向感覚",
    "意志": "やると決めたことを貫く力", "生命力": "底をつかない活力の源",
    "直感": "その場その場の安全を察知する力", "感情": "感情を深く感じて育てる力",
    "活力": "圧力をエネルギーに変える力"
}

TECH_LINE_MEANINGS = {
    1: "土台づくり・基礎固め", 2: "生まれ持った独自の才能",
    3: "試して学ぶ・実践型", 4: "人とのつながり・縁",
    5: "問題を解決する力", 6: "全体を見渡して整える力"
}

CENTER_ISSUES = {
    "頭脳": {
        "curse": "【外から植えつけられた思い込み】「いつも明確なビジョンを持て」「自分で考えろ」\n └ 他人の疑問（余計な心配ごと）を自分のことのように抱え込み、頭が疲れ果ててしまう。",
        "truth": "【本来の体の仕組み】必要な気づきだけを受け取れる「感度の高いアンテナ」。",
        "solution": "【心身を整えるための言葉】「その悩みは、私が引き受けることではありません」"
    },
    "思考": {
        "curse": "【外から植えつけられた思い込み】「一貫性を持て」「意見をころころ変えるな」\n └ 一度出した答えに無理やり縛られ、本来の柔軟な思考が固まってしまう。",
        "truth": "【本来の体の仕組み】新しい考えをどんどん取り入れられる「柔軟な思考の器」。",
        "solution": "【心身を整えるための言葉】「昨日の私と今日の私は、成長した別の私です」"
    },
    "表現": {
        "curse": "【外から植えつけられた思い込み】「自分から発言しろ」「沈黙は気まずい」\n └ 沈黙を恐れて無理に言葉を出し続け、心身が空回りしてしまう。",
        "truth": "【本来の体の仕組み】外から求められたときに最大の力を発揮する「待機型の声」。",
        "solution": "【心身を整えるための言葉】「呼ばれるまで、静かに待っているのが私の自然な状態です」"
    },
    "自己": {
        "curse": "【外から植えつけられた思い込み】「自分探しをしろ」「確固たる自分を持て」\n └ 固定した「本当の自分」を探し続けて迷い、心が落ち着かなくなる。",
        "truth": "【本来の体の仕組み】いる場所や出会う人に応じて自然に向きを変える「羅針盤」。",
        "solution": "【心身を整えるための言葉】「私は環境によって変わっていい。それが私らしさです」"
    },
    "意志": {
        "curse": "【外から植えつけられた思い込み】「約束は必ず守れ」「努力して価値を証明しろ」\n └ 体の限界を超えてまで頑張り続け、心臓や胆嚢に負担をかけてしまう。",
        "truth": "【本来の体の仕組み】自分の価値を証明し続けなくていい「無重力の心」。",
        "solution": "【心身を整えるための言葉】「証明すべきことは何もない。体が無理だと言ったら止めていい」"
    },
    "生命力": {
        "curse": "【外から植えつけられた思い込み】「途中で投げ出すな」「周りが働いているのに休むな」\n └ 他人のペースに引きずられ、休むべきタイミングを見失って疲れ果ててしまう。",
        "truth": "【本来の体の仕組み】必要な分だけ力を出して、用が済んだらすっと手放せる「充電不要な電池」。",
        "solution": "【心身を整えるための言葉】「今日分の力は使い切った。体が止まれと言う前に、先に休む」"
    },
    "直感": {
        "curse": "【外から植えつけられた思い込み】「石の上にも三年」「手放すのはもったいない」\n └ 「今離れると怖い」という古い恐れに縛られ、体や心に合わない環境に居続けてしまう。",
        "truth": "【本来の体の仕組み】違和感を感じたら、過去に縛られずすぐに離れられる「体の警報装置」。",
        "solution": "【心身を整えるための言葉】「なんとなく嫌な感じがする場所・人とは、すぐ距離を置いていい」"
    },
    "感情": {
        "curse": "【外から植えつけられた思い込み】「空気を読め」「感情的になるな」\n └ 衝突を恐れるあまり、自分の気持ちを押し込めて「いい人」を演じ続け、内側が疲弊する。",
        "truth": "【本来の体の仕組み】他者の感情の波を感じながら、そっと観察できる「共感の受信機」。",
        "solution": "【心身を整えるための言葉】「この感情の波は、誰かのもの。私はただ感じているだけでいい」"
    },
    "活力": {
        "curse": "【外から植えつけられた思い込み】「早く終わらせろ」「やることを溜めるな」\n └ 外からのプレッシャーで常に焦らされ、体が休まらなくなってしまう。",
        "truth": "【本来の体の仕組み】外からのせかしをやり過ごし、自分のペースで動ける「独立した活力の源」。",
        "solution": "【心身を整えるための言葉】「急いでも物事は変わらない。他人の焦りは受け取らなくていい」"
    }
}

DEFINED_CENTER_ISSUES = {
    "頭脳": {
        "curse": "【外から植えつけられた思い込み】「他人の悩みにも関心を持て」「もっと周りを見ろ」\n └ 自分には関係のない心配ごとまで引き受けようとして、本来の閃きが妨げられてしまう。",
        "truth": "【本来の体の仕組み】自分に必要な気づきだけをピンポイントで受け取る「専用の受信機」。",
        "solution": "【心身を整えるための言葉】「他人の悩みを自分の中に入れない。興味のないことは受け取らなくていい」"
    },
    "思考": {
        "curse": "【外から植えつけられた思い込み】「もっと柔軟になれ」「頑固は悪いことだ」\n └ 自分の確かな思考プロセスを否定し、無理に他人に合わせようとして判断が狂ってしまう。",
        "truth": "【本来の体の仕組み】一定のやり方で確実に情報を処理する「安定した思考の仕組み」。",
        "solution": "【心身を整えるための言葉】「私の考え方は生まれつきの仕様。同調せずに、自分の見解として伝えればいい」"
    },
    "表現": {
        "curse": "【外から植えつけられた思い込み】「もっと言葉を選べ」「言い方がきつい」\n └ 安定した自分の表現方法を無理に変えようとして、全身にストレスがかかってしまう。",
        "truth": "【本来の体の仕組み】自分のスタイルで確かに言葉を出せる「生まれつきの表現の出口」。",
        "solution": "【心身を整えるための言葉】「この伝え方が私の自然な声。変える必要はありません」"
    },
    "自己": {
        "curse": "【外から植えつけられた思い込み】「相手に合わせなさい」「協調性を持て」\n └ 本来安定している自分の軸を無理に変えようとして、自分が何者かわからなくなってしまう。",
        "truth": "【本来の体の仕組み】自分を中心に、合う人・環境を引き寄せる「固定された羅針盤」。",
        "solution": "【心身を整えるための言葉】「私は動かない。私に合う人だけが自然に近づいてくる」"
    },
    "意志": {
        "curse": "【外から植えつけられた思い込み】「謙虚であれ」「お金を求めるのははしたない」\n └ 自分の価値を安売りして正当な見返りを受け取らず、心身の基盤がすり減ってしまう。",
        "truth": "【本来の体の仕組み】確固たる意志で約束を果たし、正当な対価を受け取る権利がある「本格稼働の体」。",
        "solution": "【心身を整えるための言葉】「安売りは体の消耗につながる。自分の価値を認め、堂々と対価を求めていい」"
    },
    "生命力": {
        "curse": "【外から植えつけられた思い込み】「頭で考えて計画的に動け」「自分から発信しろ」\n └ 外からの働きかけを待たずに思考で無理に動こうとして、空回りして疲労だけが溜まっていく。",
        "truth": "【本来の体の仕組み】外からの呼びかけに「体が反応した瞬間」だけ、無限の力が湧き出る「反応型の生命力」。",
        "solution": "【心身を整えるための言葉】「頭で考えて動かない。体の奥が反応するまで、静かに待つ」"
    },
    "直感": {
        "curse": "【外から植えつけられた思い込み】「直感だけで動くな」「根拠を出せ」\n └ 瞬間の体の警告を無視して理屈を探し、結局タイミングを逃して危険な目に遭う。",
        "truth": "【本来の体の仕組み】今この瞬間の正解を、理由なく一瞬で知らせる「超高速の体の警報」。",
        "solution": "【心身を整えるための言葉】「なんとなく嫌だから、そうする。理由は後からでいい」"
    },
    "感情": {
        "curse": "【外から植えつけられた思い込み】「すぐ決断しろ！」「チャンスを逃すな、今すぐ決めろ！」\n └ 感情の高ぶりや落ち込みのどん底で焦って決めてしまい、後から大きく後悔することになる。",
        "truth": "【本来の体の仕組み】時間をかけるほど本当の答えがはっきり見えてくる「熟成型の決断力」。",
        "solution": "【心身を整えるための言葉】「素晴らしいお話ですね。数日ゆっくり考えてからお返事します」"
    },
    "活力": {
        "curse": "【外から植えつけられた思い込み】「自分のペースでゆっくりやれ」「焦らなくていい」\n └ 本来持っている「プレッシャーを力に変える機能」を抑えられ、本来の爆発力が出せない。",
        "truth": "【本来の体の仕組み】自らプレッシャーを生み出し、一気に物事を処理する「瞬発力型の活力」。",
        "solution": "【心身を整えるための言葉】「私はぎりぎりの方が燃える。プレッシャーは私の力の源です」"
    }
}

PROFILE_TECH_MEANINGS = {
    "1/3": "【探求と実践の人】 基礎をしっかり学んで（1）、試行錯誤で体当たりしながら（3）前進する実力派。",
    "1/4": "【知識と縁の人】 深い知識を積み上げて（1）、信頼できる身近な縁（4）を通じてその力を広げる。",
    "2/4": "【才能と縁の人】 生まれ持った独自の才能（2）を持ち、信頼できるつながり（4）の中だけで開花させる。",
    "2/5": "【天才と解決の人】 天性の直感的な力（2）を持ち、外からの助けを求める声（5）に応えて問題を解決する。",
    "3/5": "【実践と解決の人】 失敗と衝突（3）から実践的な答えを見つけ出し、周囲の困りごとを解決する（5）。",
    "3/6": "【実践から全体へ移行する人】 前半の人生は試して失敗（3）を繰り返し、後半は全体を高い視座（6）から設計する人へと変わる。",
    "4/6": "【縁とモデルの人】 人とのつながり（4）を育みながら、高い視点（6）から全体の健康を見守る。",
    "4/1": "【伝道と知識の人】 深い人脈（4）を土台に、揺るぎない基礎知識（1）を周囲へ伝えていく。",
    "5/1": "【解決と基礎の人】 確かな知識（1）を土台に、期待に完璧な答えで応える（5）頼られる人。",
    "5/2": "【解決と才能の人】 普段は目立たない（2）が、いざとなると天才的な一手（5）で問題を解決する職人。",
    "6/2": "【全体と才能の人】 生まれ持った才能（2）を持ちながら、全体の流れを俯瞰（6）して整える監督役。",
    "6/3": "【全体と実践の人】 自ら困難に飛び込み（3）ながら、どこか俯瞰した目（6）で限界を見極め続ける探求者。"
}

def print_tech_spec_report(type_str, on_centers, gates, data, def_type, b_gates_1, b_gates_2, islands):
    print(DIVIDER)
    print("🏥 体質・生命力 診断レポート")
    print("   生まれ持った体の仕組みと心身の特性")
    print(DIVIDER)

    print(f"\n【体質タイプ】: {type_str}")
    print(f" └ 特徴: {TECH_TYPE_STRENGTHS.get(type_str, '解析中')}")

    print("\n【活性化している中枢（エネルギーが安定して流れている部位）】")
    if not on_centers:
        print(" └ すべての中枢が外からの影響を受けやすい状態です。")
    for center in on_centers:
        print(f" └ {center}（{CENTER_ORGANS.get(center, '')}）: {TECH_CENTER_STRENGTHS.get(center, '')}")

    print("\n【心身の統合状態（つながりの扉）】")
    print(f"構成タイプ: {def_type}")

    if len(islands) <= 1:
        print("🌟 橋渡しの扉: なし（全体がひとつにつながっています）")
    else:
        if b_gates_1:
            bg_list = sorted(list(set(b_gates_1)))
            print(f"🌟 橋渡しの扉: {bg_list}")
            for g in bg_list:
                print(f"  - 扉 {g:>2} が開くと: 心身の断絶が消え、全体がひとつにつながります。")
        elif b_gates_2:
            combo_strs = [f"[{bg1}, {bg2}]" for bg1, bg2 in b_gates_2]
            print(f"🌟 広域の橋渡しの扉:\n   {', '.join(combo_strs)}")

    red_counts = {i: 0 for i in range(1, 7)}
    black_counts = {i: 0 for i in range(1, 7)}
    for d in data:
        if d["planet"] != "Chiron":
            if d["color"] == "Red": red_counts[d["line"]] += 1
            else: black_counts[d["line"]] += 1

    print("\n【層別の構成（各層の扉の数）】")
    print("層 | <span style='color:#FF4B4B;'>先天</span> | 後天 | 合計 | 特性")
    print("-" * 35)
    for i in range(1, 7):
        tot = red_counts[i] + black_counts[i]
        print(f" {i}層 | <span style='color:#FF4B4B;'>{red_counts[i]:>2}</span> | {black_counts[i]:>2} | {tot:>2} | {TECH_LINE_MEANINGS[i]}")

    p_sun = next(d for d in data if d["planet"] == "Sun" and d["color"] == "Black")
    p_earth = next(d for d in data if d["planet"] == "Earth" and d["color"] == "Black")
    d_sun = next(d for d in data if d["planet"] == "Sun" and d["color"] == "Red")
    d_earth = next(d for d in data if d["planet"] == "Earth" and d["color"] == "Red")

    profile = f"{p_sun['line']}/{d_sun['line']}"

    print(f"\n【人生のテーマ（プロファイル）】")
    print(f" 構成: {profile}")
    print(f" └ 特性: {PROFILE_TECH_MEANINGS.get(profile, '解析中...')}")

    print(f"\n【人生の土台（受胎十字）】")
    print(f" └ 後天・太陽（意識の方向）  : 扉 {p_sun['gate']:>2}  {GATE_TECH_MEANINGS.get(p_sun['gate'])}")
    print(f" └ 後天・地球（意識の土台）  : 扉 {p_earth['gate']:>2}  {GATE_TECH_MEANINGS.get(p_earth['gate'])}")
    print(f" └ 先天・太陽（無意識の方向）: 扉 {d_sun['gate']:>2}  {GATE_TECH_MEANINGS.get(d_sun['gate'])}")
    print(f" └ 先天・地球（無意識の土台）: 扉 {d_earth['gate']:>2}  {GATE_TECH_MEANINGS.get(d_earth['gate'])}")

    all_centers = set(CENTER_GATES.keys())
    off_centers = all_centers - set(on_centers)
    full_open = [c for c in off_centers if len(CENTER_GATES[c] & set(gates)) == 0]

    print("\n" + DIVIDER)
    print("🚨 心身の歪み診断（外からの影響による不調と、整えるための言葉）")
    print(DIVIDER)
    if not off_centers and not on_centers:
        print("  すべての中枢が感受性の高い状態です。")

    for c in ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]:
        print(f"\n■ {c}（{CENTER_ORGANS[c]}）")
        if c in off_centers:
            status_text = "完全に感受性が開いている（外の影響を強く受ける）" if c in full_open else "感受性が高い（外から影響を受けやすい）"
            print(f"状態: {status_text}")
            print(f"{CENTER_ISSUES[c]['curse']}")
            print(f"{CENTER_ISSUES[c]['truth']}")
            print(f"🌿 {CENTER_ISSUES[c]['solution']}")
        else:
            print("状態: 活性化している（安定したエネルギーが流れている）")
            if c in DEFINED_CENTER_ISSUES:
                print(f"{DEFINED_CENTER_ISSUES[c]['curse']}")
                print(f"{DEFINED_CENTER_ISSUES[c]['truth']}")
                print(f"🌿 {DEFINED_CENTER_ISSUES[c]['solution']}")
            else:
                print(" （安定したエネルギーの中枢として、正常に働いています）")

# =====================================================================
# ▼▼▼ 6. 実行ボタンと表示 ▼▼▼
# =====================================================================
if st.sidebar.button("🌿 体質診断を開始する"):
    with st.spinner("診断レポートを生成しています..."):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
            type_str, on_c, core_g, full_data, def_type, b_gates_1, b_gates_2, islands = print_master_report(
                c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE
            )
            print_tech_spec_report(type_str, on_c, core_g, full_data, def_type, b_gates_1, b_gates_2, islands)

        html_content = f.getvalue()

        html_style = (
            "background-color: #1E1E1E; color: #D4D4D4; padding: 1.5rem; border-radius: 0.5rem; "
            "font-family: 'Hiragino Kaku Gothic Pro', 'Meiryo', monospace; "
            "white-space: pre-wrap; word-wrap: break-word; line-height: 1.8; overflow-x: hidden;"
        )
        wrapped_html = f"<div style='{html_style}'>\n{html_content}\n</div>"

        st.markdown(wrapped_html, unsafe_allow_html=True)
        st.success("診断が完了しました！")
