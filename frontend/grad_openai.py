import requests
import gradio as gr
from chatbot_openai import ConversationBot

def upload_file_to_server(pdfs, images, company_name):


    url = "http://127.0.0.1:5000/upload"  
    upload_files = []
    if pdfs:
        for file in pdfs:
            upload_files.append(('files', file))

    if images:
        for file in images:
            upload_files.append(('files', file))



    data = {'company_name': company_name}
    response = requests.post(url, files=upload_files, data=data, timeout=1000)


    print(response)
    if response.status_code != 200:
        return "文件上傳失败"

    data = response.json()
    download_link = data.get("download_link", "#")
    return f"<a href='http://127.0.0.1:5000{download_link}' target='_blank'>下载報告</a>"

def clear_files():
    return None, None, None

with gr.Blocks() as build:
    company_input = gr.Textbox(label="公司名稱", placeholder="輸入公司名稱")
    pdf_input = gr.Files(label="上傳PDF文件", type="binary")
    image_input = gr.Files(label="上傳圖片文件", type="binary")
    audio_input = gr.Files(label="上傳音頻文件", type="binary")
    upload_button = gr.Button("上傳文件")
    clear_button = gr.Button("清除文件")
    outputs = gr.HTML(label="下載")

    upload_button.click(upload_file_to_server, inputs=[pdf_input, image_input, company_input], outputs=outputs)
    clear_button.click(clear_files, outputs=[pdf_input, image_input, company_input])

def predict(message, history):
    bot = ConversationBot()
    response = bot.start_process(message)

    return response

chat = gr.ChatInterface(predict, css="#component-9 { height:calc(120vh - 380px)!important; }")

demo = gr.TabbedInterface([build, chat], ["Create Report", "Chat with Documents"], css="#component-9 { height:calc(120vh - 380px)!important; }")

if __name__ == "__main__":
    demo.launch()
