# =====================================================================
# タイトル: HD自作エンジン Webアプリ版 (Notself自己採点・連動メーター実装版)
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
st.set_page_config(page_title="体質診断レポート", page_icon="👶", layout="wide", initial_sidebar_state="expanded")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

DIVIDER = "-" * 35

PLANET_ORDER = [
    "Sun", "Earth", "Moon", "NorthNode", "SouthNode",
    "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron"
]

PLANET_JP = {
    "Sun": "太陽", "Earth": "地球", "Moon": "月",
    "NorthNode": "北の交点", "SouthNode": "南の交点",
    "Mercury": "水星", "Venus": "金星", "Mars": "火星",
    "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星",
    "Neptune": "海王星", "Pluto": "冥王星", "Chiron": "キロン"
}

CENTER_ORDER = ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]

st.markdown("### **👶 体質・生命力 診断レポート**")
st.markdown("<span style='font-size: 0.9em; color: gray;'>**生まれ持った体の仕組みと、心身のエネルギーの流れを読み解きます。**</span>", unsafe_allow_html=True)

# =====================================================================
# ▼▼▼ 2. 左側メニュー: 情報の入力欄 ▼▼▼
# =====================================================================
st.sidebar.header("▼ 生年月日の入力 (日本時間)")

input_date = st.sidebar.date_input(
    "生年月日", 
    value=datetime.date(1980, 1, 1),
    min_value=datetime.date(1920, 1, 1),
    max_value=datetime.date.today()
)

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

