import streamlit as st
import numpy as np
from app_utils.general_utils import refer_to_load_data_section, add_logo, add_filters
from streamlit_extras.buy_me_a_coffee import button
from PIL import Image
import emoji
from app_utils.text_utils import get_top_emojis, human_format

USER_IMAGE = Image.open("add_ons/styles/logos/user_logo.jpg")


def add_metric_black_b():
    css_body_container = f'''
             <style>
                 [data-testid="stVerticalBlock"] div:nth-of-type(1)
                 [data-testid="stVerticalBlock"] {{background-color:rgba(11,20,26)}}
             </style>
             '''

    st.markdown(css_body_container, unsafe_allow_html=True)


def center_photo():
    css_center = """<style>body {
        background-color: #eee;
    }
    
    .fullScreenFrame > div {
        display: flex;
        justify-content: center;
    }</style>"""
    st.markdown(css_center, unsafe_allow_html=True)


def calc_n_user_per_row(top_n_users):

    if top_n_users % 2 == 0:
        users_per_row = top_n_users / 2
        output = [users_per_row, users_per_row]

    else:
        output = [np.floor(top_n_users / 2.0), np.ceil(top_n_users / 2.0)]

    if output[0] == 0:
        output[0] = output[1]
        output[1] = 0
    return output


def get_users_metrics(df, top_n,emoji_method, min_date, max_date):

    agg_df = df.groupby('username', as_index=False).agg(n_days=('date', 'nunique'),
                                n_messages=('username', 'count'),
                                n_conversation=('conversation_id', 'nunique'),
                                n_words=('text_length', 'sum'),
                                n_media=('is_media', 'sum'))

    totals_df = df.agg(n_days=('date', 'nunique'),
                                n_messages=('username', 'count'),
                                n_conversation=('conversation_id', 'nunique'),
                                n_words=('text_length', 'sum'),
                                n_media=('is_media', 'sum')).max(axis=1)

    top_emoji = get_top_emojis(st.session_state['data'][st.session_state['data']['date'].between(min_date, max_date)],
                               emoji_method)

    agg_df = agg_df.merge(top_emoji, on='username', how='left') \
        .sort_values('n_messages', ascending=False).reset_index(drop=True)[0:top_n]

    return agg_df, totals_df


def assign_metrics(col, totals_df, image, user_info, language, add_seperator=True, pct=True):

    sign = {'en': '%' if pct else 'N', 'ru': '%' if pct else 'N'}

    n_mes_lang_dict = {'en': f"{sign[language]} messages", 'ru': f'{sign[language]} сообщений'}
    n_wor_lang_dict = {'en': f"{sign[language]} words", 'ru': f'{sign[language]} слов'}
    n_days_lang_dict = {'en': f"{sign[language]} active days", 'ru': f'{sign[language]} активных дней'}
    n_conv_lang_dict = {'en': f"{sign[language]} conversation", 'ru': f'{sign[language]} переписка'}
    n_media_lang_dict = {'en': f"{sign[language]} media", 'ru': f'медиа'}
    emoji_lang_dict = {'en': "Top emoji", 'ru': "Топ эмодзи"}

    col.image(image, caption=user_info.username, width=100)
    col1, col2 = st.columns((2, 2))
    col1.metric(n_mes_lang_dict[language], human_format(user_info.n_messages / (totals_df.n_messages if pct else 1), pct))
    col1.metric(n_wor_lang_dict[language], human_format(user_info.n_words/ (totals_df.n_words if pct else 1), pct))
    col2.metric(n_days_lang_dict[language], human_format(user_info.n_days / (totals_df.n_days if pct else 1), pct))
    col2.metric(n_conv_lang_dict[language], human_format(user_info.n_conversation/ (totals_df.n_conversation if pct else 1), pct))

    col1.metric(n_media_lang_dict[language], human_format(user_info.n_media/ (totals_df.n_media if pct else 1), pct))
    if emoji.is_emoji(user_info.top_freq_emoji):
        col2.metric(emoji_lang_dict[language], emoji.emojize(emoji.demojize(user_info.top_freq_emoji)))
    else:
        col2.metric(emoji_lang_dict[language], 'No Emoji')

    if add_seperator:
        st.divider()


def main():

    st.set_page_config(layout="wide", page_title="User level analysis", page_icon="👫")
    add_logo()

    if 'data' not in st.session_state:
        refer_to_load_data_section()

    else:

        filtered_df, min_date, max_date, language = add_filters()

        if st.session_state.get('file_name'):
            st.header(st.session_state.get('file_name'))

        header_text = {'en': 'User-level analysis', 'ru': 'Анализ на уровне пользователя'}
        st.subheader(header_text[language])
        top_col, _ = st.columns((1000, 0.1))
        with top_col:
            pct_lang_dict = {'en': "Show percentages", "ru":'Показать проценты'}

            method_lang_dict = {'en': {"Most associated":"Most associated",
                                        "Most frequent":"Most frequent"},
                                 "ru": {"Наиболее связанные": "Most associated",
                                        "Наиболее частые": "Most frequent"}}

            pct = st.checkbox(pct_lang_dict[language])
            emohi_picker_lang_dict = {'en': "Top emoji method", 'ru':"Top emoji method"}
            emoji_method = st.radio(emohi_picker_lang_dict[language], list(method_lang_dict[language].keys()))

            emoji_method = method_lang_dict[language][emoji_method]

        top_n_users = min(filtered_df['username'].nunique(), 8)

        metrics_df, totals_df = get_users_metrics(filtered_df, top_n_users, emoji_method, min_date, max_date)

        row_a_n_users, row_b_n_users = calc_n_user_per_row(top_n_users)

        row_a = st.columns(np.array(int(row_a_n_users) * [10]))

        for col, user_info in zip(row_a, metrics_df[:int(row_a_n_users)].to_records()):

            with col:
                assign_metrics(col, totals_df, USER_IMAGE, user_info, language=language,pct=pct)

        if row_b_n_users != 0:

            for col, user_info in zip(row_a, metrics_df[int(row_b_n_users):].to_records()):
                with col:
                    assign_metrics(col,totals_df, USER_IMAGE, user_info, language=language,add_seperator=False,pct=pct)

        add_metric_black_b()


# Run the app
if __name__ == "__main__":
    main()
