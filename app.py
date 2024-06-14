import streamlit as st
import tempfile
from main import summarize_paper
import traceback
import requests


# サイドバーでAPIキーとデータベースIDを指定
notion_api_key = st.sidebar.text_input('Notion APIキー', value=st.secrets['NOTION_API_KEY'], type='password')
database_id = st.sidebar.text_input('データベースID', value=st.secrets['database_id'])

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