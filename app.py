# =====================================================================
# タイトル: HD自作エンジン Webアプリ版 (エラー修正完全版)
# =====================================================================
import streamlit as st
import io
import contextlib
import datetime
import collections
import os
import urllib.request
 
# swissephのインポートとエラーハンドリング
try:
    import swisseph as swe
    SWE_AVAILABLE = True
except ImportError:
    st.error("⚠️ swisseph ライブラリがインストールされていません。`pip install pyswisseph` を実行してください。")
    SWE_AVAILABLE = False
    st.stop()
 
st.set_page_config(page_title="体質診断レポート", page_icon="👶", layout="wide", initial_sidebar_state="expanded")
 
# 🌟 CSSスタイル設定
st.markdown("""
<style>
    .main { background-color: #ffffff; }
    .stApp { max-width: 1000px; margin: 0 auto; }
    .unconscious-red { color: #E53935; font-weight: bold; }
    .card { background-color: #fcfcfc; padding: 20px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 20px; }
    .rare-alert { background-color: #FFF9C4; padding: 10px; border-radius: 5px; border-left: 5px solid #FBC02D; font-weight: bold; }
</style>
""", unsafe_allow_html=True)
 
DIVIDER = "-" * 35
 
PLANET_ORDER = ["Sun", "Earth", "Moon", "NorthNode", "SouthNode", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron"]
PLANET_JP = {"Sun": "太陽", "Earth": "地球", "Moon": "月", "NorthNode": "北の交点", "SouthNode": "南の交点", "Mercury": "水星", "Venus": "金星", "Mars": "火星", "Jupiter": "木星", "Saturn": "土星", "Uranus": "天王星", "Neptune": "海王星", "Pluto": "冥王星", "Chiron": "キロン"}
CENTER_ORDER = ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]
 
def reset_state():
    """セッション状態をリセット"""
    for c in CENTER_ORDER:
        st.session_state[f"chk_{c}"] = False
 
# セッション状態の初期化
if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    reset_state()
 
st.markdown("### **👶 身体の働き・活力 診断レポート**")
st.markdown("<span style='font-size: 0.9em; color: gray;'>**持って生まれた器と、心身の活力の流れを読み解きます。**</span>", unsafe_allow_html=True)
 
