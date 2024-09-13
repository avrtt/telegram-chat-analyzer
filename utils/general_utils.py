import pandas as pd
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import pygeohash as pgh
import numpy as np
import re
from datetime import timedelta

import nltk

from utils.text_utils import clean_text, detect_lang

GOOGLE_URL_PATTERN = r"(https:\/\/maps\.google\.com\/\?q=-?\d+\.\d+,-?\d+\.\d+)"
GEOHASH_FOR_EXAMPLE_CHAT = ["dr72", "sr2y", "xn77", "stq4"]


def app_language():
    language = st.sidebar.selectbox('Language', ['English', 'Русский'])
    language = 'en' if language == "English" else 'ru'
    return language

def author():
    st.sidebar.markdown(f'''
        <br><span style="font-size: 15px;">Made by <a href="https://github.com/avrtt">Vladislav Averett</a></span>
    ''', unsafe_allow_html=True)

def generate_synthetic_locations(df):
    results_list = []

    dates_list = pd.date_range(df['date'].min(), df['date'].max()).to_pydatetime()
    noise_list = np.linspace(0.999997, 1.00003) # noise factor
    user_list = df['username'].unique()

    for geohash in GEOHASH_FOR_EXAMPLE_CHAT:
        lat, lng = pgh.decode(geohash)
        for i in range(2, np.random.choice(range(2, 10))):
            location_text = 'location: https://maps.google.com/?q=%s,%s' % (lat * np.random.choice(noise_list),
                                                                            lng * np.random.choice(noise_list))

            rand_timestamp = np.random.choice(dates_list) + timedelta(hours=np.random.choice(range(-10, 10)) +
                                                                            np.random.choice(range(-10, 10))/ 60)

            rand_user = np.random.choice(user_list)

            results_list.append({"date": rand_timestamp.isoformat(), "username": rand_user, "message": location_text})

    synthetic_df = pd.DataFrame(results_list)

    return pd.concat([df, synthetic_df], ignore_index=True)


def local_css(file_name):
    with open(file_name) as f:
        return '<style>{}</style>'.format(f.read())


def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"]::before {
                font-family: sans-serif;
                margin-left: 20px;
                margin-top: -300%;
                font-size: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def refer_to_load_data_section():
    language = app_language()
    title = {'en': "You need to upload your data first", 'ru': "Необходимо загрузить данные"}
    st.title(title[language])
    button_text = {'en': "Back to the upload page", 'ru': "Вернуться на страницу загрузки"}
    upload_data = st.button(button_text[language])
    if upload_data:
        switch_page("home")


def add_conversation_id(df,threshold_quantile=0.9):
    df = df.join(df[['timestamp']].shift(-1), lsuffix='', rsuffix='_prev')
    df['time_diff_minutes'] = ((df['timestamp_prev'] - df['timestamp']).dt.seconds / 60)
    df['conversation_id'] = (df['time_diff_minutes'] >= df['time_diff_minutes'].quantile(threshold_quantile)).astype(int).cumsum()
    df.loc[(df['time_diff_minutes'] >= df['time_diff_minutes'].quantile(0.8)), 'conversation_id'] -= 1
    return df.drop('timestamp_prev', axis=1)


def is_phone_numbers(username):
  pattern = r'^(?=.*[0-9])(?=.*-)(?=.*\+)[0-9\-+]+$'
  return bool(re.match(pattern, username.replace(' ','')))


def is_url(messege):
    pattern = r"http\S+"
    return bool(re.match(pattern, pattern.replace(' ', '')))


def add_metadata_to_df(df):
    df['timestamp'] = pd.to_datetime(df['date'])
    df['year'] = df['timestamp'].dt.year
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.floor('h').dt.strftime("%H:%M")
    df['week'] = df['timestamp'].dt.to_period('W').dt.start_time
    df['month'] = df['timestamp'].to_numpy().astype('datetime64[M]')
    df['day_name'] = df['timestamp'].dt.day_name()
    df['is_media'] = df['message'].str.contains('<Media omitted>')
    df['text_length'] = df['message'].apply(lambda x: len(str(x).split()))
    df['user_is_phone_number'] = df['username'].apply(lambda x: is_phone_numbers(x))
    df['message_has_phone_number'] = df['message'].apply(lambda x: is_phone_numbers(x))
    df['has_url'] = df['message'].apply(lambda x: is_url(x))
    df['clean_text'] = df['message'].apply(lambda x: clean_text(x))
    df = add_conversation_id(df)
    return df


def time_filter_change():
    st.session_state['time_filter'] = st.session_state.time_filter


def add_filters(add_side_filters=True):

    if add_side_filters:
        min_date = st.session_state['data']['date'].min()
        max_date = st.session_state['data']['date'].max()
        if min_date == max_date:
            max_date = max_date + timedelta(days=1)

        if not st.session_state.get('time_filter'):
            st.session_state['time_filter'] = min_date, max_date
            current_min_date, current_max_date = min_date, max_date
        else:
            current_min_date, current_max_date = st.session_state['time_filter']

        st.sidebar.write('')

        data_year = st.sidebar.multiselect("Year", ["All"] + list(st.session_state['data']['year'].astype(int).unique()),
                                           default='All')

        time_filter = st.sidebar.slider("Time Period", min_date, max_date, (current_min_date, current_max_date),
                                        key='time_filter', on_change=time_filter_change)

        st.sidebar.write('')

        users_filter = st.sidebar.multiselect("User", ["All"] + list(st.session_state['data']['username'].unique()),
                                              default='All')

        if "All" in users_filter or not users_filter:
            filtered_df = st.session_state['data']
        else:
            filtered_df = st.session_state['data'][st.session_state['data']['username'].isin(users_filter)]

        if "All" in data_year or not data_year:
            pass
        else:
            filtered_df = filtered_df[filtered_df['year'].astype(int).isin(data_year)]

        language = app_language()

        return filtered_df[filtered_df['date'].between(time_filter[0], time_filter[1])], time_filter[0], time_filter[1], language

    else:
        language = app_language()
        return st.session_state['data'], None, None, language

def get_locations_markers(df):
    locations_df = df[(df['message'].str.contains('maps.google.com')) &
                      (df['message'].str.contains('q='))]

    if not locations_df.empty:
        locations_df['lat'], locations_df['lon'] = zip(*locations_df['message'].str.extract(GOOGLE_URL_PATTERN)[0]\
                                                       .apply(lambda x: x.split('=')[1].split(',')))

        locations_df['lat'], locations_df['lon'] = locations_df['lat'].astype(float), locations_df['lon'].astype(float)

        relevant_indexes = [list(locations_df.index),
                            list(locations_df.index + 1),
                            list(locations_df.index - 1)]

        loc_df = st.session_state['data'].drop(['hour', 'date', 'month', 'year'], axis=1) \
            .loc[set().union(*relevant_indexes)].sort_index() \
            .merge(pd.DataFrame(zip(*relevant_indexes),
                                index=list(locations_df.index))\
                   .melt(ignore_index=False).reset_index()\
                       [['index', 'value']], left_index=True, right_on='value').drop('value', axis=1)

        html_list = []
        for index, temp_df in loc_df.groupby('index'):
            html_list.append({'index': index, "popup": temp_df[['username', 'timestamp', 'message']].to_html(index=False)})
        locations_df = locations_df.merge(pd.DataFrame(html_list), left_index=True, right_on='index')
        locations_df['geohash'] = locations_df.apply(lambda x: pgh.encode(x['lat'], x['lon'], precision=4), axis=1)

        return locations_df[['lat', 'lon', 'popup', 'username', 'timestamp', 'geohash']]

    else:
        return locations_df

