import uuid
import os
import pytesseract
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from PIL import Image
class FAISSIndexer:
    def __init__(self):
        load_dotenv()
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

    def load_documents(self, documents_path="../documents/"):
        documents = []
        for filename in os.listdir(documents_path):
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(documents_path, filename))
                pages = loader.load_and_split()
                documents.extend(page.page_content for page in pages)

    def build_faiss_index(self, documents, save_path="./faiss_index"):
        docsearch = FAISS.from_texts(documents, self.embeddings)
        docsearch.save_local(save_path)

    def load_faiss_index(self, save_path="../frontend/faiss_index"):
        return FAISS.load_local(save_path, self.embeddings, allow_dangerous_deserialization=True)

promptTemplate = """
# 背景設定
請根據檢索出來的文件資料精確地回答使用者針對目標公司提出的每個問題。\n\n

# 文件資料
{context}

# 問題
{question}

# 回答
"""

questions_prompts = {
    "1. 產業分析": [
        "1.1 告訴我{company_name}的國內生產與銷售價值概覽。",
        "1.2 告訴我{company_name}螺絲與螺帽的月銷售量變化。",
        "1.3 告訴我{company_name}的營運表現。",
        "1.4 告訴我{company_name}上游原材料的價格趨勢。",
        "1.5 告訴我{company_name}的經濟展望。"
    ],
    "2. 股東與團隊分析": [
        "2.1 告訴我{company_name}主要股東的資訊。",
        "2.2 告訴我{company_name}集團的組織結構。"
    ],
    "3. 營運分析": [
        "3.1 告訴我{company_name}的收入與利潤分析。",
        "3.2 告訴我{company_name}的銷售客戶分析。",
        "3.3 告訴我{company_name}的供應商分析。",
        "3.4 告訴我{company_name}的交易過程。"
    ],
    "4. 財務分析": [
        "4.1 告訴我{company_name}的財務結構。",
        "4.2 告訴我{company_name}的營運效率。",
        "4.3 告訴我{company_name}的長期投資。",
        "4.4 告訴我{company_name}的關聯方交易。",
        "4.5 告訴我{company_name}的現金流量分析。"
    ],
    "5. 相關訪談": [
        "5.1 告訴我{company_name}的廠房位置、環境、產品和技術優勢。",
        "5.2 告訴我{company_name}的生產過程、機械設備和產能利用率。",
        "5.3 告訴我{company_name}的庫存規模。",
        "5.4 告訴我{company_name}的訂單狀況。",
        "5.5 告訴我{company_name}的匯率和國家風險。"
    ],
    "6. 銀行關係": [
        "6.1 告訴我{company_name}的存款資訊。",
        "6.2 告訴我{company_name}的貸款或擔保資訊。",
        "6.3 告訴我{company_name}過去六個月和過去三年的貸款餘額單位。",
        "6.4 告訴我{company_name}過去三個月在信用報告中心的查詢頻率。",
        "6.5 告訴我{company_name}的其他信用調查資訊。",
        "6.6 告訴我{company_name}的租賃交易。",
        "6.7 告訴我{company_name}的衍生金融產品交易。"
    ],
    "7. 財務報表": [
        "7.1 告訴我{company_name}最新的財務報表資訊。"
    ]
}


def extract_text_from_image(filePath):
    image = Image.open(filePath)
    text = pytesseract.image_to_string(image)
    return [text]

def extract_texts_from_pdfs(filePaths):
    all_texts = []
    for filePath in filePaths:
        loader = PyPDFLoader(filePath)
        pages = loader.load_and_split()
        all_texts.extend([page.page_content for page in pages])
    return all_texts


def initialize_retriever():
    indexer = FAISSIndexer()

    if not os.path.exists("./faiss_index"):
        documents = indexer.load_documents()
        indexer.build_faiss_index(documents)
    docsearch = indexer.load_faiss_index()

    return docsearch.as_retriever(search_type='similarity', search_kwargs={'k': 3})

def generate_report(context, company_name, retriever):
    report = [] 
    llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for question_template in questions_prompts:
        question = question_template.format(company_name=company_name)
        results = retriever.get_relevant_documents(question)
        context_from_rag = "\n".join([result.page_content for result in results])

        if context_from_rag:
            full_context = f"{context}\n{context_from_rag}"
        else:
            full_context = context

        prompt = PromptTemplate(template=promptTemplate, input_variables=["context", "question"])
        formatted_prompt = prompt.format(context=full_context, question=question)
        llm_response = llm.invoke(formatted_prompt)
        content = llm_response.content

        report.append(f"Question: {question}\nAnswer: {content}\n\n")

    return "\n".join(report)

def save_to_pdf1(data, directory):
    unique_filename = f"report_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join(directory, unique_filename)

    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = styles['Title']
    title_style.alignment = 1

    heading_style = styles['Heading2']
    heading_style.spaceAfter = 12

    body_style = styles['BodyText']
    body_style.spaceAfter = 12

    pdfmetrics.registerFont(TTFont('SimHei', "./font/SimHei.ttf"))

    c_heading_style = ParagraphStyle(
        name='Chinese_h',
        fontName='SimHei',
        parent=styles['Heading2']
    )

    c_body_style = ParagraphStyle(
        name='Chinese_b',
        fontName='SimHei',
        parent=styles['BodyText']
    )

    story = []

    story.append(Paragraph("Credit Analysis Report", title_style))
    story.append(Spacer(1, 24))
    story.append(Paragraph(f"Company Name: {data['company_name']}", c_body_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Report Date: {date.today().strftime('%Y-%m-%d')}", body_style))
    story.append(PageBreak())

    lines = data['report'].split("\n")
    for line in lines:
        if line.startswith("Question:"):
            story.append(Paragraph(line, c_heading_style))
        elif line.startswith("Answer:"):
            story.append(Paragraph(line, c_body_style))
        else:
            story.append(Paragraph(line, c_body_style))
        story.append(Spacer(1, 12))

    def add_page_footer(canvas, doc):
        canvas.saveState()
        footer = Paragraph("Credit Analysis Report - %d " % doc.page, styles['Normal'])
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    doc.build(story, onLaterPages=add_page_footer)

    return file_path
