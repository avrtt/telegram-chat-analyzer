import io
import zipfile
from time import sleep

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from streamlit_extras.buy_me_a_coffee import button
from streamlit_extras.switch_page_button import switch_page

from utils.general_utils import (
    add_metadata_to_df,
    add_logo,
    generate_synthetic_locations,
    app_language,
    author
)
from utils.parsers import _df_from_str, parse_telegram_html

GOOGLE_VERIFICATION_TAG = '<meta name="google-site-verification" content="{}" />'

def load_data(files):
    '''Loads and processes uploaded chat data files'''
    progress_bar = st.progress(0, text="Processing...")
    df_list = []

    for index, file in enumerate(files):
        df_list.append(process_file(file))
        update_progress(progress_bar, index, len(files))

    # combine and add metadata to the final dataframe
    final_df = add_metadata_to_df(pd.concat(df_list, ignore_index=True)).sort_values('timestamp')
    st.session_state['data'] = final_df
    st.session_state['lang'] = None
    progress_bar.progress(100)


def process_file(file):
    '''Processes individual files based on their extension'''
    if file.name.endswith('.txt'):
        st.session_state['file_name'] = clean_filename(file.name)
        return _df_from_str(file.read().decode())

    elif file.name.endswith('.html'):
        return process_telegram_html(file)

    elif file.name.endswith('.zip'):
        return process_zip_file(file)


def process_telegram_html(file):
    '''Processes Telegram .html files'''
    try:
        group_name, group_df = parse_telegram_html(file.read().decode())
        st.session_state['file_name'] = group_name
        return group_df
    except Exception as e:
        st.error(f"Failed to process {file.name}: {e}")
        return None


def process_zip_file(file):
    '''Processes zipped WhatsApp files'''
    with io.BytesIO(file.read()) as zip_file:
        with zipfile.ZipFile(zip_file, 'r') as z:
            txt_file = [f for f in z.namelist() if f.endswith('.txt')][0]
            with z.open(txt_file) as txt_file:
                st.session_state['file_name'] = clean_filename(txt_file.name)
                return _df_from_str(txt_file.read().decode())


def clean_filename(filename):
    '''Cleans up filenames by removing unwanted parts'''
    return (
        filename.replace('.txt', '')
        .replace('WhatsApp Chat with', '')
        .replace('_', '')
    )


def update_progress(progress_bar, index, total_files):
    '''Updates the progress bar during file processing'''
    progress = (index + 1) / total_files
    progress_bar.progress(progress, text="Processing...")


def display_home_screen(language):
    '''Displays the home screen with instructions and uploading options'''
    home_holder = st.empty()
    home_text = {
        "en": "Upload exported chats",
        "ru": "Загрузите экспортированные чаты",
    }
    home_holder.markdown(
        f'<span style="font-size: 20px;">{home_text[language]}</span>',
        unsafe_allow_html=True,
    )


def display_upload_prompt(language):
    '''Displays the upload file prompt'''
    upload_text = {
        "en": "Supports Telegram (.html) and WhatsApp (.txt & .zip) exported files", 
        "ru": "Поддерживает файлы из Telegram (.html) и WhatsApp (.txt & .zip)"
    }
    return st.file_uploader(upload_text[language], type=["txt", "html", "zip"], accept_multiple_files=True)


def display_how_to_export(language):
    '''Displays instructions on how to export chats from WhatsApp and Telegram'''
    telegram_text = {"en": "Telegram", "ru": "для Telegram"}
    whatsapp_text = {"en": "WhatsApp", "ru": "для WhatsApp"}
    export_text = {"en": "Export reference:", "ru": "Описание процесса экспорта:"}

    export_text_html = f'''
        <span>{export_text[language]}</span>
    '''

    telegram_html = f'''
        <a href="https://telegram.org/blog/export-and-more">
            <span>{telegram_text[language]}</span>
        </a>
    '''

    whatsapp_html = f'''
        <a href="https://faq.whatsapp.com/1180414079177245/">
            <span>{whatsapp_text[language]}</span>
        </a>
        <br><br>
    '''

    st.markdown(f'{export_text_html}<br>- {telegram_html}<br>- {whatsapp_html}', unsafe_allow_html=True)


def main():
    '''Main function to run the Streamlit app'''
    add_logo()

    language = app_language()

    display_home_screen(language)
    uploaded_files = display_upload_prompt(language)
    display_how_to_export(language)

    if uploaded_files:
        clear_placeholders()
        load_data(uploaded_files)
        switch_page("basic statistics")
        st.write("Chat uploaded successfully!")
        sleep(2)


def clear_placeholders():
    '''Clears all UI placeholders'''
    st.empty()


if __name__ == "__main__":
    main()
    author()