CENTER_ORGANS = {
    "頭脳": "松果体", "思考": "脳下垂体", "表現": "甲状腺・副甲状腺",
    "自己": "肝臓・血液", "意志": "心臓・胸腺・胆嚢", "生命力": "卵巣・精巣",
    "直感": "脾臓・リンパ系", "感情": "膵臓・腎臓・神経系", "活力": "副腎"
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

GATE_TECH_MEANINGS = {
    1:  "【創造】 独自の生命表現を生み出す力", 2:  "【受容】 必要なものを自然に引き寄せる磁力",
    3:  "【秩序】 混乱した状態を整え形にする力", 4:  "【答え】 不調の原因を論理的に見つける力",
    5:  "【待機】 安定したリズムで体を動かす力", 6:  "【摩擦】 ぶつかりながら境界線を整える力",
    7:  "【役割】 未来の体の在り方を設計する力", 8:  "【貢献】 独自のビジョンを外へ伝える力",
    9:  "【集中】 細部まで丁寧に注意を向ける力", 10: "【自己行動】 自分らしさを土台にした生き方",
    11: "【思想】 無数のアイデアを心の中で育てる力", 12: "【慎重】 適切なタイミングで言葉を発する力",
    13: "【聞く】 過去の記憶を丁寧に聞き取る力", 14: "【技術】 豊かさを大きく広げる増幅の力",
    15: "【柔軟】 さまざまな環境に自然に溶け込む力", 16: "【練習】 繰り返しによって精度を高める力",
    17: "【意見】 筋道立てて物事を組み立てる力", 18: "【修正】 既存の仕組みの問題を見つけ直す力",
    19: "【感知】 必要な環境を察知する感受性", 20: "【今】 今この瞬間の状況を的確に伝える力",
    21: "【統制】 資源を中心で束ねて管理する力", 22: "【開放】 感情を優雅に外へ表現する力",
    23: "【同化】 複雑なものをシンプルに伝える力", 24: "【帰還】 繰り返し内省して最善解を見つける力",
    25: "【純粋な愛】 見返りを求めない愛を広げる力", 26: "【効率】 少ない力で大きな成果を引き出す力",
    27: "【養育】 他者の体と心を整え支える力", 28: "【挑戦】 限界まで試して突き抜ける力",
    29: "【肯定】 全力で取り組み完遂する力", 30: "【体験】 新しい体験への入口を開く力",
    31: "【影響力】 論理的に周囲を導くリーダーの力", 32: "【継続】 長く受け継がれてきた価値を守る力",
    33: "【振り返り】 過去の記録を整理し蓄える力", 34: "【力】 自立して動く主エネルギーの馬力",
    35: "【変化】 新しい体験を積み重ねて前進する力", 36: "【危機突破】 未知の困難を乗り越えて処理する力",
    37: "【絆】 共同体の中で資源を分かち合う力", 38: "【抵抗】 目的を守るための粘り強い防衛力",
    39: "【刺激】 停滞を突き動かして変化を促す力", 40: "【孤独】 一人の時間で体を回復させる力",
    41: "【始まり】 新しい取り組みの最初の一歩", 42: "【完成】 始まったことを最後まで育てる力",
    43: "【洞察】 突然ひらめく独創的な気づきの力", 44: "【警戒】 過去の記憶から危険を読み取る力",
    45: "【まとめ役】 資源を集め管理する力", 46: "【体との一致】 物理的な環境と完全に同調する力",
    47: "【解析】 過去の経験に意味を見出す力", 48: "【深い知恵】 蓄積された知識の奥から引き出す力",
    49: "【刷新】 不要な関係を断ち切り作り直す力", 50: "【価値観】 全体の安全を守る共通の規範",
    51: "【衝撃】 驚きによって体と心を再起動させる力", 52: "【静止】 深く集中するための静止の力",
    53: "【開始】 新しい取り組みを動かし始める力", 54: "【向上心】 上の段階へ自らを押し上げる力",
    55: "【豊かさ】 感情の波を通じて豊かさを育てる力", 56: "【語り】 体験を物語にして届ける力",
    57: "【直感】 今この瞬間の危険を即座に察知する力", 58: "【生きがい】 体を整え続ける持続的な生命力",
    59: "【親密さ】 心の壁を越えてつながる力", 60: "【制限の中で生きる】 制約の中で確実に前進する力",
    61: "【神秘】 未知の真理へ触れようとする力", 62: "【細部】 細かいところまで正確に記述する力",
    63: "【問い】 論理的な矛盾を見つけ問い直す力", 64: "【混沌の整理】 整理されていない記憶を受け止める力"
}

MOTOR_CENTERS = {"生命力", "意志", "感情", "活力"}
LOWER_CENTERS = {"自己", "意志", "生命力", "直感", "感情", "活力"}

TECH_TYPE_STRENGTHS = {
    "生命力型": "安定した生命力を持ち続けるエンジン体質。\n繰り返しの積み重ねで体と心を最高の状態へ整え、外からの呼びかけへの反応力が高い。",
    "表現する生命型": "複数のことを同時にこなす多機能型の体質。\n試行錯誤しながら最短の道を直感で見つける、素早い行動力を持つ。",
    "行動開始型": "自分から新しいことを始める力（主導権）がある体質。\nゼロから道を切り開き、他者を動かす働きかけができる。",
    "導き型": "全体の流れを高い視点から見渡せる体質。\nエネルギーを効率よく使い、他者の状態を整えることが得意。",
    "反射型": "周囲の環境全体を映し出すセンサー体質。\n偏りなく全体の健康状態を感じ取り、公平に判断できる。"
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
        "curse": "🌀 【外から植えつけられた思い込み】「いつも明確なビジョンを持て」「自分で考えろ」",
        "truth": "✨ 【本来の体の仕組み】必要な気づきだけを受け取れる「感度の高いアンテナ」。",
        "solution": "👉 【心身を整えるための言葉】「その悩みは、私が引き受けることではありません」"
    },
    "思考": {
        "curse": "🌀 【外から植えつけられた思い込み】「一貫性を持て」「意見をころころ変えるな」",
        "truth": "✨ 【本来の体の仕組み】新しい考えをどんどん取り入れられる「柔軟な思考の器」。",
        "solution": "👉 【心身を整えるための言葉】「昨日の私と今日の私は、成長した別の私です」"
    },
    "表現": {
        "curse": "🌀 【外から植えつけられた思い込み】「自分から発言しろ」「沈黙は気まずい」",
        "truth": "✨ 【本来の体の仕組み】外から求められたときに最大の力を発揮する「待機型の声」。",
        "solution": "👉 【心身を整えるための言葉】「呼ばれるまで、静かに待っているのが私の自然な状態です」"
    },
    "自己": {
        "curse": "🌀 【外から植えつけられた思い込み】「自分探しをしろ」「確固たる自分を持て」",
        "truth": "✨ 【本来の体の仕組み】いる場所や出会う人に応じて自然に向きを変える「羅針盤」。",
        "solution": "👉 【心身を整えるための言葉】「私は環境によって変わっていい。それが私らしさです」"
    },
    "意志": {
        "curse": "🌀 【外から植えつけられた思い込み】「約束は必ず守れ」「努力して価値を証明しろ」",
        "truth": "✨ 【本来の体の仕組み】自分の価値を証明し続けなくていい「無重力の心」。",
        "solution": "👉 【心身を整えるための言葉】「証明すべきことは何もない。体が無理だと言ったら止めていい」"
    },
    "生命力": {
        "curse": "🌀 【外から植えつけられた思い込み】「途中で投げ出すな」「周りが働いているのに休むな」",
        "truth": "✨ 【本来の体の仕組み】必要な分だけ力を出して、用が済んだらすっと手放せる「充電不要な電池」。",
        "solution": "👉 【心身を整えるための言葉】「今日分の力は使い切った。体が止まれと言う前に、先に休む」"
    },
    "直感": {
        "curse": "🌀 【外から植えつけられた思い込み】「石の上にも三年」「手放すのはもったいない」",
        "truth": "✨ 【本来の体の仕組み】違和感を感じたら、過去に縛られずすぐに離れられる「体の警報装置」。",
        "solution": "👉 【心身を整えるための言葉】「なんとなく嫌な感じがする場所・人とは、すぐ距離を置いていい」"
    },
    "感情": {
        "curse": "🌀 【外から植えつけられた思い込み】「空気を読め」「感情的になるな」",
        "truth": "✨ 【本来の体の仕組み】他者の感情の波を感じながら、そっと観察できる「共感の受信機」。",
        "solution": "👉 【心身を整えるための言葉】「この感情の波は、誰かのもの。私はただ感じているだけでいい」"
    },
    "活力": {
        "curse": "🌀 【外から植えつけられた思い込み】「早く終わらせろ」「やることを溜めるな」",
        "truth": "✨ 【本来の体の仕組み】外からのせかしをやり過ごし、自分のペースで動ける「独立した活力の源」。",
        "solution": "👉 【心身を整えるための言葉】「急いでも物事は変わらない。他人の焦りは受け取らなくていい」"
    }
}

