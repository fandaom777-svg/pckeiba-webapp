import streamlit as st
import pandas as pd

st.set_page_config(page_title="競馬予測", page_icon="🐎")

KEIBAJO_NAMES = {
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟', '05': '東京',
    '06': '中山', '07': '中京', '08': '京都', '09': '阪神', '10': '小倉',
}

# 実際の競馬中継・出馬表と同じ枠番の配色(背景色, 文字色)
WAKU_COLORS = {
    '1': ('#FFFFFF', '#000000'),
    '2': ('#000000', '#FFFFFF'),
    '3': ('#FF0000', '#FFFFFF'),
    '4': ('#0000FF', '#FFFFFF'),
    '5': ('#FFFF00', '#000000'),
    '6': ('#00A550', '#FFFFFF'),
    '7': ('#FF8C00', '#000000'),
    '8': ('#FF69B4', '#000000'),
}

# ◎○は円形の記号でフォントのem目一杯を使うため小さめのfont-sizeで、
# ▲△は三角形の記号でem内での見た目の面積が小さいため大きめのfont-sizeで
# 表示することで、見た目の大きさを揃える
MARK_FONT_SIZES = {
    '◎': '0.95em',
    '○': '1.65em',
    '▲': '1.55em',
    '△': '1.55em',
}

# grade_code(jvd_ra)に対応する格付け表記
GRADE_SUFFIX = {
    'A': 'GⅠ', 'B': 'GⅡ', 'C': 'GⅢ',
    'F': 'J.GⅠ', 'G': 'J.GⅡ', 'H': 'J.GⅢ',
    'L': 'L',
}

# AI予測ランク(S+/S/A/B/C、2026-09-09〜)。「AI予測の条件別信頼性」調査に基づく
# レース単位の参考ランク(◎○▲△の決定には使わない)。色は暖色=積極、寒色=中立、
# グレー/警告色=見送り・要注意という直感に沿わせている
RANK_INFO = {
    'S+': ('本命型', '#B8860B', '◎が単勝2.5倍以下。的中率は高いが配当は伸びにくいため、'
                                '点数を絞る・ワイド中心などの買い方も検討'),
    'S': ('黄金ゾーン', '#1a7f37', '検証上、通常の三連複流しで最も回収率が高かった条件'),
    'A': ('妙味', '#0969da', '一見僅差だが、検証上むしろ好成績だった条件'),
    'B': ('標準', '#57606a', '平均的な条件(AIとオッズが食い違うケースを含む)'),
    'C': ('混戦・見送り推奨', '#cf222e', '検証上、最も成績が悪かった条件'),
}


def number_badge(number, wakuban):
    bg, fg = WAKU_COLORS.get(str(wakuban), ('#CCCCCC', '#000000'))
    border = 'border: 1px solid #888;' if str(wakuban) == '1' else ''
    return (
        f'<span style="display:inline-flex; align-items:center; justify-content:center; '
        f'width:1.8em; height:1.8em; border-radius:4px; background-color:{bg}; color:{fg}; '
        f'{border} font-weight:bold;">{number}</span>'
    )


def mark_badge(mark):
    if not mark:
        return ''
    font_size = MARK_FONT_SIZES.get(mark, '1.3em')
    return (
        f'<span style="display:inline-flex; align-items:center; justify-content:center; '
        f'width:1.6em; height:1.6em; font-size:{font_size}; line-height:1;">{mark}</span>'
    )


def check_password():
    if st.session_state.get('authenticated'):
        return True

    st.title('競馬予測 ログイン')
    password = st.text_input('パスワード', type='password')
    if st.button('ログイン'):
        if password == st.secrets.get('APP_PASSWORD', ''):
            st.session_state['authenticated'] = True
            st.rerun()
        else:
            st.error('パスワードが違います')
    return False


if not check_password():
    st.stop()

st.title('競馬予測')

try:
    df = pd.read_csv('predictions_latest.csv', dtype=str)
