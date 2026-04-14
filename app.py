# =====================================================================
# タイトル: HD自作エンジン Webアプリ版 (Notself連動 ＋ 三層モード切替版)
# =====================================================================
import streamlit as st
import io
import contextlib
import swisseph as swe
import datetime
import collections
import os
import urllib.request

st.set_page_config(page_title="体質診断レポート", page_icon="👶", layout="wide", initial_sidebar_state="expanded")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

DIVIDER = "-" * 35

PLANET_ORDER = ["Sun", "Earth", "Moon", "NorthNode", "SouthNode", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"]
PLANET_JP = {"Sun": "太陽", "Earth": "地球", "Moon": "月", "NorthNode": "北の交点", "SouthNode": "南の交点", "Mercury": "水星", "Venus": "金星", "Mars": "火星", "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星", "Neptune": "海王星", "Pluto": "冥王星", "Chiron": "キロン"}
CENTER_ORDER = ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]

st.markdown("### **👶 体質・生命力 診断レポート**")
st.markdown("<span style='font-size: 0.9em; color: gray;'>**生まれ持った体の仕組みと、心身のエネルギーの流れを読み解きます。**</span>", unsafe_allow_html=True)

# =====================================================================
# ▼▼▼ 2. 左側メニュー: モード切替 ＆ 入力 ▼▼▼
# =====================================================================
st.sidebar.header("▼ 翻訳モードの選択")
display_mode = st.sidebar.radio(
    "誰に診断結果を見せますか？", 
    ["🌿 やさしい言葉（初心者・一般）", "💻 理系・システム工学（論理派）", "🏫 中高生向け（学園生活・青春）"]
)

st.sidebar.markdown("---")
st.sidebar.header("▼ 生年月日の入力 (日本時間)")
input_date = st.sidebar.date_input("生年月日", value=datetime.date(1980, 1, 1), min_value=datetime.date(1920, 1, 1))
col1, col2 = st.sidebar.columns(2)
HOUR = col1.selectbox("時", range(24), index=12)
MINUTE = col2.selectbox("分", range(60), index=30)
YEAR, MONTH, DAY = input_date.year, input_date.month, input_date.day

