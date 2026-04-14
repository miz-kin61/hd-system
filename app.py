# =====================================================================
# ▼▼▼ 5. 計算・出力のロジック (統合＆順番最適化版) ▼▼▼
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

# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# ⚠️前回消してしまった「テキスト辞書データ」を復活！
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
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
        "curse": "🌀 【外から植えつけられた思い込み】「いつも明確なビジョンを持て」「自分で考えろ」\n\n └ 他人の疑問（余計な心配ごと）を自分のことのように抱え込み、頭が疲れ果ててしまう。",
        "truth": "✨ 【本来の体の仕組み】必要な気づきだけを受け取れる「感度の高いアンテナ」。",
        "solution": "🌿 【心身を整えるための言葉】「その悩みは、私が引き受けることではありません」"
    },
    "思考": {
        "curse": "🌀 【外から植えつけられた思い込み】「一貫性を持て」「意見をころころ変えるな」\n\n └ 一度出した答えに無理やり縛られ、本来の柔軟な思考が固まってしまう。",
        "truth": "✨ 【本来の体の仕組み】新しい考えをどんどん取り入れられる「柔軟な思考の器」。",
        "solution": "🌿 【心身を整えるための言葉】「昨日の私と今日の私は、成長した別の私です」"
    },
    "表現": {
        "curse": "🌀 【外から植えつけられた思い込み】「自分から発言しろ」「沈黙は気まずい」\n\n └ 沈黙を恐れて無理に言葉を出し続け、心身が空回りしてしまう。",
        "truth": "✨ 【本来の体の仕組み】外から求められたときに最大の力を発揮する「待機型の声」。",
        "solution": "🌿 【心身を整えるための言葉】「呼ばれるまで、静かに待っているのが私の自然な状態です」"
    },
    "自己": {
        "curse": "🌀 【外から植えつけられた思い込み】「自分探しをしろ」「確固たる自分を持て」\n\n └ 固定した「本当の自分」を探し続けて迷い、心が落ち着かなくなる。",
        "truth": "✨ 【本来の体の仕組み】いる場所や出会う人に応じて自然に向きを変える「羅針盤」。",
        "solution": "🌿 【心身を整えるための言葉】「私は環境によって変わっていい。それが私らしさです」"
    },
    "意志": {
        "curse": "🌀 【外から植えつけられた思い込み】「約束は必ず守れ」「努力して価値を証明しろ」\n\n └ 体の限界を超えてまで頑張り続け、心臓や胆嚢に負担をかけてしまう。",
        "truth": "✨ 【本来の体の仕組み】自分の価値を証明し続けなくていい「無重力の心」。",
        "solution": "🌿 【心身を整えるための言葉】「証明すべきことは何もない。体が無理だと言ったら止めていい」"
    },
    "生命力": {
        "curse": "🌀 【外から植えつけられた思い込み】「途中で投げ出すな」「周りが働いているのに休むな」\n\n └ 他人のペースに引きずられ、休むべきタイミングを見失って疲れ果ててしまう。",
        "truth": "✨ 【本来の体の仕組み】必要な分だけ力を出して、用が済んだらすっと手放せる「充電不要な電池」。",
        "solution": "🌿 【心身を整えるための言葉】「今日分の力は使い切った。体が止まれと言う前に、先に休む」"
    },
    "直感": {
        "curse": "🌀 【外から植えつけられた思い込み】「石の上にも三年」「手放すのはもったいない」\n\n └ 「今離れると怖い」という古い恐れに縛られ、体や心に合わない環境に居続けてしまう。",
        "truth": "✨ 【本来の体の仕組み】違和感を感じたら、過去に縛られずすぐに離れられる「体の警報装置」。",
        "solution": "🌿 【心身を整えるための言葉】「なんとなく嫌な感じがする場所・人とは、すぐ距離を置いていい」"
    },
    "感情": {
        "curse": "🌀 【外から植えつけられた思い込み】「空気を読め」「感情的になるな」\n\n └ 衝突を恐れるあまり、自分の気持ちを押し込めて「いい人」を演じ続け、内側が疲弊する。",
        "truth": "✨ 【本来の体の仕組み】他者の感情の波を感じながら、そっと観察できる「共感の受信機」。",
        "solution": "🌿 【心身を整えるための言葉】「この感情の波は、誰かのもの。私はただ感じているだけでいい」"
    },
    "活力": {
        "curse": "🌀 【外から植えつけられた思い込み】「早く終わらせろ」「やることを溜めるな」\n\n └ 外からのプレッシャーで常に焦らされ、体が休まらなくなってしまう。",
        "truth": "✨ 【本来の体の仕組み】外からのせかしをやり過ごし、自分のペースで動ける「独立した活力の源」。",
        "solution": "🌿 【心身を整えるための言葉】「急いでも物事は変わらない。他人の焦りは受け取らなくていい」"
    }
}