except FileNotFoundError:
    st.error('予測データがまだありません。しばらくしてから再度アクセスしてください。')
    st.stop()

df['date_disp'] = df['kaisai_nen'] + '/' + df['kaisai_tsukihi'].str[:2] + '/' + df['kaisai_tsukihi'].str[2:]
df['keibajo_name'] = df['keibajo_code'].map(KEIBAJO_NAMES).fillna(df['keibajo_code'])

dates = sorted(df['date_disp'].unique())
selected_date = st.selectbox('日付', dates)
df_date = df[df['date_disp'] == selected_date]

tracks = sorted(df_date['keibajo_name'].unique())
selected_track = st.selectbox('開催場', tracks)
df_track = df_date[df_date['keibajo_name'] == selected_track]

race_nums = sorted(df_track['race_bango'].unique(), key=int)
selected_race = st.selectbox('レース番号', race_nums, format_func=lambda r: f'{int(r)}R')
df_race = df_track[df_track['race_bango'] == selected_race].copy()

df_race['umaban_int'] = df_race['umaban'].astype(int)
df_race['wakuban_int'] = df_race['wakuban'].astype(int)
df_race = df_race.sort_values('umaban_int')
df_race['mark'] = df_race['mark'].fillna('')
df_race['bamei'] = df_race['bamei'].str.strip()

# レース名(特別・重賞のみ): 列が無い場合(未反映のCSV)は従来通り「XXR」のみ表示
race_title = f'{selected_track}{int(selected_race)}R'
if 'kyosomei_ryakusho_10' in df_race.columns:
    race_name = str(df_race['kyosomei_ryakusho_10'].iloc[0] or '').strip()
    if race_name and race_name.lower() != 'nan':
        grade_code = str(df_race['grade_code'].iloc[0] or '').strip() if 'grade_code' in df_race.columns else ''
        race_title += race_name + GRADE_SUFFIX.get(grade_code, '')
st.markdown(f'<div style="font-size:1.1rem; font-weight:600; margin-bottom:0.2em;">{race_title}</div>',
            unsafe_allow_html=True)

# 参考情報: ◎(ランキングモデル)と指数1位(二値分類モデル)が一致しているか。
# 過去の検証で一致率72.3%・一致時の方が的中率/回収率が高い傾向を確認済み(モデルの統合はしない、
# あくまで参考表示)
if 'ai_agree' in df_race.columns and pd.notna(df_race['ai_agree'].iloc[0]):
    if float(df_race['ai_agree'].iloc[0]) == 1:
        agree_html = '<span style="color:#1a7f37;">◎と指数1位が一致</span>'
    else:
        agree_html = '<span style="color:#888;">◎と指数1位が不一致</span>'
    st.markdown(f'<div style="font-size:0.8rem; margin-bottom:0.4em;">{agree_html}</div>',
                unsafe_allow_html=True)

# AI予測ランク(参考表示): レース単位のS+/S/A/B/C/Dバッジ
if 'ai_rank' in df_race.columns and pd.notna(df_race['ai_rank'].iloc[0]):
    rank_value = str(df_race['ai_rank'].iloc[0]).strip()
    label, color, desc = RANK_INFO.get(rank_value, (rank_value, '#57606a', ''))
    rank_html = (
        f'<span style="display:inline-block; padding:0.1em 0.5em; border-radius:4px; '
        f'background-color:{color}; color:#FFFFFF; font-weight:bold; font-size:0.9rem;">'
        f'{rank_value} {label}</span>'
        f'<span style="font-size:0.75rem; color:#888; margin-left:0.5em;">{desc}</span>'
    )
    st.markdown(f'<div style="margin-bottom:0.4em;">{rank_html}</div>', unsafe_allow_html=True)

