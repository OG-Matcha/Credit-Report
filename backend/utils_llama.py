import uuid
import os
import pytesseract
import speech_recognition as sr
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from datetime import date
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from PIL import Image


class FAISSIndexer:
    def __init__(self):
        load_dotenv()
        self.embeddings = FastEmbedEmbeddings()  # 使用 FastEmbedEmbeddings 代替 OpenAIEmbeddings

    def load_documents(self, documents_path="C:/Credit-Report/documents/"):
        documents = []
        for filename in os.listdir(documents_path):
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(documents_path, filename))
                pages = loader.load_and_split()
                documents.extend(page.page_content for page in pages)
        return documents

    def build_faiss_index(self, documents, save_path="/faiss_index"):
        # 建立 FAISS 索引
        docsearch = FAISS.from_texts(documents, self.embeddings)

        # 保存索引到本地
        docsearch.save_local(save_path)
        print(f"FAISS index saved to {save_path}")

    def load_faiss_index(self, save_path="/faiss_index"):
        return FAISS.load_local(save_path, self.embeddings, allow_dangerous_deserialization=True)

promptTemplate = """Answer the question as precise as possible using the provided context. If the answer is
not contained in the context, say "answer not available in context." \n\n
Context: {context}
Question: {question}
Answer:
"""


questions_prompts = {
    "1. Industry Analysis": [
        "1.1 Please provide the domestic production and sales value overview of {company_name}.",
        "1.2 Please provide the monthly sales volume changes of screws and nuts for {company_name}.",
        "1.3 Please provide the operational performance of {company_name}.",
        "1.4 Please provide the price trend of upstream raw materials for {company_name}.",
        "1.5 Please provide the economic outlook for {company_name}."
    ],
    "2. Shareholder and Team Analysis": [
        "2.1 Please provide information on the major shareholders of {company_name}.",
        "2.2 Please provide the organizational structure of the group of {company_name}."
    ],
    "3. Operational Analysis": [
        "3.1 Please provide the revenue and profit analysis of {company_name}.",
        "3.2 Please provide the sales customer analysis of {company_name}.",
        "3.3 Please provide the supplier analysis of {company_name}.",
        "3.4 Please provide the transaction process of {company_name}."
    ],
    "4. Financial Analysis": [
        "4.1 Please provide the financial structure of {company_name}.",
        "4.2 Please provide the operational efficiency of {company_name}.",
        "4.3 Please provide the long-term investments of {company_name}.",
        "4.4 Please provide the related party transactions of {company_name}.",
        "4.5 Please provide the cash flow analysis of {company_name}."
    ],
    "5. Related Interviews": [
        "5.1 Please provide the plant location, environment, product, and technical advantages of {company_name}.",
        "5.2 Please provide the production process, machinery and equipment, and capacity utilization rate of {company_name}.",
        "5.3 Please provide the inventory scale of {company_name}.",
        "5.4 Please provide the order status of {company_name}.",
        "5.5 Please provide the exchange rate and country risk of {company_name}."
    ],
    "6. Banking Relations": [
        "6.1 Please provide the deposit information of {company_name}.",
        "6.2 Please provide the loan or guarantee information of {company_name}.",
        "6.3 Please provide the loan balance units for the past six months and the past three years of {company_name}.",
        "6.4 Please provide the query frequency in the credit reporting center for the past three months for {company_name}.",
        "6.5 Please provide other credit investigation information of {company_name}.",
        "6.6 Please provide the leasing transactions of {company_name}.",
        "6.7 Please provide the derivative financial products transactions of {company_name}."
    ],
    "7. Financial Statements": [
        "7.1 Please provide the latest financial statements of {company_name}."
    ]
}


def extract_text_from_image(filePath):
    image = Image.open(filePath)
    text = pytesseract.image_to_string(image)
    print(text)
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


    if not os.path.exists("/faiss_index"):
        documents = indexer.load_documents()
        indexer.build_faiss_index(documents)
    docsearch = indexer.load_faiss_index()

    return docsearch.as_retriever(search_type='similarity', search_kwargs={'k': 3})

def generate_report(context, company_name, retriever):
    report = []
    llm = ChatOllama(model="llama3:8b")  # 使用Ollama管理的模型

    for question_template in questions_prompts:
        question = question_template.format(company_name=company_name)
        results = retriever.get_relevant_documents(question)  # 查询RAG
        context_from_rag = "\n".join([result.page_content for result in results])

        if context_from_rag:
            full_context = f"{context}\n{context_from_rag}"
        else:
            full_context = context  # 即使没有找到相关内容，仍然使用模型回答

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
    title_style.alignment = 1  # 设置居中对齐

    heading_style = styles['Heading2']
    heading_style.spaceAfter = 12

    body_style = styles['BodyText']
    body_style.spaceAfter = 12

    story = []

    story.append(Paragraph("Credit Analysis Report", title_style))
    story.append(Spacer(1, 24))
    story.append(Paragraph(f"Company Name: {data['company_name']}", body_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Report Date: {date.today().strftime('%Y-%m-%d')}", body_style))
    story.append(PageBreak())

    lines = data['report'].split("\n")
    for line in lines:
        if line.startswith("Question:"):
            story.append(Paragraph(line, heading_style))
        elif line.startswith("Answer:"):
            story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 12))

    def add_page_footer(canvas, doc):
        canvas.saveState()
        footer = Paragraph("Credit Analysis Report - %d " % doc.page, styles['Normal'])
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    doc.build(story, onLaterPages=add_page_footer)

    print(file_path)
    return file_path  # 返回绝对路径