# =====================================================================
# ▼▼▼ 3. 三層モード辞書システム（省略一切なし！） ▼▼▼
# =====================================================================
def get_dictionaries(mode):
    if "理系" in mode:
        type_strengths = {
            "生命力型": "【持続稼働型エンジン】外部Pingへのレスポンス時に最大トルクを発揮する高耐久仕様。",
            "表現する生命型": "【並列処理対応コア】直感的最適化を行いながら複数タスクを高速コンパイルする多機能型。",
            "行動開始型": "【独立起動システム】他プロセスに実行トリガーを送るroot権限を持つ自律型ユニット。",
            "導き型": "【リソース最適化プロセッサ】全体のトラフィックを俯瞰監視し、効率化を図るシステム管理AI。",
            "反射型": "【全方位サンプリング・センサー】環境の健全性を中立にモニタリングする広域環境センサー。"
        }
        center_issues = {
            "頭脳": {"curse": "⚠️ 【エラー: 無効クエリ過剰処理】無関係な外部データ受信によるメモリリーク。", "truth": "⚡ 【仕様】必要なシグナルのみ受信する特定周波数アンテナ。", "solution": "🛠️ 【パッチ】無関係なクエリは強制DROPする。"},
            "思考": {"curse": "⚠️ 【エラー: キャッシュ強制固定化】古い演算結果に縛られアルゴリズム更新不可。", "truth": "⚡ 【仕様】入力に応じて都度レンダリングを行う動的プロセッサ。", "solution": "🛠️ 【パッチ】前回の結果に依存せず、都度再計算する。"},
            "表現": {"curse": "⚠️ 【エラー: 未要求パケット送信】Pingなしで送信しパケットロスが発生。", "truth": "⚡ 【仕様】リクエスト時のみポート開放するレスポンス特化型。", "solution": "🛠️ 【パッチ】外部リクエスト（Ping）が来るまで待機。"},
            "自己": {"curse": "⚠️ 【エラー: 静的IPアドレス固執】環境変化に応じたルーティング不全。", "truth": "⚡ 【仕様】接続先に応じて自動設定される動的IP（DHCP）。", "solution": "🛠️ 【パッチ】環境によって自身の座標は変動してよいと許可する。"},
            "意志": {"curse": "⚠️ 【エラー: オーバースペック稼働】要求以上の処理によるマザーボード焼損。", "truth": "⚡ 【仕様】省エネ稼働によるシステム寿命の最大化。", "solution": "🛠️ 【パッチ】スペック以上の要求にはError 403を返す。"},
            "生命力": {"curse": "⚠️ 【エラー: シャットダウン無視】停止できずバッテリー完全放電。", "truth": "⚡ 【仕様】タスク完了後に自動スリープするエコ仕様。", "solution": "🛠️ 【パッチ】残量10%で強制シャットダウンを実行。"},
            "直感": {"curse": "⚠️ 【エラー: レガシー環境固執】危険な旧環境に留まるセキュリティリスク。", "truth": "⚡ 【仕様】リアルタイムで脅威検知・ブロックするファイアウォール。", "solution": "🛠️ 【パッチ】エラー検知の瞬間、即時ログアウト。"},
            "感情": {"curse": "⚠️ 【エラー: ノイズ混入即時コンパイル】波形安定前の演算による致命的バグ。", "truth": "⚡ 【仕様】波形を時間をかけて遅延評価する高精度演算システム。", "solution": "🛠️ 【パッチ】波形グラフが安定するまで演算をペンディングする。"},
            "活力": {"curse": "⚠️ 【エラー: 外部同期処理】他システムのペースに合わせ過負荷ダウン。", "truth": "⚡ 【仕様】自身のクロック周波数による非同期処理完遂。", "solution": "🛠️ 【パッチ】他人のクロック周波数（焦り）には同期しない。"}
        }
    elif "中高生" in mode:
        type_strengths = {
            "生命力型": "【コツコツ職人タイプ】好きなことには無限に熱中できる！周りの誘いに「乗った！」と反応すると最強。",
            "表現する生命型": "【マルチな切り込み隊長】やりたいことがいっぱい！試行錯誤しながら最短ルートを見つける天才。",
            "行動開始型": "【クラスの流行りを作る人】ゼロから新しい遊びや流行をスタートさせる力がある、独立独歩のリーダー。",
            "導き型": "【名マネージャー・名監督】みんなの得意なことを見抜いて、チームを勝利に導くアドバイザー役。",
            "反射型": "【クラスの守り神】みんなの空気感を鏡のように映し出す。いるだけでその場の良し悪しがわかる不思議な存在。"
        }
        center_issues = {
            "頭脳": {"curse": "🌀 【悩み】「テスト勉強しなきゃ」「将来どうしよう」と、友達の悩みまで背負い込んで頭パンパン。", "truth": "✨ 【才能】自分に必要な「ひらめき」だけを受け取れる高性能アンテナ。", "solution": "👉 【コツ】「その悩み、私が今考えることじゃないな」とスルーしてOK。"},
            "思考": {"curse": "🌀 【悩み】「一度言ったことは変えちゃダメだ」と意地を張って、自分の首を絞めてる。", "truth": "✨ 【才能】新しい情報をどんどん取り入れて考えをアップデートできる柔軟な頭。", "solution": "👉 【コツ】「昨日の意見と違ってもいいじゃん！進化してる証拠だよ」。"},
            "表現": {"curse": "🌀 【悩み】沈黙が怖くて、思ってもないことを話し続けて後で「あちゃー」ってなる。", "truth": "✨ 【才能】誰かに聞かれた時、一番説得力のある言葉が出てくる「待機モード」の声。", "solution": "👉 【コツ】「話しかけられるまで、静かに余裕をかましておこう」。"},
            "自己": {"curse": "🌀 【悩み】「本当の自分」を探して、キャラ迷走中。周りに合わせすぎて疲れちゃう。", "truth": "✨ 【才能】場所や友達によって、自分を自由に変えられる「変幻自在のカメレオン」。", "solution": "👉 【コツ】「今の環境で楽しんでる自分が、今の正解！」。"},
            "意志": {"curse": "🌀 【悩み】「もっと頑張って認められなきゃ」と、無理な約束をして自分を追い込んでる。", "truth": "✨ 【才能】頑張らなくても最初から価値がある。無理な努力はしなくていい人。", "solution": "👉 【コツ】「やりたくないことは断っていい。君の価値は成績じゃ決まらない」。"},
            "生命力": {"curse": "🌀 【悩み】みんながまだ起きてるから…と、休むタイミングを逃して寝不足フラフラ。", "truth": "✨ 【才能】集中してやりきったら、あとはスッと眠りにつけるスッキリ体質。", "solution": "👉 【コツ】「電池が切れる前に、自分から先に寝逃げしよう」。"},
            "直感": {"curse": "🌀 【悩み】「なんとなく嫌な予感」を無視して、合わないグループに居続けてストレスMAX。", "truth": "✨ 【才能】「あ、ここ危ない」と瞬時に察知する最強の防犯アラーム。", "solution": "👉 【コツ】「なんとなく嫌」は絶対正しい。すぐに距離を置いて逃げよう。"},
            "感情": {"curse": "🌀 【悩み】気分が上がってる時や、イライラしてる時に勢いで決めて、後で大後悔。", "truth": "✨ 【才能】時間をかけて自分の気持ちが落ち着くのを待てば、100点の答えが出せる。", "solution": "👉 【コツ】「一晩寝かせてから返事するわ」が最強の決め台詞。"},
            "活力": {"curse": "🌀 【悩み】「早く課題出しなさい！」と急かされてパニック。焦ってミス連発。", "truth": "✨ 【才能】自分のペースで取り組めば、すごいパワーでやり切れる集中力の持ち主。", "solution": "👉 【コツ】「人は人、私は私。他人の焦り（プレッシャー）は受け取らない」。"}
        }
    else: # やさしい言葉モード
        type_strengths = {
            "生命力型": "安定した生命力を持ち続けるエンジン体質。\n繰り返しの積み重ねで体と心を最高の状態へ整え、外からの呼びかけへの反応力が高い。",
            "表現する生命型": "複数のことを同時にこなす多機能型の体質。\n試行錯誤しながら最短の道を直感で見つける、素早い行動力を持つ。",
            "行動開始型": "自分から新しいことを始める力（主導権）がある体質。\nゼロから道を切り開き、他者を動かす働きかけができる。",
            "導き型": "全体の流れを高い視点から見渡せる体質。\nエネルギーを効率よく使い、他者の状態を整えることが得意。",
            "反射型": "周囲の環境全体を映し出すセンサー体質。\n偏りなく全体の健康状態を感じ取り、公平に判断できる。"
        }
        center_issues = {
            "頭脳": {"curse": "🌀 【思い込み】「いつも明確なビジョンを持て」「自分で考えろ」\n └ 他人の疑問を抱え込み、頭が疲れ果ててしまう。", "truth": "✨ 【本来の仕組み】必要な気づきだけを受け取れる「感度の高いアンテナ」。", "solution": "👉 【整える言葉】「その悩みは、私が引き受けることではありません」"},
            "思考": {"curse": "🌀 【思い込み】「一貫性を持て」「意見をころころ変えるな」\n └ 一度出した答えに縛られ、柔軟な思考が固まってしまう。", "truth": "✨ 【本来の仕組み】新しい考えをどんどん取り入れられる「柔軟な思考の器」。", "solution": "👉 【整える言葉】「昨日の私と今日の私は、成長した別の私です」"},
            "表現": {"curse": "🌀 【思い込み】「自分から発言しろ」「沈黙は気まずい」\n └ 沈黙を恐れて無理に言葉を出し続け、空回りしてしまう。", "truth": "✨ 【本来の仕組み】外から求められたときに最大の力を発揮する「待機型の声」。", "solution": "👉 【整える言葉】「呼ばれるまで、静かに待っているのが私の自然な状態です」"},
            "自己": {"curse": "🌀 【思い込み】「自分探しをしろ」「確固たる自分を持て」\n └ 固定した自分を探し続けて迷い、心が落ち着かなくなる。", "truth": "✨ 【本来の仕組み】いる場所や出会う人に応じて自然に向きを変える「羅針盤」。", "solution": "👉 【整える言葉】「私は環境によって変わっていい。それが私らしさです」"},
            "意志": {"curse": "🌀 【思い込み】「約束は必ず守れ」「努力して価値を証明しろ」\n └ 体の限界を超えてまで頑張り続け、負担をかけてしまう。", "truth": "✨ 【本来の仕組み】自分の価値を証明し続けなくていい「無重力の心」。", "solution": "👉 【整える言葉】「証明すべきことは何もない。体が無理だと言ったら止めていい」"},
            "生命力": {"curse": "🌀 【思い込み】「途中で投げ出すな」「休むな」\n └ 他人のペースに引きずられ、疲れ果ててしまう。", "truth": "✨ 【本来の仕組み】必要な分だけ力を出して、用が済んだらすっと手放せる「充電不要な電池」。", "solution": "👉 【整える言葉】「今日分の力は使い切った。体が止まれと言う前に、先に休む」"},
            "直感": {"curse": "🌀 【思い込み】「石の上にも三年」「手放すのはもったいない」\n └ 古い恐れに縛られ、合わない環境に居続けてしまう。", "truth": "✨ 【本来の仕組み】違和感を感じたらすぐ離れられる「体の警報装置」。", "solution": "👉 【整える言葉】「なんとなく嫌な感じがする場所・人とは、すぐ距離を置いていい」"},
            "感情": {"curse": "🌀 【思い込み】「空気を読め」「感情的になるな」\n └ 自分の気持ちを押し込めて「いい人」を演じ続け、疲弊する。", "truth": "✨ 【本来の仕組み】他者の感情の波を感じながら、そっと観察できる「共感の受信機」。", "solution": "👉 【整える言葉】「この感情の波は、誰かのもの。私はただ感じているだけでいい」"},
            "活力": {"curse": "🌀 【思い込み】「早く終わらせろ」「やることを溜めるな」\n └ 外からのプレッシャーで常に焦らされ、体が休まらなくなる。", "truth": "✨ 【本来の仕組み】外からのせかしをやり過ごし、自分のペースで動ける「独立した活力の源」。", "solution": "👉 【整える言葉】「急いでも物事は変わらない。他人の焦りは受け取らなくていい」"}
        }

    return type_strengths, center_issues, DEFINED_CENTER_ISSUES_BASE