DEFINED_CENTER_ISSUES = {
    "頭脳": {
        "curse": "🌀 【外から植えつけられた思い込み】「他人の悩みにも関心を持て」「もっと周りを見ろ」\n\n └ 自分には関係のない心配ごとまで引き受けようとして、本来の閃きが妨げられてしまう。",
        "truth": "✨ 【本来の体の仕組み】自分に必要な気づきだけをピンポイントで受け取る「専用の受信機」。",
        "solution": "🌿 【心身を整えるための言葉】「他人の悩みを自分の中に入れない。興味のないことは受け取らなくていい」"
    },
    "思考": {
        "curse": "🌀 【外から植えつけられた思い込み】「もっと柔軟になれ」「頑固は悪いことだ」\n\n └ 自分の確かな思考プロセスを否定し、無理に他人に合わせようとして判断が狂ってしまう。",
        "truth": "✨ 【本来の体の仕組み】一定のやり方で確実に情報を処理する「安定した思考の仕組み」。",
        "solution": "🌿 【心身を整えるための言葉】「私の考え方は生まれつきの仕様。同調せずに、自分の見解として伝えればいい」"
    },
    "表現": {
        "curse": "🌀 【外から植えつけられた思い込み】「もっと言葉を選べ」「言い方がきつい」\n\n └ 安定した自分の表現方法を無理に変えようとして、全身にストレスがかかってしまう。",
        "truth": "✨ 【本来の体の仕組み】自分のスタイルで確かに言葉を出せる「生まれつきの表現の出口」。",
        "solution": "🌿 【心身を整えるための言葉】「この伝え方が私の自然な声。変える必要はありません」"
    },
    "自己": {
        "curse": "🌀 【外から植えつけられた思い込み】「相手に合わせなさい」「協調性を持て」\n\n └ 本来安定している自分の軸を無理に変えようとして、自分が何者かわからなくなってしまう。",
        "truth": "✨ 【本来の体の仕組み】自分を中心に、合う人・環境を引き寄せる「固定された羅針盤」。",
        "solution": "🌿 【心身を整えるための言葉】「私は動かない。私に合う人だけが自然に近づいてくる」"
    },
    "意志": {
        "curse": "🌀 【外から植えつけられた思い込み】「謙虚であれ」「お金を求めるのははしたない」\n\n └ 自分の価値を安売りして正当な見返りを受け取らず、心身の基盤がすり減ってしまう。",
        "truth": "✨ 【本来の体の仕組み】確固たる意志で約束を果たし、正当な対価を受け取る権利がある「本格稼働の体」。",
        "solution": "🌿 【心身を整えるための言葉】「安売りは体の消耗につながる。自分の価値を認め、堂々と対価を求めていい」"
    },
    "生命力": {
        "curse": "🌀 【外から植えつけられた思い込み】「頭で考えて計画的に動け」「自分から発信しろ」\n\n └ 外からの働きかけを待たずに思考で無理に動こうとして、空回りして疲労だけが溜まっていく。",
        "truth": "✨ 【本来の体の仕組み】外からの呼びかけに「体が反応した瞬間」だけ、無限の力が湧き出る「反応型の生命力」。",
        "solution": "🌿 【心身を整えるための言葉】「頭で考えて動かない。体の奥が反応するまで、静かに待つ」"
    },
    "直感": {
        "curse": "🌀 【外から植えつけられた思い込み】「直感だけで動くな」「根拠を出せ」\n\n └ 瞬間の体の警告を無視して理屈を探し、結局タイミングを逃して危険な目に遭う。",
        "truth": "✨ 【本来の体の仕組み】今この瞬間の正解を、理由なく一瞬で知らせる「超高速の体の警報」。",
        "solution": "🌿 【心身を整えるための言葉】「なんとなく嫌だから、そうする。理由は後からでいい」"
    },
    "感情": {
        "curse": "🌀 【外から植えつけられた思い込み】「すぐ決断しろ！」「チャンスを逃すな、今すぐ決めろ！」\n\n └ 感情の高ぶりや落ち込みのどん底で焦って決めてしまい、後から大きく後悔することになる。",
        "truth": "✨ 【本来の体の仕組み】時間をかけるほど本当の答えがはっきり見えてくる「熟成型の決断力」。",
        "solution": "🌿 【心身を整えるための言葉】「素晴らしいお話ですね。数日ゆっくり考えてからお返事します」"
    },
    "活力": {
        "curse": "🌀 【外から植えつけられた思い込み】「自分のペースでゆっくりやれ」「焦らなくていい」\n\n └ 本来持っている「プレッシャーを力に変える機能」を抑えられ、本来の爆発力が出せない。",
        "truth": "✨ 【本来の体の仕組み】自らプレッシャーを生み出し、一気に物事を処理する「瞬発力型の活力」。",
        "solution": "🌿 【心身を整えるための言葉】「私はぎりぎりの方が燃える。プレッシャーは私の力の源です」"
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

# 🌟 全ての計算と出力を「一般向け」と「専門向け」に分けた最強の関数
def generate_reports(data, jd_d, y, m, d, h, mi):
    # --- 前半：全ての計算処理 ---
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

    raw_s = sum([calc_gate_score(x["gate"], x["planet"]) for x in data if x["planet"] != "Chiron"])

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

    # =========================================================
    # ▼ 前半パート：一般人（フロント）向け レポート作成
    # =========================================================
    gen_f = io.StringIO()
    with contextlib.redirect_stdout(gen_f):
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

        print("\n" + DIVIDER)
        print("🚨 心身の歪み診断（外からの影響による不調と、整えるための言葉）")
        print(DIVIDER)
        all_centers = set(CENTER_GATES.keys())
        off_centers = all_centers - set(on_c)
        full_open = [c for c in off_centers if len(CENTER_GATES[c] & set(core_g)) == 0]

        if not off_centers and not on_c: print("  すべての中枢が感受性の高い状態です。\n")

        for c in ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]:
            print(f"\n■ **{c}**（{CENTER_ORGANS[c]}）\n")
            if c in off_centers:
                status_text = "完全に感受性が開いている（外の影響を強く受ける）" if c in full_open else "感受性が高い（外から影響を受けやすい）"
                print(f"状態: {status_text}\n\n")
                print(f"{CENTER_ISSUES[c]['curse']}\n\n")
                print(f"{CENTER_ISSUES[c]['truth']}\n\n")
                print(f"{CENTER_ISSUES[c]['solution']}\n")
            else:
                print("状態: 活性化している（安定したエネルギーが流れている）\n\n")
                if c in DEFINED_CENTER_ISSUES:
                    print(f"{DEFINED_CENTER_ISSUES[c]['curse']}\n\n")
                    print(f"{DEFINED_CENTER_ISSUES[c]['truth']}\n\n")
                    print(f"{DEFINED_CENTER_ISSUES[c]['solution']}\n")
                else:
                    print(" （安定したエネルギーの中枢として、正常に働いています）\n")

        print("\n" + DIVIDER)
        print("🔋 身体の中枢別 エネルギー状態（概要）")
        print(DIVIDER)
        print(f"全体の自発エネルギー密度: {raw_s:.1f} 🔋")
        if connected_motors:
            motors_jp = "・".join(connected_motors)
            print(f"💡 表現と連動している活力の源: {motors_jp}\n")

        center_order = ["頭脳", "思考", "表現", "自己", "意志", "生命力", "直感", "感情", "活力"]
        for c in center_order:
            c_score = 0.0
            status = "活性化している" if c in on_c else "感受性が高い（外から影響を受けやすい）"
            for x in data:
                if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]:
                    s = calc_gate_score(x["gate"], x["planet"])
                    c_score += s

            print(f"\n■ **{c}**（{CENTER_ORGANS[c]}）\n")
            if c in ["頭脳", "思考"]: print(f"{status}\n")
            else: print(f"{status}  [小計: {c_score:.1f}🔋]\n")

    general_html = gen_f.getvalue()

    # =========================================================
    # ▼ 後半パート：専門家（マニア）向け 詳細データ出力
    # =========================================================
    exp_f = io.StringIO()
    with contextlib.redirect_stdout(exp_f):
        print(f"【受胎十字 (インカネーションクロス)】\n")
        print(f"\n └ 先天(無意識): 太陽 {d_sun['gate']:>2} / 地球 {d_earth['gate']:>2}\n")
        print(f"\n └ 後天(意　識): 太陽 {p_sun['gate']:>2} / 地球 {p_earth['gate']:>2}\n")
        
        print(f"\n【心身の統合状態 (定義型)】: {definition_type}\n")
        if "特殊二系統型" in definition_type:
            print("\n └ 特徴: 島が遠く離れており、1つの扉では繋がりません。他者との関わりを通じて時間をかけて全体を統合していく体質です。\n")
        if len(initial_islands) <= 1:
            print("🌟 橋渡しの扉: なし（全体がひとつにつながっています）\n")
        else:
            if b_gates_1:
                bg_list = sorted(list(set(b_gates_1)))
                print(f"🌟 橋渡しの扉: {bg_list}\n")
            elif b_gates_2:
                combo_strs = [f"[{bg1}, {bg2}]" for bg1, bg2 in b_gates_2]
                print(f"🌟 広域の橋渡しの扉:\n   {', '.join(combo_strs)}\n")

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
                p_jp = PLANET_JP.get(p, p)
                print(f"{p_jp}")
                print(f"<span class='unconscious-red'>先天 {r['gate']:02d}.{r['line']}{r_sc}</span> ║ 後天 {b['gate']:02d}.{b['line']}{b_sc}\n")

        print("\n" + DIVIDER)
        print("🚪 中枢ごとの扉（ゲート）の詳細一覧")
        print(DIVIDER)
        for c in center_order:
            c_gates = []
            for x in data:
                if x["planet"] != "Chiron" and x["gate"] in CENTER_GATES[c]:
                    s = calc_gate_score(x["gate"], x["planet"])
                    c_gates.append((x["gate"], x["line"], x["planet"], x["color"], s))

            if c_gates:
                print(f"\n■ **{c}**\n")
                c_gates_sorted = sorted(c_gates, key=lambda x: x[0])
                for g, line, p, col, s in c_gates_sorted:
                    score_str = f" [{s:>4.1f}]" if s > 0 else ""
                    p_jp = PLANET_JP.get(p, p)
                    mean_str = GATE_TECH_MEANINGS.get(g, "")
                    if col == "Red": print(f"\nー <span class='unconscious-red'>扉 {g:>2} {mean_str} ({p_jp}/先天){score_str}</span>")
                    else: print(f"\nー 扉 {g:>2} {mean_str} ({p_jp}/後天){score_str}")

        print("\n" + DIVIDER)
        print("📊 層別の構成（各層の扉の数）")
        print(DIVIDER)
        print("<b>層 ║ <span class='unconscious-red'>先天</span> ║ 後天 ║ 合計 ║ 特性</b>\n")
        for i in range(1, 7):
            tot = red_counts[i] + black_counts[i]
            print(f" {i}層 ║ <span class='unconscious-red'>{red_counts[i]:>2}</span> │ {black_counts[i]:>2} ║ {tot:>2} ║ {TECH_LINE_MEANINGS[i]}\n")

    expert_html = exp_f.getvalue()
    return general_html, expert_html


# =====================================================================
# ▼▼▼ 6. 実行ボタンと表示 ▼▼▼
# =====================================================================
if st.sidebar.button("🌿 体質診断を開始する"):
    with st.spinner("診断レポートを生成しています..."):
        c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
        
        # 関数を呼び出して、2つのHTML（一般用・専門用）を受け取る
        general_html, expert_html = generate_reports(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE)
        
        # 🌟 一般向けレポート（フロント部分）をドカンと表示
        st.markdown(f"<div class='card'>\n{general_html}\n</div>", unsafe_allow_html=True)
        
        # 🌟 専門データは画面の一番下で「折りたたみ（アコーディオン）」にする！
        with st.expander("▼ 【専門データ】ゲート・ライン・天体の詳細設定を開く"):
            st.markdown(f"<div class='card' style='background-color:#f8f9fa;'>\n{expert_html}\n</div>", unsafe_allow_html=True)

        st.success("診断が完了しました！")