DEFINED_CENTER_ISSUES = {
    "頭脳": {
        "curse": "🌀 【外から植えつけられた思い込み】「他人の悩みにも関心を持て」「もっと周りを見ろ」",
        "truth": "✨ 【本来の体の仕組み】自分に必要な気づきだけをピンポイントで受け取る「専用の受信機」。",
        "solution": "👉 【心身を整えるための言葉】「他人の悩みを自分の中に入れない。興味のないことは受け取らなくていい」"
    },
    "思考": {
        "curse": "🌀 【外から植えつけられた思い込み】「もっと柔軟になれ」「頑固は悪いことだ」",
        "truth": "✨ 【本来の体の仕組み】一定のやり方で確実に情報を処理する「安定した思考の仕組み」。",
        "solution": "👉 【心身を整えるための言葉】「私の考え方は生まれつきの仕様。同調せずに、自分の見解として伝えればいい」"
    },
    "表現": {
        "curse": "🌀 【外から植えつけられた思い込み】「もっと言葉を選べ」「言い方がきつい」",
        "truth": "✨ 【本来の体の仕組み】自分のスタイルで確かに言葉を出せる「生まれつきの表現の出口」。",
        "solution": "👉 【心身を整えるための言葉】「この伝え方が私の自然な声。変える必要はありません」"
    },
    "自己": {
        "curse": "🌀 【外から植えつけられた思い込み】「相手に合わせなさい」「協調性を持て」",
        "truth": "✨ 【本来の体の仕組み】自分を中心に、合う人・環境を引き寄せる「固定された羅針盤」。",
        "solution": "👉 【心身を整えるための言葉】「私は動かない。私に合う人だけが自然に近づいてくる」"
    },
    "意志": {
        "curse": "🌀 【外から植えつけられた思い込み】「謙虚であれ」「お金を求めるのははしたない」",
        "truth": "✨ 【本来の体の仕組み】確固たる意志で約束を果たし、正当な対価を受け取る権利がある「本格稼働の体」。",
        "solution": "👉 【心身を整えるための言葉】「安売りは体の消耗につながる。自分の価値を認め、堂々と対価を求めていい」"
    },
    "生命力": {
        "curse": "🌀 【外から植えつけられた思い込み】「頭で考えて計画的に動け」「自分から発信しろ」",
        "truth": "✨ 【本来の体の仕組み】外からの呼びかけに「体が反応した瞬間」だけ、無限の力が湧き出る「反応型の生命力」。",
        "solution": "👉 【心身を整えるための言葉】「頭で考えて動かない。体の奥が反応するまで、静かに待つ」"
    },
    "直感": {
        "curse": "🌀 【外から植えつけられた思い込み】「直感だけで動くな」「根拠を出せ」",
        "truth": "✨ 【本来の体の仕組み】今この瞬間の正解を、理由なく一瞬で知らせる「超高速の体の警報」。",
        "solution": "👉 【心身を整えるための言葉】「なんとなく嫌だから、そうする。理由は後からでいい」"
    },
    "感情": {
        "curse": "🌀 【外から植えつけられた思い込み】「すぐ決断しろ！」「チャンスを逃すな、今すぐ決めろ！」",
        "truth": "✨ 【本来の体の仕組み】時間をかけるほど本当の答えがはっきり見えてくる「熟成型の決断力」。",
        "solution": "👉 【心身を整えるための言葉】「素晴らしいお話ですね。数日ゆっくり考えてからお返事します」"
    },
    "活力": {
        "curse": "🌀 【外から植えつけられた思い込み】「自分のペースでゆっくりやれ」「焦らなくていい」",
        "truth": "✨ 【本来の体の仕組み】自らプレッシャーを生み出し、一気に物事を処理する「瞬発力型の活力」。",
        "solution": "👉 【心身を整えるための言葉】「私はぎりぎりの方が燃える。プレッシャーは私の力の源です」"
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

# 🌟 計算結果を「辞書データ」として全て返す関数（対話型UIの土台）
def generate_report_data(data, jd_d, y, m, d, h, mi):
    dv = swe.revjul(jd_d)
    dj = datetime.datetime(int(dv[0]), int(dv[1]), int(dv[2]), int(dv[3]), int((dv[3] % 1) * 60)) + datetime.timedelta(hours=9)
    
    core_g = set([x["gate"] for x in data if x["planet"] != "Chiron"]) | FORCED_GATES
    initial_on_c = get_defined_centers(core_g)
    initial_islands = get_islands_for_gates(core_g, initial_on_c)
    on_c = initial_on_c

    energized_centers = set(MOTOR_CENTERS)
    if {25, 51}.issubset(core_g) or {5, 15}.issubset(core_g) or {2, 14}.issubset(core_g) or {29, 46}.issubset(core_g) or {34, 10}.issubset(core_g): energized_centers.add("自己")
    if {18, 58}.issubset(core_g) or {28, 38}.issubset(core_g) or {32, 54}.issubset(core_g) or {34, 57}.issubset(core_g) or {27, 50}.issubset(core_g) or {26, 44}.issubset(core_g): energized_centers.add("直感")
    if {34, 20}.issubset(core_g) or {12, 22}.issubset(core_g) or {35, 36}.issubset(core_g) or {21, 45}.issubset(core_g): energized_centers.add("表現")

    b_gates_1, b_gates_2 = [], []
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

    is_rare = False
    if len(initial_islands) == 0: definition_type, is_rare = "全感受型", True
    elif len(initial_islands) == 1: definition_type = "一体型"
    elif len(initial_islands) == 2:
        if len(b_gates_1) > 0: definition_type = "二系統型"
        else: definition_type, is_rare = "特殊二系統型", True
    elif len(initial_islands) == 3: definition_type = "三系統型"
    elif len(initial_islands) == 4: definition_type, is_rare = "四系統型", True
    else: definition_type = "多系統型"

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

    if "生命力" in on_c: type_str = "表現する生命型" if motor_to_throat else "生命力型"
    else:
        if motor_to_throat: type_str = "行動開始型"
        elif len(on_c) > 0:
            type_str = "導き型"
            if len(on_c.intersection(LOWER_CENTERS)) == 0: is_rare = True
        else: type_str = "反射型"

    def calc_gate_score(gate, planet):
        c = next((k for k, v in CENTER_GATES.items() if gate in v), None)
        if c in energized_centers:
            return (CUSTOM_WEIGHTS.get(planet, 0) / 2.0) * (1.0 if c in on_c else DORMANT_MULTIPLIER)
        return 0.0

    # スコアの整数計算
    center_scores = {}
    total_score = 0
    for c in CENTER_ORDER:
        c_score = 0.0
        for x in data:
            if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]:
                c_score += calc_gate_score(x["gate"], x["planet"])
        c_int = int(c_score)
        center_scores[c] = c_int
        total_score += c_int

    red_counts, black_counts = {i: 0 for i in range(1, 7)}, {i: 0 for i in range(1, 7)}
    for d_item in data:
        if d_item["planet"] != "Chiron":
            if d_item["color"] == "Red": red_counts[d_item["line"]] += 1
            else: black_counts[d_item["line"]] += 1

    p_sun = next(d_item for d_item in data if d_item["planet"] == "Sun" and d_item["color"] == "Black")
    p_earth = next(d_item for d_item in data if d_item["planet"] == "Earth" and d_item["color"] == "Black")
    d_sun = next(d_item for d_item in data if d_item["planet"] == "Sun" and d_item["color"] == "Red")
    d_earth = next(d_item for d_item in data if d_item["planet"] == "Earth" and d_item["color"] == "Red")
    profile = f"{p_sun['line']}/{d_sun['line']}"

    # ===== HTML: 基本スペック =====
    spec_f = io.StringIO()
    with contextlib.redirect_stdout(spec_f):
        print(f"意識　（後天）　： {y}/{m:02d}/{d:02d} {h:02d}:{mi:02d}\n")
        print(f"<span class='unconscious-red'>無意識（先天）　： {dj.strftime('%Y/%m/%d %H:%M')}</span>\n")
        if is_rare: print(f"<div class='rare-alert'>★ 【特殊な特徴を検出】<br>詳細はぜひHD資格のある専門家にお問合せください！</div>\n")
        print(DIVIDER)
        print("**👶 あなたの基本体質と人生のテーマ**")
        print(DIVIDER)
        print(f"\n【体質タイプ】: {type_str}\n")
        print(f"\n └ 特徴: {TECH_TYPE_STRENGTHS.get(type_str, '解析中')}\n")
        print(f"\n【人生のテーマ (役割)】: {profile}\n")
        print(f"\n └ 特性: {PROFILE_TECH_MEANINGS.get(profile, '解析中...')}\n")
    
    # ===== HTML: エネルギー概要 =====
    ov_f = io.StringIO()
    with contextlib.redirect_stdout(ov_f):
        print("\n" + DIVIDER)
        print("🔋 身体の中枢別 エネルギー状態（概要）")
        print(DIVIDER)
        print(f"全体の自発エネルギー密度: {total_score} 🔋")
        if connected_motors:
            motors_jp = "・".join(connected_motors)
            print(f"💡 表現と連動している活力の源: {motors_jp}\n")

        for c in CENTER_ORDER:
            status = "活性化している" if c in on_c else "感受性が高い（外から影響を受けやすい）"
            print(f"\n■ **{c}**（{CENTER_ORGANS[c]}）\n")
            if c in ["頭脳", "思考"]: print(f"{status}\n")
            else: print(f"{status}  [小計: {center_scores[c]} 🔋]\n")

    # ===== HTML: 専門家向けデータ =====
    exp_f = io.StringIO()
    with contextlib.redirect_stdout(exp_f):
        print(f"【受胎十字 (インカネーションクロス)】\n")
        print(f"\n └ 先天(無意識): 太陽 {d_sun['gate']:>2} / 地球 {d_earth['gate']:>2}\n")
        print(f"\n └ 後天(意　識): 太陽 {p_sun['gate']:>2} / 地球 {p_earth['gate']:>2}\n")
        print(f"\n【心身の統合状態 (定義型)】: {definition_type}\n")
        if len(initial_islands) <= 1: print("🌟 橋渡しの扉: なし\n")
        else:
            if b_gates_1: print(f"🌟 橋渡しの扉: {sorted(list(set(b_gates_1)))}\n")
            elif b_gates_2: print(f"🌟 広域の橋渡しの扉:\n   {', '.join([f'[{bg1}, {bg2}]' for bg1, bg2 in b_gates_2])}\n")

        print("\n" + "=" * 35)
        print("🔭 天体と扉（ゲート）の対応表")
        print("=" * 35)
        for p in PLANET_ORDER:
            r = next((x for x in data if x["planet"] == p and x["color"] == "Red"), None)
            b = next((x for x in data if x["planet"] == p and x["color"] == "Black"), None)
            if r and b:
                rs = calc_gate_score(r["gate"], p) if p != "Chiron" else 0.0
                bs = calc_gate_score(b["gate"], p) if p != "Chiron" else 0.0
                r_sc = f" [{rs:>4.1f}]" if rs > 0 else "       "
                b_sc = f" [{bs:>4.1f}]" if bs > 0 else "       "
                print(f"{PLANET_JP.get(p, p)}")
                print(f"<span class='unconscious-red'>先天 {r['gate']:02d}.{r['line']}{r_sc}</span> ║ 後天 {b['gate']:02d}.{b['line']}{b_sc}\n")

        print("\n" + DIVIDER)
        print("🚪 中枢ごとの扉（ゲート）の詳細一覧")
        print(DIVIDER)
        for c in CENTER_ORDER:
            c_gates = [(x["gate"], x["line"], x["planet"], x["color"], calc_gate_score(x["gate"], x["planet"])) for x in data if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]]
            if c_gates:
                print(f"\n■ **{c}**\n")
                for g, line, p, col, s in sorted(c_gates, key=lambda x: x[0]):
                    score_str = f" [{s:>4.1f}]" if s > 0 else ""
                    mean_str = GATE_TECH_MEANINGS.get(g, "")
                    if col == "Red": print(f"\nー <span class='unconscious-red'>扉 {g:>2} {mean_str} ({PLANET_JP.get(p, p)}/先天){score_str}</span>")
                    else: print(f"\nー 扉 {g:>2} {mean_str} ({PLANET_JP.get(p, p)}/後天){score_str}")

    all_centers = set(CENTER_GATES.keys())
    off_centers = all_centers - set(on_c)
    full_open = [c for c in off_centers if len(CENTER_GATES[c] & set(core_g)) == 0]

    return {
        "total_score": total_score,
        "center_scores": center_scores,
        "off_centers": off_centers,
        "full_open": full_open,
        "on_c": on_c,
        "html_spec": spec_f.getvalue(),
        "html_overview": ov_f.getvalue(),
        "html_expert": exp_f.getvalue()
    }