# 参考情報: Cランク限定「オッズ差による◎ダウングレード」ルール(2026-09-11〜)。
# 単勝オッズで◯の方が明確に人気(オッズ差>1.0)な場合に◎◯を入れ替えて表示している。
# CSVはdtype=strで読むため、pandasが書き出す真偽値はTrue/Falseの文字列になる点に注意
# (過去にai_agreeで同様の落とし穴があり== 1比較のバグを出した経緯がある)
if 'axis_taikou_swapped' in df_race.columns and (df_race['axis_taikou_swapped'] == 'True').any():
    st.markdown(
        '<div style="font-size:0.8rem; color:#bf8700; margin-bottom:0.4em;">'
        '⚠️ オッズ差ルールにより◎◯を入れ替え表示(単勝オッズで◯の方が明確に人気だったため)</div>',
        unsafe_allow_html=True)

has_index_score = 'index_score' in df_race.columns

rows_html = ''
for _, row in df_race.iterrows():
    bamei_disp = row['bamei']
    if has_index_score and pd.notna(row['index_score']):
        bamei_disp += f' {int(float(row["index_score"]))}'
    rows_html += (
        '<tr>'
        f'<td style="text-align:center; padding:4px;">{number_badge(row["wakuban_int"], row["wakuban_int"])}</td>'
        f'<td style="text-align:center; padding:4px;">{number_badge(row["umaban_int"], row["wakuban_int"])}</td>'
        f'<td style="text-align:center; padding:4px;">{mark_badge(row["mark"])}</td>'
        f'<td style="padding:4px;">{bamei_disp}</td>'
        '</tr>'
    )

table_html = f"""
<table style="border-collapse:collapse; width:100%;">
  <thead>
    <tr>
      <th style="text-align:center; padding:4px;">枠番</th>
      <th style="text-align:center; padding:4px;">馬番</th>
      <th style="text-align:center; padding:4px;">印</th>
      <th style="text-align:left; padding:4px;">馬名</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
"""
st.markdown(table_html, unsafe_allow_html=True)

# ===== 資金配分レコメンド(参考表示、2026-09-09〜): S+/S/A/Bランクの馬連・三連複について、
# 相手馬の単勝オッズ逆比例で1万円を配分した場合の推奨金額(generate_predictions.pyで算出)。
# 検証(simulate_stake_allocation.py)で均等配分より安定して優れていたオッズ逆比例配分を採用。
# あくまで参考情報であり、実際の購入判断・金額はユーザー自身の判断に委ねる。
try:
    stake_df = pd.read_csv('stake_recommendations.csv', dtype=str)
except FileNotFoundError:
    stake_df = None

if stake_df is not None and len(df_race) > 0:
    key_cols_stake = ['kaisai_nen', 'kaisai_tsukihi', 'keibajo_code', 'kaisai_kai', 'kaisai_nichime', 'race_bango']
    race_key_vals = df_race.iloc[0][key_cols_stake]
    mask = pd.Series(True, index=stake_df.index)
    for col in key_cols_stake:
        if col in stake_df.columns:
            mask &= (stake_df[col] == race_key_vals[col])
        else:
            mask &= False
    stake_race = stake_df[mask]
    if len(stake_race) > 0:
        st.markdown(
            '<div style="font-size:0.85rem; font-weight:600; margin-top:0.8em;">推奨資金配分(参考、1万円あたり)</div>',
            unsafe_allow_html=True)
        for bet_type in ['馬連', '三連複']:
            sub = stake_race[stake_race['bet_type'] == bet_type].copy()
            if len(sub) == 0:
                continue
            sub['suggested_amount'] = sub['suggested_amount'].astype(float).astype(int)
            sub = sub.sort_values('suggested_amount', ascending=False)
            rows_stake = ''.join(
                f'<tr><td style="padding:2px 8px;">{r["combo"]}</td>'
                f'<td style="padding:2px 8px; text-align:right;">{r["suggested_amount"]:,}円</td></tr>'
                for _, r in sub.iterrows()
            )
            st.markdown(
                f'<div style="font-size:0.78rem; color:#888; margin-top:0.4em;">{bet_type}</div>'
                f'<table style="font-size:0.8rem; border-collapse:collapse;"><tbody>{rows_stake}</tbody></table>',
                unsafe_allow_html=True)