# =====================================================================
# ▼▼▼ 翻訳辞書（全モード・省略なし完全版） ▼▼▼
# =====================================================================
def get_dictionaries(mode):
    if "ビジネス" in mode:
        type_strengths = {
            "生命力型": "【持続型リソース】確実なタスク消化で組織の土台を作る、高耐久のエンジン気質。",
            "表現する生命型": "【マルチタスク型】複数プロジェクトを同時に回し、最短ルートで最適化する効率化のプロ。",
            "行動開始型": "【ゼロイチ・起業家型】自らプロジェクトを立ち上げ、他者を巻き込んで推進するリーダー。",
            "導き型": "【俯瞰・マネジメント型】組織全体の動きを見渡し、人材とリソースを最適配置するアドバイザー。",
            "反射型": "【組織のバロメーター型】チームの健康状態や空気感を中立に評価できる、貴重な環境センサー。"
        }
        center_issues = {
            "頭脳": {"curse": "⚠️ 【非効率なインプット】自社の管轄外の課題まで抱え込み、脳内リソースが枯渇する。", "truth": "⚡ 【本来の強み】必要な情報だけを抽出する高精度のフィルター機能。", "solution": "🛠️ 【最適化】「それは私の管轄外」とタスクを切り離す。"},
            "思考": {"curse": "⚠️ 【古いスキームへの固執】「一貫性」に縛られ、柔軟なピボット（方針転換）ができなくなる。", "truth": "⚡ 【本来の強み】状況に応じて常に最新の最適解をアップデートできる柔軟性。", "solution": "🛠️ 【最適化】過去の決定にこだわらず、データに基づき都度判断する。"},
            "表現": {"curse": "⚠️ 【無駄なアウトプット】求められていない場面で発言し、影響力が分散（空回り）する。", "truth": "⚡ 【本来の強み】相手からリクエストされた時に、最大の説得力を発揮する声。", "solution": "🛠️ 【最適化】相手から「意見を求められる」まで待機する。"},
            "自己": {"curse": "⚠️ 【ポジショニングの迷走】固定のキャラ（役割）を作ろうとして、環境適応力が低下する。", "truth": "⚡ 【本来の強み】アサインされたプロジェクトやチームに合わせて、柔軟に立ち回れる適応力。", "solution": "🛠️ 【最適化】環境に応じて流動的に役割を変えてよいと許可する。"},
            "意志": {"curse": "⚠️ 【オーバーワーク】自らの価値を証明しようと、無理なコミットメント（約束）をして疲弊する。", "truth": "⚡ 【本来の強み】無理な努力をしなくても、存在自体に価値がある状態。", "solution": "🛠️ 【最適化】自分のキャパシティを超える要求は堂々と断る。"},
            "生命力": {"curse": "⚠️ 【撤退ラインの見誤り】他人の労働ペースに引きずられ、休息のタイミングを逃しダウンする。", "truth": "⚡ 【本来の強み】必要なタスクが終われば、すぐにオフモードに切り替えられる省エネ体質。", "solution": "🛠️ 【最適化】余力があるうちに、自ら意図的にストップをかける。"},
            "直感": {"curse": "⚠️ 【サンクコストの罠】「ここまでやったから」という過去の投資に縛られ、損切りが遅れる。", "truth": "⚡ 【本来の強み】リスクや違和感を瞬時に察知する、優れた危機管理センサー。", "solution": "🛠️ 【最適化】違和感を感じたプロジェクト・関係からは即座に撤退する。"},
            "感情": {"curse": "⚠️ 【感情的な即決】気分の高揚や焦りに任せて決断し、後で大きな損失を生む。", "truth": "⚡ 【本来の強み】時間をかけて多角的にリスクを評価できる、精度の高い分析力。", "solution": "🛠️ 【最適化】決断は一晩持ち帰り、クールダウンしてから行う。"},
            "活力": {"curse": "⚠️ 【他者のペースへの同期】外部からのプレッシャーに急かされ、仕事のクオリティが低下する。", "truth": "⚡ 【本来の強み】自らのペースを守ることで、確実かつ高品質なアウトプットを出せる力。", "solution": "🛠️ 【最適化】他人の「焦り」を自分のタスクに持ち込ませない。"}
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
            "頭脳": {"curse": "🌀 【悩み・モヤモヤ】友達の悩みまで背負い込んで、頭パンパンで疲労困憊。", "truth": "✨ 【ホントの才能】自分に必要な「ひらめき」だけを受け取れる高性能アンテナ。", "solution": "👉 【抜け出すヒント】「その悩み、私が今考えることじゃないな」とスルーしてOK。"},
            "思考": {"curse": "🌀 【悩み・モヤモヤ】「一度言ったことは変えちゃダメだ」と意地を張って、自分の首を絞めてる。", "truth": "✨ 【ホントの才能】新しい情報をどんどん取り入れて考えをアップデートできる柔軟な頭。", "solution": "👉 【抜け出すヒント】「昨日の意見と違ってもいいじゃん！進化してる証拠だよ」。"},
            "表現": {"curse": "🌀 【悩み・モヤモヤ】沈黙が怖くて、思ってもないことを話し続けて後で「あちゃー」ってなる。", "truth": "✨ 【ホントの才能】誰かに聞かれた時、一番説得力のある言葉が出てくる「待機モード」の声。", "solution": "👉 【抜け出すヒント】「話しかけられるまで、静かに余裕をかましておこう」。"},
            "自己": {"curse": "🌀 【悩み・モヤモヤ】「本当の自分」を探して、キャラ迷走中。周りに合わせすぎて疲れちゃう。", "truth": "✨ 【ホントの才能】場所や友達によって、自分を自由に変えられる「変幻自在のカメレオン」。", "solution": "👉 【抜け出すヒント】「今の環境で楽しんでる自分が、今の正解！」。"},
            "意志": {"curse": "🌀 【悩み・モヤモヤ】「もっと頑張って認められなきゃ」と、無理な約束をして自分を追い込んでる。", "truth": "✨ 【ホントの才能】頑張らなくても最初から価値がある。無理な努力はしなくていい人。", "solution": "👉 【抜け出すヒント】「やりたくないことは断っていい。君の価値は成績じゃ決まらない」。"},
            "生命力": {"curse": "🌀 【悩み・モヤモヤ】みんなが起きてるから…と、休むタイミングを逃して寝不足フラフラ。", "truth": "✨ 【ホントの才能】集中してやりきったら、あとはスッと眠りにつけるスッキリ体質。", "solution": "👉 【抜け出すヒント】「電池が切れる前に、自分から先に寝逃げしよう」。"},
            "直感": {"curse": "🌀 【悩み・モヤモヤ】「なんとなく嫌な予感」を無視して、合わないグループに居続けてストレスMAX。", "truth": "✨ 【ホントの才能】「あ、ここ危ない」と瞬時に察知する最強の防犯アラーム。", "solution": "👉 【抜け出すヒント】「なんとなく嫌」は絶対正しい。すぐに距離を置いて逃げよう。"},
            "感情": {"curse": "🌀 【悩み・モヤモヤ】気分が上がってる時やイライラしてる時に勢いで決めて、後で大後悔。", "truth": "✨ 【ホントの才能】時間をかけて自分の気持ちが落ち着くのを待てば、100点の答えが出せる。", "solution": "👉 【抜け出すヒント】「一晩寝かせてから返事するわ」が最強の決め台詞。"},
            "活力": {"curse": "🌀 【悩み・モヤモヤ】「早く出しなさい！」と急かされてパニック。焦ってミス連発。", "truth": "✨ 【ホントの才能】自分のペースで取り組めば、すごいパワーでやり切れる集中力の持ち主。", "solution": "👉 【抜け出すヒント】「人は人、私は私。他人の焦り（プレッシャー）は受け取らない」。"}
        }
    else: 
        type_strengths = {
            "生命力型": "安定した活力を持ち続けるエンジン体質。\n繰り返しの積み重ねで体と心を最高の状態へ整え、外からの呼びかけへの反応力が高い。",
            "表現する生命型": "複数のことを同時にこなす多機能型の体質。\n試行錯誤しながら最短の道を直感で見つける、素早い行動力を持つ。",
            "行動開始型": "自分から新しいことを始める力（主導権）がある体質。\nゼロから道を切り開き、他者を動かす働きかけができる。",
            "導き型": "全体の流れを高い視点から見渡せる体質。\n活力を効率よく使い、他者の状態を整えることが得意。",
            "反射型": "周囲の環境全体を映し出すセンサー体質。\n偏りなく全体の健康状態を感じ取り、公平に判断できる。"
        }
        center_issues = {
            "頭脳": {"curse": "🌀 【思い込み】「他人の疑問まで抱え込み、頭が疲れ果ててしまう」", "truth": "✨ 【本来の強み】自分に必要な気づきだけを受け取れる「感度の高いアンテナ」。", "solution": "💡 【整える言葉】「その悩みは、私が引き受けることではありません」"},
            "思考": {"curse": "🌀 【思い込み】「一度出した答えに縛られ、柔軟な思考が固まってしまう」", "truth": "✨ 【本来の強み】新しい考えをどんどん取り入れられる「柔軟な思考の器」。", "solution": "💡 【整える言葉】「昨日の私と今日の私は、成長した別の私です」"},
            "表現": {"curse": "🌀 【思い込み】「沈黙を恐れて無理に言葉を出し続け、空回りしてしまう」", "truth": "✨ 【本来の強み】外から求められたときに最大の力を発揮する「待機型の声」。", "solution": "💡 【整える言葉】「呼ばれるまで、静かに待っているのが私の自然な状態です」"},
            "自己": {"curse": "🌀 【思い込み】「固定した自分を探し続けて迷い、心が落ち着かなくなる」", "truth": "✨ 【本来の強み】いる場所や出会う人に応じて自然に向きを変える「羅針盤」。", "solution": "💡 【整える言葉】「私は環境によって変わっていい。それが私らしさです」"},
            "意志": {"curse": "🌀 【思い込み】「体の限界を超えてまで頑張り続け、負担をかけてしまう」", "truth": "✨ 【本来の強み】自分の価値を証明し続けなくていい「無重力の心」。", "solution": "💡 【整える言葉】「証明すべきことは何もない。体が無理だと言ったら止めていい」"},
            "生命力": {"curse": "🌀 【思い込み】「他人のペースに引きずられ、疲れ果ててしまう」", "truth": "✨ 【本来の強み】必要な活力を出して、用が済んだらすっと手放せる「充電不要な電池」。", "solution": "💡 【整える言葉】「今日分の活力は使い切った。体が止まれと言う前に、先に休む」"},
            "直感": {"curse": "🌀 【思い込み】「古い恐れに縛られ、合わない環境に居続けてしまう」", "truth": "✨ 【本来の強み】違和感を感じたらすぐ離れられる「体の警報装置」。", "solution": "💡 【整える言葉】「なんとなく嫌な感じがする場所・人とは、すぐ距離を置いていい」"},
            "感情": {"curse": "🌀 【思い込み】「自分の気持ちを押し込めて『いい人』を演じ続け、消耗する」", "truth": "✨ 【本来の強み】他者の感情の波を感じながら、そっと観察できる「共感の受信機」。", "solution": "💡 【整える言葉】「この感情の波は、誰かのもの。私はただ感じているだけでいい」"},
            "活力": {"curse": "🌀 【思い込み】「外からのプレッシャーで常に焦らされ、体が休まらなくなる」", "truth": "✨ 【本来の強み】外からのせかしをやり過ごし、自分のペースで動ける「独立した活力の源」。", "solution": "💡 【整える言葉】「急いでも物事は変わらない。他人の焦りは受け取らない」"}
        }
 
    DEFINED_CENTER_ISSUES_BASE = {
        "頭脳": {"curse": "🌀 【外からの思い込み】「他人の悩みにも関心を持て」", "truth": "✨ 【本来の仕組み】自分に必要な気づきだけを受け取る。", "solution": "👉 【整える言葉】「他人の悩みを自分の中に入れない。」"},
        "思考": {"curse": "🌀 【外からの思い込み】「もっと柔軟になれ」", "truth": "✨ 【本来の仕組み】一定のやり方で確実に情報を処理する。", "solution": "👉 【整える言葉】「私の考え方は生まれつきの仕様。」"},
        "表現": {"curse": "🌀 【外からの思い込み】「もっと言葉を選べ」", "truth": "✨ 【本来の仕組み】自分のスタイルで確かに言葉を出せる。", "solution": "👉 【整える言葉】「この伝え方が私の自然な声。」"},
        "自己": {"curse": "🌀 【外からの思い込み】「相手に合わせなさい」", "truth": "✨ 【本来の仕組み】自分を中心に、合う人・環境を引き寄せる。", "solution": "👉 【整える言葉】「私は動かない。合う人だけが近づいてくる」"},
        "意志": {"curse": "🌀 【外からの思い込み】「謙虚であれ」", "truth": "✨ 【本来の仕組み】確固たる意志で正当な対価を受け取る。", "solution": "👉 【整える言葉】「堂々と対価を求めていい」"},
        "生命力": {"curse": "🌀 【外からの思い込み】「頭で考えて動け」", "truth": "✨ 【本来の仕組み】体が反応した瞬間だけ、無限の活力が湧き出る。", "solution": "👉 【整える言葉】「体の奥が反応するまで、静かに待つ」"},
        "直感": {"curse": "🌀 【外からの思い込み】「根拠を出せ」", "truth": "✨ 【本来の仕組み】今この瞬間の正解を、一瞬で知らせる警報。", "solution": "👉 【整える言葉】「なんとなく嫌だから。理由は後でいい」"},
        "感情": {"curse": "🌀 【外からの思い込み】「すぐ決断しろ！」", "truth": "✨ 【本来の仕組み】時間をかけるほど本当の答えが見えてくる。", "solution": "👉 【整える言葉】「数日ゆっくり考えてからお返事します」"},
        "活力": {"curse": "🌀 【外からの思い込み】「焦らなくていい」", "truth": "✨ 【本来の仕組み】自らプレッシャーを生み出し、一気に処理する。", "solution": "👉 【整える言葉】「プレッシャーは私の力の源です」"}
    }
    return type_strengths, center_issues, DEFINED_CENTER_ISSUES_BASE
 