# =====================================================================
# ▼▼▼ 4. 固定データ群（省略なし！） ▼▼▼
# =====================================================================
CUSTOM_WEIGHTS = {"Sun": 35.0, "Earth": 35.0, "Moon": 10.0, "Mercury": 4.5, "Venus": 4.0, "Mars": 3.5, "Jupiter": 3.0, "Saturn": 2.0, "Uranus": 1.5, "Neptune": 1.0, "Pluto": 0.5, "NorthNode": 0.0, "SouthNode": 0.0, "Chiron": 0.0}
DORMANT_MULTIPLIER = 0.3
FORCED_GATES = set()
GATE_SEQUENCE = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
CENTER_GATES = {"頭脳": {64, 61, 63}, "思考": {47, 24, 4, 17, 43, 11}, "表現": {62, 23, 56, 31, 8, 33, 20, 16, 35, 12, 45}, "自己": {7, 1, 13, 25, 46, 2, 15, 10}, "意志": {21, 51, 26, 40}, "生命力": {34, 5, 14, 29, 59, 9, 3, 42, 27}, "直感": {48, 57, 44, 50, 32, 28, 18}, "感情": {36, 22, 37, 6, 49, 55, 30}, "活力": {58, 38, 54, 53, 60, 52, 19, 39, 41}}
CENTER_ORGANS = {"頭脳": "松果体", "思考": "脳下垂体", "表現": "甲状腺・副甲状腺", "自己": "肝臓・血液", "意志": "心臓・胸腺・胆嚢", "生命力": "卵巣・精巣", "直感": "脾臓・リンパ系", "感情": "膵臓・腎臓・神経系", "活力": "副腎"}
CHANNELS = {"頭脳_思考": [(64,47,"64-47"), (61,24,"61-24"), (63,4,"63-4")], "思考_表現": [(17,62,"17-62"), (43,23,"43-23"), (11,56,"11-56")], "表現_自己": [(31,7,"31-7"), (8,1,"8-1"), (33,13,"33-13"), (10,20,"10-20")], "表現_意志": [(45,21,"45-21")], "表現_感情": [(35,36,"35-36"), (12,22,"12-22")], "表現_直感": [(16,48,"16-48"), (20,57,"20-57")], "表現_生命力": [(20,34,"20-34")], "自己_意志": [(25,51,"25-51")], "自己_生命力": [(5,15,"5-15"), (46,29,"46-29"), (2,14,"2-14"), (10,34,"10-34")], "自己_直感": [(10,57,"10-57")], "意志_感情": [(40,37,"40-37")], "意志_直感": [(26,44,"26-44")], "生命力_感情": [(6,59,"6-59")], "生命力_直感": [(50,27,"50-27"), (34,57,"34-57")], "生命力_活力": [(53,42,"53-42"), (3,60,"3-60"), (9,52,"9-52")], "感情_活力": [(19,49,"19-49"), (39,55,"39-55"), (41,30,"41-30")], "直感_活力": [(18,58,"18-58"), (28,38,"28-38"), (32,54,"32-54")]}

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

