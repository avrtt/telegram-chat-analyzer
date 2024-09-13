import pandas as pd
import streamlit as st
import json
import requests

from streamlit_folium import st_folium
import folium

from time import sleep
from random import randint
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

from app_utils.general_utils import refer_to_load_data_section, add_logo, add_filters, \
    get_locations_markers, local_css
from app_utils.graphs_utils import generate_geo_barchart, generate_geo_piehart
from streamlit_extras.buy_me_a_coffee import button

user_agent = 'user_me_{}'.format(randint(10000,99999))
geolocator = Nominatim(user_agent=user_agent)


def filter_locations_df(df, locations_df, min_date, max_date):

    filtered_locations_df = df[(df['timestamp'].dt.date.between(min_date, max_date)) &
                               df['username'].isin(locations_df['username'].unique())]

    return filtered_locations_df


def map_query(latitude, longitude, sleep_sec=3):
    sleep_sec = randint(1 * 100, sleep_sec * 100) / 100
    try:
        return geolocator.reverse((latitude, longitude)).raw
    except GeocoderTimedOut:
        logging.info('TIMED OUT: GeocoderTimedOut: Retrying...')
        sleep(randint(1 * 100, sleep_sec * 100) / 100)
        return map_query(geolocator, (latitude, longitude), sleep_sec).raw
    except GeocoderServiceError as e:
        logging.info('CONNECTION REFUSED: GeocoderServiceError encountered.')
        logging.error(e)
        return None
    except Exception as e:
        logging.info('ERROR: Terminating due to exception {}'.format(e))
        return None


def get_locations_details(locations_df):

    progress_text = "Resolving lat lng to address. Please wait."
    location_resolver_bar = st.progress(0, text=progress_text)

    address_list = []

    for index, item in enumerate(locations_df[['lat', 'lon']].values):
        lat, lng = item
        locations_details_df = map_query(longitude=lng, latitude=lat)
        if locations_details_df.get('address'):
            address_list.append(locations_details_df.get('address'))
        location_resolver_bar.progress(((index + 1) / len(locations_df)), text=progress_text)

    location_resolver_bar.empty()

    return locations_df.drop(["popup", 'geohash'], axis=1).join(pd.DataFrame(address_list))


def main():
    st.set_page_config(layout="wide", page_title="Geographics", page_icon="🌎")
    add_logo()

    if 'data' not in st.session_state:
        refer_to_load_data_section()

    else:
        filtered_df, min_date, max_date, language = add_filters()

        locations_df = get_locations_markers(filtered_df)

        if st.session_state.get('file_name'):
            st.header(st.session_state.get('file_name'))

        header_text = {'en': 'Geographics', 'ru': 'География'}
        st.subheader(header_text[language])

        if not locations_df.empty:
            st.markdown(local_css("add_ons/styles/metrics.css"), unsafe_allow_html=True)

            top_freq_geohash = locations_df['geohash'].value_counts().index[0]

            m = folium.Map(location=locations_df[locations_df['geohash'] == top_freq_geohash][['lat', 'lon']].mean().values.tolist(),
                           zoom_start=15, tiles='cartodbpositron')

            sw = locations_df[locations_df['geohash'] == top_freq_geohash][['lat', 'lon']].min().values.tolist()
            ne = locations_df[locations_df['geohash'] == top_freq_geohash][['lat', 'lon']].max().values.tolist()

            m.fit_bounds([sw, ne])

            for i in locations_df.to_dict('records'):
                folium.Marker(location=[i['lat'], i['lon']], popup=i['popup'],
                              tooltip=i['username']+'<br>'+i['timestamp'].date().isoformat()).add_to(m)

            col1, col2 = st.columns((10, 6))
            loc_lang_dict = {'en': "Overall locations", "ru": 'Всего локаций'}
            users_lang_dict = {'en': "Overall users with locations", "ru": 'Всего пользователей с локациями'}
            col1.metric(loc_lang_dict[language], locations_df.shape[0])
            col2.metric(users_lang_dict[language], locations_df['username'].nunique())
            col2, col3 = st.columns((10, 6))

            with col2:
                st_folium(m, width=2000, height=500, returned_objects=[], use_container_width=True)

            with col3:
                if ('geo_data' not in st.session_state) or (len(locations_df) > len(st.session_state['geo_data'])):
                    st.session_state['geo_data'] = get_locations_details(locations_df)

                filtered_locations_df = filter_locations_df(st.session_state['geo_data'], locations_df, min_date, max_date)
                st.plotly_chart(generate_geo_piehart(filtered_locations_df, language), use_container_width=True)

            filtered_locations_df = filter_locations_df(st.session_state['geo_data'], locations_df, min_date, max_date)
            general_col, _ = st.columns((1000, 1))
            with general_col:
                road_city_lang_dict = {'en': 'Top cities & roads', 'ru': 'Города и дороги (топ)'}
                st.subheader(road_city_lang_dict[language])
                col4, col5 = st.columns((6, 8))
                col4.plotly_chart(generate_geo_barchart(filtered_locations_df, language, "city"), use_container_width=True)
                col5.plotly_chart(generate_geo_barchart(filtered_locations_df, language, "road"), use_container_width=True)

        else:
            no_loc_lang_dict = {"en": 'No locations to show', "ru": "Нет локаций для отображения"}
            st.header(no_loc_lang_dict[language])


if __name__ == "__main__":
    main()