# =====================================================================
# ▼▼▼ 固定データ群（省略なし完全版） ▼▼▼
# =====================================================================
CUSTOM_WEIGHTS = {"Sun": 35.0, "Earth": 35.0, "Moon": 10.0, "Mercury": 4.5, "Venus": 4.0, "Mars": 3.5, "Jupiter": 3.0, "Saturn": 2.0, "Uranus": 1.5, "Neptune": 1.0, "Pluto": 0.5, "NorthNode": 1.0, "SouthNode": 1.0, "Chiron": 0.0}
DORMANT_MULTIPLIER = 0.3
FORCED_GATES = set()
GATE_SEQUENCE = [41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3, 27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56, 31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50, 28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60]
CENTER_GATES = {"頭脳": {64, 61, 63}, "思考": {47, 24, 4, 17, 43, 11}, "表現": {62, 23, 56, 31, 8, 33, 20, 16, 35, 12, 45}, "自己": {7, 1, 13, 25, 46, 2, 15, 10}, "意志": {21, 51, 26, 40}, "生命力": {34, 5, 14, 29, 59, 9, 3, 42, 27}, "直感": {48, 57, 44, 50, 32, 28, 18}, "感情": {36, 22, 37, 6, 49, 55, 30}, "活力": {58, 38, 54, 53, 60, 52, 19, 39, 41}}
CHANNELS = {"頭脳_思考": [(64,47,"64-47"), (61,24,"61-24"), (63,4,"63-4")], "思考_表現": [(17,62,"17-62"), (43,23,"43-23"), (11,56,"11-56")], "表現_自己": [(31,7,"31-7"), (8,1,"8-1"), (33,13,"33-13"), (10,20,"10-20")], "表現_意志": [(45,21,"45-21")], "表現_感情": [(35,36,"35-36"), (12,22,"12-22")], "表現_直感": [(16,48,"16-48"), (20,57,"20-57")], "表現_生命力": [(20,34,"20-34")], "自己_意志": [(25,51,"25-51")], "自己_生命力": [(5,15,"5-15"), (46,29,"46-29"), (2,14,"2-14"), (10,34,"10-34")], "自己_直感": [(10,57,"10-57")], "意志_感情": [(40,37,"40-37")], "意志_直感": [(26,44,"26-44")], "生命力_感情": [(6,59,"6-59")], "生命力_直感": [(50,27,"50-27"), (34,57,"34-57")], "生命力_活力": [(53,42,"53-42"), (3,60,"3-60"), (9,52,"9-52")], "感情_活力": [(19,49,"19-49"), (39,55,"39-55"), (41,30,"41-30")], "直感_活力": [(18,58,"18-58"), (28,38,"28-38"), (32,54,"32-54")]}
MOTOR_CENTERS = {"生命力", "意志", "感情", "活力"}
 
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
 
