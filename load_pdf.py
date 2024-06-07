import os
import fitz
from vertexai.preview.vision_models import Image
#from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
import base64
from PIL import Image
import io
import json
import streamlit as st

genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
model_name = "gemini-1.5-flash"
model = genai.GenerativeModel(model_name)
model_json = genai.GenerativeModel(
    model_name,
    generation_config={"response_mime_type": "application/json"}
    )
    
def get_pdf_doc_object(pdf_path: str):
    """
    `fitz.open()`を使用してPDFファイルを開き、PDFドキュメントオブジェクトとページ数を返します。

    引数:
        pdf_path: PDFファイルへのパス。

    戻り値:
        `fitz.Document`オブジェクトとPDF内のページ数を含むタプル。
    """

    # PDFファイルを読み込む
    doc: fitz.Document = fitz.open(pdf_path)

    # PDFのページ数を格納
    num_pages: int = len(doc)

    return doc, num_pages

def summarize_text_data(text: str) -> str:
    """
    gemini-proモデルを使用してテキストデータを要約

    引数:
	text: 要約するテキスト

    戻り値:
	要約テキスト
    """
    generate_contet_list = ["""You are an assistant tasked with summarizing academic paper. \
    These summaries should include important point to explain research.""",text]

    res = model.generate_content(generate_contet_list)
    text_sum = res.candidates[0].content.parts[0].text

    return text_sum



#ページごとにloop
def summarize_pdf_text(doc):
    text_metadata = {}
    for page in doc:
        page_text = page.get_text()

        page_num = page.number + 1
        print(f'Page num is {page_num}, Page text length is {len(page_text)}')

        summarized_page_text = summarize_text_data(page_text)
        text_metadata[page_num] = {
        "summarized_text": summarized_page_text,
        'text':page_text,
        }
    return text_metadata

def summarize_pdf_image(doc):
    output_dir = "./image"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    image_num = 0
    image_metadata = {}
    for page in doc:
        page_num = page.number + 1
        print(f'Page num is {page_num}')

        # 画像処理
        # ページに複数ある場合があるので、loopで処理
        image_data = page.get_images()
        for img_index, img in enumerate(image_data):
            # 画像を取得
            image_num += 1
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image = Image.open(io.BytesIO(image_bytes))
            #encoded_content = base64.b64encode(image).decode("utf-8")
            output_path = f"{output_dir}/annotated_image_{page_num + 1}_{img_index + 1}.{image_ext}"
            image.save(output_path)
            # 画像をテキスト化
            generate_contet_list = ["""You are an assistant tasked with summarizing images for retrieval. \
                These summaries will be embedded and used to retrieve the raw image. \
                Give a concise summary of the image that is well optimized for retrieval.\
                total words should be 300 - 500 words""",image]
            res = model.generate_content(generate_contet_list)
            image_description = res.candidates[0].content.parts[0].text

            # 各画像にメタデータをJSON
            image_metadata[image_num] = {
                "image_num": image_num,
                "image_path": output_path,
                "image_description": image_description,
                #"image":encoded_content
            }
    return image_metadata

def get_properties_from_text(text):
    prompt = ["""次のJSONスキーマを使用して、
        以下の論文textからtitle, authors, publish date(yyyy-mm-dd形式), 10. から始まるDOIを抽出して。

        {
            "title": str,
            "authors": list[str],
            "publish_date": str,
            "DOI": str
        }
        Return: dict

        
    """
    ,text]
    response = model_json.generate_content(prompt).text
    response = json.loads(response)
    response['authors'] = [{'name': author.replace(',', '.')} for author in response['authors']]
    return response

def get_summarize_by_format_from_text(text):
    prompt = ["""次のJSONスキーマを使用して、以下の学術論文要約textから以下の情報を読み取って。
        どんなものか？: What is the research? (Answer in japanese, one sentence)
        どこがすごい？: What is the advance point of this paper compared to previous research? (Answer in japanese, 1-3 sentence)
        肝となる手法は？: What is the key to the technique or experimental method?(Answer in japanese, 1-3 sentence)
        どう主張が示された？: How the central claim of this paper was validated?(Answer in japanese, 1-3 sentence)
        残された課題は？: What are the remaining issues and discussions resulting from the research?(Answer in japanese, 1-3 sentence)
        論文のキーワード : What are keywords of this paper? (Answer in English, 3 - 5 keywords)
        
        {
            "どんなものか？": str,
            "どこがすごい？": str,
            "肝となる手法は？": str
            "どう主張が示された？": str,
            "論文のキーワード": list[str]
        }
        Return: dict

        
    """
    ,text]
    response = model_json.generate_content(prompt).text
    response = json.loads(response)
    response['論文のキーワード'] = [{'name': author} for author in response['論文のキーワード']]
    return response