# =====================================================================
# ▼▼▼ 6. 実行ボタンと表示 ▼▼▼
# =====================================================================
# ボタンを押した時だけデータを再計算し、セッションに保存
if st.sidebar.button("🌿 体質診断を開始する"):
    with st.spinner("診断レポートを生成しています..."):
        c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
        rd = generate_report_data(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE)
        st.session_state['report_data'] = rd
        # 以前のチェックボックスの履歴をリセット
        for c in CENTER_ORDER:
            if f"chk_{c}" in st.session_state:
                del st.session_state[f"chk_{c}"]

# データが保存されていれば、UIを描画（チェックボックスを押しても消えません）
if 'report_data' in st.session_state:
    rd = st.session_state['report_data']
    total_score = rd['total_score']
    
    # チェックボックスによる減点計算
    deducted = 0
    for c in CENTER_ORDER:
        if st.session_state.get(f"chk_{c}", False):
            deducted += rd['center_scores'][c]
            
    current_score = max(0, total_score - deducted)

    # 🌟 1. マス目のメーター（連動して動く！）
    st.markdown(f"### 🔋 本来の「らしさ」エネルギー発揮度: {current_score} / {total_score}")
    
    blocks_html = "<div style='width: 80%; display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 20px; padding: 10px; background: #f8f9fa; border-radius: 8px;'>"
    for i in range(total_score):
        bg = "#00BFFF" if i < current_score else "#CFD8DC" # Activeは水色、Inactiveはグレー
        blocks_html += f"<div style='width: 14px; height: 14px; background-color: {bg}; border-radius: 2px; box-shadow: 1px 1px 2px rgba(0,0,0,0.1);'></div>"
    blocks_html += "</div>"
    st.markdown(blocks_html, unsafe_allow_html=True)
    
    # 🌟 2. 一般向け: 基本スペック
    st.markdown(f"<div class='card'>\n{rd['html_spec']}\n</div>", unsafe_allow_html=True)
    
    # 🌟 3. インタラクティブ・心身の歪み診断（Notself）
    st.markdown("### 🚨 心身の歪み診断（Notself自己採点）")
    st.info("💡 日常の中で感じる不調（外からの影響）にチェックを入れてください。本来のエネルギーがどれだけブロックされているか、上のバーと連動して視覚化されます。")
    
    for c in CENTER_ORDER:
        with st.container():
            st.markdown(f"#### ■ **{c}**（{CENTER_ORGANS[c]}）")
            if c in rd['off_centers']:
                status_text = "完全に感受性が開いている（外の影響を強く受ける）" if c in rd['full_open'] else "感受性が高い（外から影響を受けやすい）"
                st.markdown(f"**状態: {status_text}**")
                st.markdown(f"**{CENTER_ISSUES[c]['curse']}**")
                st.markdown(f"*{CENTER_ISSUES[c]['truth']}*")
                st.markdown(f"`{CENTER_ISSUES[c]['solution']}`")
            else:
                st.markdown("**状態: 活性化している（安定したエネルギーが流れている）**")
                if c in DEFINED_CENTER_ISSUES:
                    st.markdown(f"**{DEFINED_CENTER_ISSUES[c]['curse']}**")
                    st.markdown(f"*{DEFINED_CENTER_ISSUES[c]['truth']}*")
                    st.markdown(f"`{DEFINED_CENTER_ISSUES[c]['solution']}`")
                else:
                    st.markdown("（安定したエネルギーの中枢として、正常に働いています）")
            
            pts = rd['center_scores'][c]
            lbl = f"✖ 最近この不調（思い込み）に振り回されている気がする（エネルギー -{pts} 減点）" if pts > 0 else "✖ 最近この不調（思い込み）に振り回されている気がする"
            st.checkbox(lbl, key=f"chk_{c}")
            st.divider()

    # 🌟 4. 一般向け: エネルギー概要
    st.markdown(f"<div class='card'>\n{rd['html_overview']}\n</div>", unsafe_allow_html=True)
    
    # 🌟 5. マニア向け: 専門データの格納
    with st.expander("▼ 【専門データ】ゲート・ライン・天体の詳細を開く"):
        st.markdown(f"<div class='card' style='background-color:#f8f9fa;'>\n{rd['html_expert']}\n</div>", unsafe_allow_html=True)
