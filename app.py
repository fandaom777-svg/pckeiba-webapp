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
st.markdown(f'<div style="font-size:1.1rem; font-weight:600; margin-bottom:0.4em;">{race_title}</div>',
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