# =====================================================================
# ▼▼▼ 天文暦セットアップ & 計算関数 ▼▼▼
# =====================================================================
def setup_ephemeris():
    """エフェメリスファイルのセットアップ"""
    ephe_dir = './ephe_data'
    os.makedirs(ephe_dir, exist_ok=True)
    
    files_to_download = ['sepl_18.se1', 'semo_18.se1', 'seas_18.se1']
    
    for f in files_to_download:
        filepath = os.path.join(ephe_dir, f)
        if not os.path.exists(filepath):
            try:
                url = f'https://github.com/aloistr/swisseph/raw/master/ephe/{f}'
                urllib.request.urlretrieve(url, filepath)
            except Exception as e:
                st.warning(f"⚠️ エフェメリスファイル {f} のダウンロードに失敗しました: {e}")
    
    swe.set_ephe_path(ephe_dir)
 
# エフェメリスの初期化
if SWE_AVAILABLE:
    try:
        setup_ephemeris()
    except Exception as e:
        st.error(f"⚠️ エフェメリスのセットアップに失敗しました: {e}")
        st.stop()
 
def calculate_design_jd(jd_b, sun_lon):
    """デザイン日時の計算"""
    try:
        target = (sun_lon - 88.0 + 360.0) % 360.0
        jd_guess = jd_b - 89.5
        for _ in range(20):
            pos, _ = swe.calc_ut(jd_guess, swe.SUN)
            diff = (pos[0] - target + 360.0) % 360.0
            if diff > 180:
                diff -= 360.0
            jd_guess -= diff / 0.9856
            if abs(diff) < 0.00001:
                break
        return jd_guess
    except Exception as e:
        st.error(f"デザイン日時の計算エラー: {e}")
        return jd_b - 88.0
 