DEFINED_CENTER_ISSUES_BASE = {
    "頭脳": {"curse": "🌀 【外からの思い込み】「他人の悩みにも関心を持て」", "truth": "✨ 【本来の仕組み】自分に必要な気づきだけを受け取る。", "solution": "👉 【整える言葉】「他人の悩みを自分の中に入れない。」"},
    "思考": {"curse": "🌀 【外からの思い込み】「もっと柔軟になれ」", "truth": "✨ 【本来の仕組み】一定のやり方で確実に情報を処理する。", "solution": "👉 【整える言葉】「私の考え方は生まれつきの仕様。」"},
    "表現": {"curse": "🌀 【外からの思い込み】「もっと言葉を選べ」", "truth": "✨ 【本来の仕組み】自分のスタイルで確かに言葉を出せる。", "solution": "👉 【整える言葉】「この伝え方が私の自然な声。」"},
    "自己": {"curse": "🌀 【外からの思い込み】「相手に合わせなさい」", "truth": "✨ 【本来の仕組み】自分を中心に、合う人・環境を引き寄せる。", "solution": "👉 【整える言葉】「私は動かない。合う人だけが近づいてくる」"},
    "意志": {"curse": "🌀 【外からの思い込み】「謙虚であれ」", "truth": "✨ 【本来の仕組み】確固たる意志で正当な対価を受け取る。", "solution": "👉 【整える言葉】「堂々と対価を求めていい」"},
    "生命力": {"curse": "🌀 【外からの思い込み】「頭で考えて動け」", "truth": "✨ 【本来の仕組み】体が反応した瞬間だけ、無限の力が湧き出る。", "solution": "👉 【整える言葉】「体の奥が反応するまで、静かに待つ」"},
    "直感": {"curse": "🌀 【外からの思い込み】「根拠を出せ」", "truth": "✨ 【本来の仕組み】今この瞬間の正解を、一瞬で知らせる警報。", "solution": "👉 【整える言葉】「なんとなく嫌だから。理由は後でいい」"},
    "感情": {"curse": "🌀 【外からの思い込み】「すぐ決断しろ！」", "truth": "✨ 【本来の仕組み】時間をかけるほど本当の答えが見えてくる。", "solution": "👉 【整える言葉】「数日ゆっくり考えてからお返事します」"},
    "活力": {"curse": "🌀 【外からの思い込み】「焦らなくていい」", "truth": "✨ 【本来の仕組み】自らプレッシャーを生み出し、一気に処理する。", "solution": "👉 【整える言葉】「プレッシャーは私の力の源です」"}
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

TECH_LINE_MEANINGS = {
    1: "土台づくり・基礎固め", 2: "生まれ持った独自の才能",
    3: "試して学ぶ・実践型", 4: "人とのつながり・縁",
    5: "問題を解決する力", 6: "全体を見渡して整える力"
}

MOTOR_CENTERS = {"生命力", "意志", "感情", "活力"}
LOWER_CENTERS = {"自己", "意志", "生命力", "直感", "感情", "活力"}

# =====================================================================
# ▼▼▼ 天文暦セットアップ & 計算関数 ▼▼▼
# =====================================================================
ephe_dir = './ephe_data'
os.makedirs(ephe_dir, exist_ok=True)
for f in ['sepl_18.se1', 'semo_18.se1', 'seas_18.se1']:
    if not os.path.exists(os.path.join(ephe_dir, f)):
        urllib.request.urlretrieve('https://github.com/aloistr/swisseph/raw/master/ephe/' + f, os.path.join(ephe_dir, f))
swe.set_ephe_path(ephe_dir)

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
    planets = {swe.SUN: "Sun", swe.MOON: "Moon", swe.TRUE_NODE: "NorthNode", swe.MERCURY: "Mercury", swe.VENUS: "Venus", swe.MARS: "Mars", swe.JUPITER: "Jupiter", swe.SATURN: "Saturn", swe.URANUS: "Uranus", swe.NEPTUNE: "Neptune", swe.PLUTO: "Pluto", swe.CHIRON: "Chiron"}
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

def generate_report_data(data, jd_d, y, m, d, h, mi, mode):
    T_TYPE, T_CENTER, T_DEF_CENTER = get_dictionaries(mode)
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
        elif len(on_c) > 0: type_str = "導き型"
        else: type_str = "反射型"

    def calc_gate_score(gate, planet):
        c = next((k for k, v in CENTER_GATES.items() if gate in v), None)
        if c in energized_centers:
            return (CUSTOM_WEIGHTS.get(planet, 0) / 2.0) * (1.0 if c in on_c else DORMANT_MULTIPLIER)
        return 0.0
    
    center_scores = {}
    total_score = 0
    for c in CENTER_ORDER:
        c_score = sum(calc_gate_score(x["gate"], x["planet"]) for x in data if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c])
        center_scores[c] = int(c_score)
        total_score += int(c_score)

    all_centers = set(CENTER_GATES.keys())
    off_centers = all_centers - set(on_c)
    full_open = [c for c in off_centers if len(CENTER_GATES[c] & set(core_g)) == 0]

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

    dv = swe.revjul(jd_d)
    dj = datetime.datetime(int(dv[0]), int(dv[1]), int(dv[2]), int(dv[3]), int((dv[3] % 1) * 60)) + datetime.timedelta(hours=9)

    spec_f = io.StringIO()
    with contextlib.redirect_stdout(spec_f):
        print(f"意識　（後天）　： {y}/{m:02d}/{d:02d} {h:02d}:{mi:02d}\n")
        print(f"<span class='unconscious-red'>無意識（先天）　： {dj.strftime('%Y/%m/%d %H:%M')}</span>\n")
        if is_rare: print(f"<div class='rare-alert'>★ 【特殊な特徴を検出】<br>詳細はぜひHD資格のある専門家にお問合せください！</div>\n")
        print(DIVIDER)
        print("**👶 あなたの基本体質と役割**")
        print(DIVIDER)
        print(f"\n【体質タイプ】: {type_str}\n")
        print(f"\n └ 特徴: {T_TYPE.get(type_str, '解析中')}\n")
        print(f"\n【人生の役割】: {profile}\n")
        print(f"\n └ 特性: {PROFILE_TECH_MEANINGS.get(profile, '')}\n")

    exp_f = io.StringIO()
    with contextlib.redirect_stdout(exp_f):
        print(f"【受胎十字 (インカネーションクロス)】\n")
        print(f"\n └ 先天(無意識): 太陽 {d_sun['gate']:>2} / 地球 {d_earth['gate']:>2}\n")
        print(f"\n └ 後天(意　識): 太陽 {p_sun['gate']:>2} / 地球 {p_earth['gate']:>2}\n")
        print(f"\n【心身の統合状態 (定義型)】: {definition_type}\n")
        if "特殊二系統型" in definition_type:
            print("\n └ 特徴: 島が遠く離れており、1つの扉では繋がりません。他者との関わりを通じて時間をかけて全体を統合していく体質です。\n")
        if len(initial_islands) <= 1:
            print("🌟 橋渡しの扉: なし\n")
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

        print("\n" + DIVIDER)
        print("📊 層別の構成（各層の扉の数）")
        print(DIVIDER)
        print("<b>層 ║ <span class='unconscious-red'>先天</span> ║ 後天 ║ 合計 ║ 特性</b>\n")
        for i in range(1, 7):
            tot = red_counts[i] + black_counts[i]
            print(f" {i}層 ║ <span class='unconscious-red'>{red_counts[i]:>2}</span> │ {black_counts[i]:>2} ║ {tot:>2} ║ {TECH_LINE_MEANINGS[i]}\n")

    return {
        "total_score": total_score, "center_scores": center_scores, "off_centers": off_centers, "full_open": full_open,
        "on_c": on_c, "T_CENTER": T_CENTER, "T_DEF_CENTER": T_DEF_CENTER, "html_spec": spec_f.getvalue(), "html_expert": exp_f.getvalue()
    }

