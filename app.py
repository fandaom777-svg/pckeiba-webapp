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


def waku_badge(wakuban):
    bg, fg = WAKU_COLORS.get(str(wakuban), ('#CCCCCC', '#000000'))
    border = 'border: 1px solid #888;' if str(wakuban) == '1' else ''
    return (
        f'<span style="display:inline-block; width:1.8em; height:1.8em; line-height:1.8em; '
        f'text-align:center; border-radius:4px; background-color:{bg}; color:{fg}; '
        f'{border} font-weight:bold;">{wakuban}</span>'
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

st.subheader(f'{selected_date} {selected_track} {int(selected_race)}R')

rows_html = ''
for _, row in df_race.iterrows():
    rows_html += (
        '<tr>'
        f'<td style="text-align:center; padding:4px;">{waku_badge(row["wakuban_int"])}</td>'
        f'<td style="text-align:center; padding:4px;">{row["umaban_int"]}</td>'
        f'<td style="text-align:center; padding:4px; font-size:1.2em;">{row["mark"]}</td>'
        f'<td style="padding:4px;">{row["bamei"]}</td>'
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