def get_chart_data(y, m, d, h, mi):
    """チャートデータの取得"""
    try:
        utc = datetime.datetime(y, m, d, h, mi) - datetime.timedelta(hours=9)
        jd_b = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60.0)
        sun_pos, _ = swe.calc_ut(jd_b, swe.SUN)
        jd_d = calculate_design_jd(jd_b, sun_pos[0])
        
        data = []
        # ⭐ 修正: Marsを正しい定数に変更
        planets = {
            swe.SUN: "Sun", 
            swe.MOON: "Moon", 
            swe.TRUE_NODE: "NorthNode", 
            swe.MERCURY: "Mercury", 
            swe.VENUS: "Venus", 
            swe.MARS: "Mars",  # 修正: "Mars" → swe.MARS
            swe.JUPITER: "Jupiter", 
            swe.SATURN: "Saturn", 
            swe.URANUS: "Uranus", 
            swe.NEPTUNE: "Neptune", 
            swe.PLUTO: "Pluto", 
            swe.CHIRON: "Chiron"
        }
        
        for is_red, jd in [(True, jd_d), (False, jd_b)]:
            col = "Red" if is_red else "Black"
            for p_id, p_name in planets.items():
                try:
                    pos, _ = swe.calc_ut(jd, p_id)
                    g = GATE_SEQUENCE[int(((pos[0] - 302.0 + 360.0) % 360.0) / 5.625)]
                    l = int(((pos[0] - 302.0 + 360.0) % 360.0 % 5.625) / (5.625 / 6)) + 1
                    data.append({"planet": p_name, "color": col, "gate": g, "line": l})
                    
                    if p_name == "Sun":
                        eg = GATE_SEQUENCE[int(((pos[0] + 180 - 302.0 + 360.0) % 360.0) / 5.625)]
                        el = int(((pos[0] + 180 - 302.0 + 360.0) % 360.0 % 5.625) / (5.625 / 6)) + 1
                        data.append({"planet": "Earth", "color": col, "gate": eg, "line": el})
                    
                    if p_name == "NorthNode":
                        sg = GATE_SEQUENCE[int(((pos[0] + 180 - 302.0 + 360.0) % 360.0) / 5.625)]
                        sl = int(((pos[0] + 180 - 302.0 + 360.0) % 360.0 % 5.625) / (5.625 / 6)) + 1
                        data.append({"planet": "SouthNode", "color": col, "gate": sg, "line": sl})
                except Exception as e:
                    st.warning(f"天体 {p_name} の計算エラー: {e}")
                    continue
        
        return data, jd_d
    except Exception as e:
        st.error(f"チャートデータ取得エラー: {e}")
        return [], 0
 
