import gradio as gr
import requests

def upload_file_to_server(file, company_name):
    if file is None:
        return "未選擇文件"
    if not company_name:
        return "公司名稱不能為空"

    url = "http://127.0.0.1:5000/upload"  
    files = {'file': ('report.pdf', file, 'application/pdf')}

    data = {'company_name': company_name}
    response = requests.post(url, files=files, data=data)
    

    print(response)
    if response.status_code != 200:
        return "文件上傳失败"

    data = response.json()
    download_link = data.get("download_link", "#")
    return f"<a href='http://127.0.0.1:5000{download_link}' target='_blank'>下载報告</a>"

file_input = gr.File(label="上傳PDF文件", type="binary")

company_input = gr.Textbox(label="公司名稱", placeholder="輸入公司名稱")
outputs = gr.HTML(label="下載")

interface = gr.Interface(
    fn=upload_file_to_server,
    inputs=[file_input, company_input],
    outputs=outputs,
    title="文件上傳到服務器"
)

interface.launch()
