import time
from load_pdf import get_pdf_doc_object, summarize_pdf_text, summarize_pdf_image, get_properties_from_text, get_summarize_by_format_from_text
from add_notion import add_notion

def summarize_paper(pdf_path,database_id,notion_api_key):
    doc, num_pages = get_pdf_doc_object(pdf_path)

    summary = summarize_pdf_text(doc)
    summarized_texts = [entry['summarized_text'] for entry in summary.values()]
    concatenated_text = ' '.join(summarized_texts)
    first_page_text = summary[1]['text']
    time.sleep(60)

    properties = get_properties_from_text(first_page_text)

    formated_paper = get_summarize_by_format_from_text(concatenated_text)

    # time.sleep(10)

    #images = summarize_pdf_image(doc)

    dict = properties | formated_paper

    for key in dict:
        print(key, dict[key])

    add_notion(dict,database_id,notion_api_key)
    return dict

if __name__=="__main__":
    summarize_paper("./doc/test.pdf")