def generate_report_data(data, jd_d, y, m, d, h, mi, mode):
    """レポートデータの生成"""
    try:
        T_TYPE, T_CENTER, T_DEF_CENTER = get_dictionaries(mode)
        
        # データが空の場合のチェック
        if not data:
            st.error("チャートデータが生成されませんでした。")
            return None
        
        core_g = set([x["gate"] for x in data if x["planet"] != "Chiron"]) | FORCED_GATES
        
        # 🌟 定義・未定義センターの確定
        on_c = set()
        for r, cs in CHANNELS.items():
            c1, c2 = r.split('_')
            for g1, g2, cid in cs:
                if g1 in core_g and g2 in core_g:
                    on_c.update([c1, c2])
        
        off_centers = set(CENTER_ORDER) - on_c
 
        # エネルギー定義の判定
        energized_centers = set(MOTOR_CENTERS)
        if {25, 51}.issubset(core_g) or {5, 15}.issubset(core_g) or {2, 14}.issubset(core_g) or {29, 46}.issubset(core_g) or {34, 10}.issubset(core_g):
            energized_centers.add("自己")
        if {18, 58}.issubset(core_g) or {28, 38}.issubset(core_g) or {32, 54}.issubset(core_g) or {34, 57}.issubset(core_g) or {27, 50}.issubset(core_g) or {26, 44}.issubset(core_g):
            energized_centers.add("直感")
        if {34, 20}.issubset(core_g) or {12, 22}.issubset(core_g) or {35, 36}.issubset(core_g) or {21, 45}.issubset(core_g):
            energized_centers.add("表現")
 
        motor_to_throat = False
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
                    queue.extend([n for n in adj[curr] if n not in v_throat])
 
        if "生命力" in on_c:
            type_str = "表現する生命型" if motor_to_throat else "生命力型"
        else:
            if motor_to_throat:
                type_str = "行動開始型"
            elif len(on_c) > 0:
                type_str = "導き型"
            else:
                type_str = "反射型"
 
        def calc_gate_score(gate, planet):
            c = next((k for k, v in CENTER_GATES.items() if gate in v), None)
            if c in energized_centers:
                return (CUSTOM_WEIGHTS.get(planet, 0) / 2.0) * (1.0 if c in on_c else DORMANT_MULTIPLIER)
            return 0.0
 
        # 🌟【完全修正版】スコア計算ロジック（0点撲滅！）
        center_scores = {}
        total_score = 0
        for c in CENTER_ORDER:
            c_score = sum(calc_gate_score(x["gate"], x["planet"]) for x in data if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c])
            c_int = int(round(c_score))
            
            if c in off_centers:
                # 未定義（白）の場合：漏電として最低「5ポイント」
                c_int = max(c_int, 5)
            else:
                # 定義済（色つき）の場合：0点にならないよう、本来の器として最低「10ポイント」を保証
                c_int = max(c_int, 10)
                
            center_scores[c] = c_int
            total_score += c_int
 
        # プロファイルの取得
        p_sun_list = [x for x in data if x["planet"] == "Sun" and x["color"] == "Black"]
        d_sun_list = [x for x in data if x["planet"] == "Sun" and x["color"] == "Red"]
        
        if not p_sun_list or not d_sun_list:
            st.error("太陽のデータが見つかりません。")
            return None
        
        p_sun = p_sun_list[0]
        d_sun = d_sun_list[0]
        profile = f"{p_sun['line']}/{d_sun['line']}"
 
        # 🌟 HTMLテキストの生成
        spec_f = io.StringIO()
        with contextlib.redirect_stdout(spec_f):
            print(DIVIDER)
            print("**👶 あなたの基本体質と役割**")
            print(DIVIDER)
            print(f"\n【生まれつきの性質】: {type_str}\n")
            print(f"\n └ 特徴: {T_TYPE.get(type_str, '解析中')}\n")
            print(f"\n【人生の役割】: {profile}\n")
            print(f"\n └ 特性: {PROFILE_TECH_MEANINGS.get(profile, '')}\n")
 
        # 専門家向けHTML
        exp_f = io.StringIO()
        with contextlib.redirect_stdout(exp_f):
            print(f"\n【心身の統合状態 (定義型)】: 解析中\n")
            print("\n" + DIVIDER)
            print("**🔭 天体と扉の対応表**")
            print(DIVIDER)
            for p in PLANET_ORDER:
                r_list = [x for x in data if x["planet"] == p and x["color"] == "Red"]
                b_list = [x for x in data if x["planet"] == p and x["color"] == "Black"]
                
                r = r_list[0] if r_list else None
                b = b_list[0] if b_list else None
                
                if r and b:
                    print(f"{PLANET_JP.get(p, p)}")
                    print(f"<span class='unconscious-red'>先天 {r['gate']:02d}.{r['line']}</span> ║ 後天 {b['gate']:02d}.{b['line']}\n")
            
            print("\n" + DIVIDER)
            print("**🚪 身体の働き（中枢）ごとの詳細一覧**")
            print(DIVIDER)
            for c in CENTER_ORDER:
                c_gates = [(x["gate"], x["line"], x["planet"], x["color"]) for x in data if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]]
                if c_gates:
                    print(f"\n■ **{c}**\n")
                    for g, line, p, col in sorted(c_gates, key=lambda x: x[0]):
                        mean_str = GATE_TECH_MEANINGS.get(g, "")
                        if col == "Red":
                            print(f"\nー <span class='unconscious-red'>扉 {g:>2} {mean_str} (先天)</span>")
                        else:
                            print(f"\nー 扉 {g:>2} {mean_str} (後天)")
 
        return {
            "total_score": total_score, 
            "center_scores": center_scores, 
            "off_centers": off_centers,
            "on_c": on_c, 
            "T_CENTER": T_CENTER, 
            "T_DEF_CENTER": T_DEF_CENTER, 
            "html_spec": spec_f.getvalue(), 
            "html_expert": exp_f.getvalue()
        }
    except Exception as e:
        st.error(f"レポート生成エラー: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None
 
# =====================================================================
# ▼▼▼ UI描画（リアルタイム反映版） ▼▼▼
# =====================================================================
st.sidebar.header("▼ 翻訳モードの選択")
display_mode = st.sidebar.radio(
    "誰に診断結果を見せますか？", 
    ["🌿 やさしい和語（初心者・一般）", "🏫 中高生向け（学園生活・青春）", "💻 ビジネス・論理派（経営・最適化）"],
    on_change=reset_state
)
 
st.sidebar.markdown("---")
st.sidebar.header("▼ 生年月日の入力 (日本時間)")
input_date = st.sidebar.date_input("生年月日", value=datetime.date(1980, 1, 1), min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
col1, col2 = st.sidebar.columns(2)
HOUR = col1.selectbox("時", range(24), index=12)
MINUTE = col2.selectbox("分", range(60), index=30)
YEAR, MONTH, DAY = input_date.year, input_date.month, input_date.day
 
if st.sidebar.button("🌿 体質診断を開始する", on_click=reset_state):
    with st.spinner("診断中..."):
        c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
        report = generate_report_data(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE, display_mode)
        if report:
            st.session_state['report_data'] = report
            st.session_state['current_mode'] = display_mode
        else:
            st.error("診断データの生成に失敗しました。")
 
if 'report_data' in st.session_state:
    if st.session_state.get('current_mode') != display_mode:
        with st.spinner("モード切替中..."):
            c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
            report = generate_report_data(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE, display_mode)
            if report:
                st.session_state['report_data'] = report
                st.session_state['current_mode'] = display_mode
 
    rd = st.session_state['report_data']
    mode = st.session_state['current_mode']
    
    # 🌟 プレースホルダー作成
    meter_top = st.empty()
    spec_card = st.empty()
    
    st.markdown("---")
    st.info("日常の「思い込み」にチェックを入れてください。活力を奪っている原因がわかります。")
    
    # 🚨 チェックボックスセクション
    for c in CENTER_ORDER:
        with st.container():
            st.markdown(f"#### ■ **{c}**")
            t_data = rd['T_CENTER'][c] if c in rd['off_centers'] else rd['T_DEF_CENTER'][c]
            st.markdown(f"**{t_data['curse']}**")
            
            pts = rd['center_scores'][c]
            
            # session_stateの初期化チェック
            if f"chk_{c}" not in st.session_state:
                st.session_state[f"chk_{c}"] = False
            
            st.checkbox(f"👆 最近、この状態に当てはまる (-{pts} 消耗)", key=f"chk_{c}")
            
            st.markdown(f"*{t_data['truth']}*\n\n`{t_data['solution']}`")
            st.divider()
 
    # 🌟 リアルタイム計算
    deducted = sum(rd['center_scores'][c] for c in CENTER_ORDER if st.session_state.get(f"chk_{c}", False))
    current_score = max(0, rd['total_score'] - deducted)
 
    # 🌟 プレースホルダーの中身を埋める（リアルタイム更新）
    with meter_top.container():
        st.markdown(f"### 🔋 本来の器: {rd['total_score']} / {rd['total_score']}")
        blocks_top = "".join([f"<div style='width:14px;height:14px;background:#00BFFF;border-radius:2px;display:inline-block;margin:2px;'></div>" for _ in range(rd['total_score'])])
        st.markdown(f"<div style='background:#f8f9fa;padding:10px;border-radius:8px;'>{blocks_top}</div>", unsafe_allow_html=True)
 
    with spec_card.container():
        st.markdown(f"<div class='card'>\n{rd['html_spec']}\n</div>", unsafe_allow_html=True)
 
    # 🌟 一番下の「現在の活力」メーター
    st.markdown("---")
    st.markdown(f"### 📉 現在の活力: {current_score} / {rd['total_score']}")
    if deducted > 0:
        st.warning(f"⚠️ 滞りの影響で **{deducted} ポイント** 消耗しています。")
    else:
        st.success("✨ 素晴らしい！本来の力を100%発揮できています！")
        
    blocks_bottom = ""
    for i in range(rd['total_score']):
        color = "#E53935" if i < current_score else "#CFD8DC"
        blocks_bottom += f"<div style='width:14px;height:14px;background:{color};border-radius:2px;display:inline-block;margin:2px;'></div>"
    st.markdown(f"<div style='background:#f8f9fa;padding:10px;border-radius:8px;'>{blocks_bottom}</div>", unsafe_allow_html=True)
 
    # 🌟 VIPエリア（省略なし）
    with st.expander("▼ 🔒【鑑定士向け詳細データ】扉・段階・天体の詳細（※要パスコード）"):
        st.info("💡 ここから先は鑑定士（専門家）向けの命式データエリアです。")
        secret_code = st.text_input("公式LINEで配布している『秘密の合言葉（パスコード）』を入力してください：", type="password")
        if secret_code == "2026":
            st.success("認証成功！詳細データを展開します。")
            st.markdown(f"<div class='card' style='background-color:#f8f9fa;'>\n{rd['html_expert']}\n</div>", unsafe_allow_html=True)
        elif secret_code != "":
            st.error("合言葉が間違っています。")