# =====================================================================
# ▼▼▼ 6. 実行ボタンとUIの描画 ▼▼▼
# =====================================================================
if st.sidebar.button("🌿 体質診断を開始する"):
    with st.spinner("診断中..."):
        c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
        st.session_state['report_data'] = generate_report_data(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE, display_mode)
        st.session_state['current_mode'] = display_mode
        for c in CENTER_ORDER:
            if f"chk_{c}" in st.session_state: del st.session_state[f"chk_{c}"]

if 'report_data' in st.session_state:
    rd = st.session_state['report_data']
    mode = st.session_state['current_mode']
    
    st.info(f"現在の翻訳モード: **{mode}**")
    
    if "理系" in mode:
        title, desc, m_title, chk_lbl = "🚨 心身のバグ診断", "エラー（思い込み）にチェックを入れてください。システムダウン値が可視化されます。", "システム稼働率", "✖ システムエラー発生中"
    elif "中高生" in mode:
        title, desc, m_title, chk_lbl = "🚨 青春のモヤモヤ診断", "日常の「あるある」にチェック！自分らしさがどれくらい隠れてるかわかるよ。", "自分らしさ全開度", "✖ この「あるある」にハマってる"
    else:
        title, desc, m_title, chk_lbl = "🚨 心身の歪み診断", "日常の不調（思い込み）にチェックを入れてください。エネルギーのブロックが視覚化されます。", "本来のエネルギー発揮度", "✖ これに振り回されている"

    deducted = sum(rd['center_scores'][c] for c in CENTER_ORDER if st.session_state.get(f"chk_{c}", False))
    current_score = max(0, rd['total_score'] - deducted)

    st.markdown(f"### 🔋 {m_title}: {current_score} / {rd['total_score']}")
    blocks_html = f"<div style='width: 80%; display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 20px; padding: 10px; background: #f8f9fa; border-radius: 8px;'>"
    for i in range(rd['total_score']):
        bg = "#E53935" if "理系" in mode and i < current_score else ("#00BFFF" if i < current_score else "#CFD8DC")
        blocks_html += f"<div style='width: 14px; height: 14px; background-color: {bg}; border-radius: 2px; box-shadow: 1px 1px 2px rgba(0,0,0,0.1);'></div>"
    st.markdown(blocks_html + "</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='card'>\n{rd['html_spec']}\n</div>", unsafe_allow_html=True)

    st.markdown(f"### {title}")
    st.info(desc)
    for c in CENTER_ORDER:
        with st.container():
            st.markdown(f"#### ■ **{c}**")
            t_data = rd['T_CENTER'][c] if c in rd['off_centers'] else rd['T_DEF_CENTER'][c]
            st.markdown(f"**{t_data['curse']}**\n\n*{t_data['truth']}*\n\n`{t_data['solution']}`")
            
            pts = rd['center_scores'][c]
            lbl = f"{chk_lbl} (-{pts} 減点)" if pts > 0 else chk_lbl
            st.checkbox(lbl, key=f"chk_{c}")
            st.divider()

    with st.expander("▼ 【専門データ】ゲート・ライン・天体の詳細を開く"):
        st.markdown(f"<div class='card' style='background-color:#f8f9fa;'>\n{rd['html_expert']}\n</div>", unsafe_allow_html=True)
