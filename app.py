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

# 🌟 全ての計算と出力を統合した最強の関数
def generate_full_report(data, jd_d, y, m, d, h, mi):
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


    # --- 後半：出力パート（同期ウケ抜群のプロフェッショナル配列！） ---

    # ① 日時
    print(f"意識　（後天）　： {y}/{m:02d}/{d:02d} {h:02d}:{mi:02d}\n")
    print(f"<span class='unconscious-red'>無意識（先天）　： {dj.strftime('%Y/%m/%d %H:%M')}</span>\n")
    if is_rare: print(f"<div class='rare-alert'>★ 【特殊な特徴を検出】<br>詳細はぜひHD資格のある専門家にお問合せください！</div>\n")

    # ② 基本スペック（プロファイル・タイプ・十字・定義型）
    print(DIVIDER)
    print("**👶 基本スペック（HDプロフェッショナル分析）**")
    print(DIVIDER)
    print(f"\n【体質タイプ】: {type_str}\n")
    print(f"\n └ 特徴: {TECH_TYPE_STRENGTHS.get(type_str, '解析中')}\n")
    print(f"\n【人生のテーマ (プロファイル)】: {profile}\n")
    print(f"\n └ 特性: {PROFILE_TECH_MEANINGS.get(profile, '解析中...')}\n")
    print(f"\n【受胎十字 (インカネーションクロス)】\n")
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

    # ③ 天体データ対応表（黒・赤）
    print("\n" + "=" * 35)
    print("🔭 【詳細データ】各星と扉の対応表")
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

    # ④ ライン層別カウント表
    print("\n**【層別の構成（各層の扉の数）】**\n")
    print("<b>層 ║ <span class='unconscious-red'>先天</span> ║ 後天 ║ 合計 ║ 特性</b>\n")
    for i in range(1, 7):
        tot = red_counts[i] + black_counts[i]
        print(f" {i}層 ║ <span class='unconscious-red'>{red_counts[i]:>2}</span> │ {black_counts[i]:>2} ║ {tot:>2} ║ {TECH_LINE_MEANINGS[i]}\n")

    # ⑤ 中枢（センター）別エネルギー詳細スコア
    print("\n" + DIVIDER)
    print("👶 身体の中枢別 エネルギー状態（扉の詳細スコア）")
    print(DIVIDER)
    print(f"🔋 自発エネルギー密度: {raw_s:.1f}")
    if connected_motors:
        motors_jp = "・".join(connected_motors)
        print(f"💡 表現と連動している活力の源: {motors_jp}\n")

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

        print(f"\n■ **{c}**（{CENTER_ORGANS[c]}）\n")
        if c in ["頭脳", "思考"]: print(f"{status}\n")
        else: print(f"{status}  [小計: {c_score:.1f}🔋]\n")

        if not c_gates:
            print("ー 該当する扉なし\n")
        else:
            c_gates_sorted = sorted(c_gates, key=lambda x: x[0])
            for g, line, p, col, s in c_gates_sorted:
                score_str = f" [{s:>4.1f}]" if s > 0 else ""
                p_jp = PLANET_JP.get(p, p)
                mean_str = GATE_TECH_MEANINGS.get(g, "")
                if col == "Red": print(f"\nー <span class='unconscious-red'>扉 {g:>2} {mean_str} ({p_jp}/先天){score_str}</span>")
                else: print(f"\nー 扉 {g:>2} {mean_str} ({p_jp}/後天){score_str}")
        print("")

    # ⑥ 心身の歪み診断（アプリの独自価値！）
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

# =====================================================================
# ▼▼▼ 6. 実行ボタンと表示 ▼▼▼
# =====================================================================
if st.sidebar.button("🌿 体質診断を開始する"):
    with st.spinner("診断レポートを生成しています..."):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            c_data, jd_d = get_chart_data(YEAR, MONTH, DAY, HOUR, MINUTE)
            # 関数が1つにまとまったので、呼び出しが超シンプルに！
            generate_full_report(c_data, jd_d, YEAR, MONTH, DAY, HOUR, MINUTE)
            
        html_content = f.getvalue()

        # 🌟 カードデザインクラス (.card) を適用！
        wrapped_html = f"<div class='card'>\n{html_content}\n</div>"

        st.markdown(wrapped_html, unsafe_allow_html=True)
        st.success("診断が完了しました！")
