Uncover deep insights from your Telegram chats using various data analysis tools.

# Features
- Upload your chat exports to Streamlit-based web interface
- Get basic statistics for your chats and do NLP
- Perform user-level analysis
- Analyze user interactions
- Visualize trends, patterns & geographical data

Initially built for Telegram chat analysis, but also supports WhatsApp exports.

# Dependencies
- streamlit
- scikit-learn
- pandas
- scipy
- nltk
- folium
- gensim
- geopy
- googletrans
- pygeohash
- st-annotated-text
- whatstk

# Setup

### Secrets
To run this app locally, you need to create a `secrets.toml` file, which should be placed in:

- `~/.streamlit/secrets.toml` for macOS/Linux
- `%userprofile%/.streamlit/secrets.toml` for Windows

Learn more about Streamlit secrets [here](https://docs.streamlit.io/develop/concepts/connections/secrets-management).

The `secrets.toml` file should contain your Hugging Face API token:
```toml
hf_api_token = "TOKEN"
```

Follow [these instructions](https://huggingface.co/docs/hub/en/security-tokens) to generate it.

### Enviroment
Clone the repository:
```bash
git clone git@github.com:avrtt/telegram-chat-analyzer.git
cd telegram-chat-analyzer
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run:
```bash
streamlit run Home.py
```

# Trobleshooting

If you run Streamlit and it says that module is missing, you should probably upgrade Streamlit:
```bash
pip install --upgrade streamlit 
```

# Contributing
Feel free to open PRs and issues.

# License
Distributed under the MIT License. See LICENSE.txt for more information.
