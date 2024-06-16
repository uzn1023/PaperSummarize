import streamlit as st
import tempfile
from main import summarize_paper
import traceback
import requests


# ユーザー名と対応する Notion API キーとデータベース ID を保存する辞書
user_data = {
    "Uezono": {
        "notion_api_key": st.secrets['NOTION_API_KEY'],
        "database_id": st.secrets['database_id']
    },
    "You-go": {
        "notion_api_key": "hogehoge",
        "database_id": "fugafuga"
    }
    # 他のユーザーを追加する
}
# サイドバーでユーザー名を選択
selected_user = st.sidebar.selectbox('ユーザー名を選択', list(user_data.keys()))

# 選択されたユーザーの Notion API キーとデータベース ID を取得
notion_api_key = user_data[selected_user]["notion_api_key"]
database_id = user_data[selected_user]["database_id"]

# サイドバーに自動入力と手動入力のオプションを追加
st.sidebar.text_input('Notion APIキー', value=notion_api_key, type='password', key='api_key')
st.sidebar.text_input('データベースID', value=database_id, key='database_id')

# 手動入力された値を取得
notion_api_key = st.session_state.api_key
database_id = st.session_state.database_id

st.title("論文要約GPT")

uploaded_files = st.file_uploader("PDFファイルをアップロードしてください", type="pdf", accept_multiple_files=True)
pdf_urls = st.text_area("PDFファイルのURLを改行区切りで入力してください")

if uploaded_files or pdf_urls:
    if st.button('処理を開始'):
        progress_bar = st.progress(0)
        if uploaded_files:
            for i, uploaded_file in enumerate(uploaded_files):
                # 一時ファイルに保存
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_path = temp_file.name
                    try:
                        dict = summarize_paper(temp_file_path, database_id, notion_api_key)
                        with st.expander(f"{uploaded_file.name}の要約"):
                            st.table(dict)
                    except:
                        st.error(f'{uploaded_file.name}の処理に失敗しました')
                        traceback.print_exc()
                progress_bar.progress((i + 1) / len(uploaded_files))
        elif pdf_urls:
            pdf_urls = pdf_urls.splitlines()
            for i, pdf_url in enumerate(pdf_urls):
                try:
                    response = requests.get(pdf_url)
                    response.raise_for_status()  # ステータスコードが200以外の場合、例外を発生させる
                    pdf_content = response.content
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(pdf_content)
                        temp_file_path = temp_file.name
                        dict = summarize_paper(temp_file_path, database_id, notion_api_key)
                        with st.expander(f"{pdf_url}の要約"):
                            st.table(dict)
                except requests.exceptions.RequestException as e:
                    st.error(f"PDFファイルの取得に失敗しました: {e}")
                except:
                    st.error(f'{pdf_url}の処理に失敗しました')
                    traceback.print_exc()
                progress_bar.progress((i + 1) / len(pdf_urls))
        st.success('すべてのファイルが処理されました')