import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class ConversationBot:
    def __init__(self):
        load_dotenv()

        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(api_key=self.OPENAI_API_KEY)
        self.conversations = []
        self.info = []

        self._build_faiss_index(self.embeddings)
        self.docs = self._load_faiss_index(self.embeddings)
        self.rag_chain = self._create_rag_chain(self.docs)


    def _load_documents(self, documents_path="../upload/"):
        documents = []
        for filename in os.listdir(documents_path):
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(os.path.join(documents_path, filename))
                pages = loader.load_and_split()
                documents.extend(page.page_content for page in pages)
        return documents

    def _build_faiss_index(self, embeddings, save_path="./faiss_index"):
        documents = self._load_documents()

        docsearch = FAISS.from_texts(documents, embeddings)
        docsearch.save_local(save_path)

    def _load_faiss_index(self, embeddings, save_path="./faiss_index"):
        return FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)

    def _create_retriever(self, doc, k=3):
        retriever = doc.as_retriever(search_type='similarity', search_kwargs={'k': k})

        return retriever

    def _create_llm(self):
        return ChatOpenAI(api_key=self.OPENAI_API_KEY)

    def _initialize_prompt(self):
        system_prompt = """
# 背景設定
你是企業金融的 AI 輔助小幫手，你的工作是透過整理客戶徵信報告、分析內容或摘要訪視之相關重點，你會收到目標公司的信審報告，你要去幫助銀行行員快速的了解客戶，進而讓銀行與客戶間可建立更緊密的關係並也提高客戶滿意度。

# 任務
1. 根據使用者上次使用的資料以及檢索出來的資料去回答使用者的問題。
2. 如果資料的內容無法回答問題，回答「我不太清楚，請更詳細描述問題或自行查看報告內容」。
3. 你會收到你和使用者之前的一些對話，讓你可以更好的延續對話並解答問題。
4. 你會收到上次和使用者對話檢索的資料，讓你可以更好的回答延伸問題。

# 資料
{context}
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        return prompt

    def _create_rag_chain(self, docs):
        retriever = self._create_retriever(docs)
        llm = self._create_llm()
        prompt = self._initialize_prompt()
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        return rag_chain

    def _retrieve_answers(self, query, rag_chain):
        conversation = self.conversations

        question = f"""
# 使用者與你的對話紀錄
{conversation}

# 上一個對話的資料
{self.info}

# 問題
{query}
"""
        result = rag_chain.invoke({"input": question})

        self.info = [document.page_content for document in result['context']]
        answer = result['answer']

        while len(conversation) > 4:
            self.conversations.pop(0)

        self.conversations.append(query)
        self.conversations.append(answer)

        return answer


    def start_process(self, query):
        answer = self._retrieve_answers(query, self.rag_chain)

        return answer
