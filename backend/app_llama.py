import os
import uuid
from flask import Flask, request, jsonify, send_file
from backend.utils_llama import extract_texts_from_pdfs ,extract_text_from_image, initialize_retriever, generate_report, save_to_pdf1

app = Flask(__name__)

def get_temp_directory():
    return os.path.join(os.path.expanduser('~'), 'Desktop', 'temp')

@app.route('/upload', methods=['POST'])
def model_response():

    files = request.files.getlist('files') 
    company_name = request.form['company_name']


    temp_dir = get_temp_directory()
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    all_texts = []
    for file in files:
        unique_filename = f"{uuid.uuid4().hex}.pdf"  # 如果所有文件都是 PDF，也可以根據實際情況設置文件擴展名
        temp_file_path = os.path.join(temp_dir, unique_filename)
        file.save(temp_file_path)

        if file.filename.endswith('.pdf'):
            text = extract_texts_from_pdfs([temp_file_path])

        elif file.filename.endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(temp_file_path)  # 您需要實現此功能
        elif file.filename.endswith('.mp3'):
            text = extract_text_from_audio(temp_file_path)  # 您需要實現此功能
        else:
            continue

        all_texts.extend(text)  
 
    # 初始化檢索器
    retriever = initialize_retriever()
    report = generate_report('\n'.join(all_texts), company_name, retriever)

    data = {
        'report': report,
        'company_name': company_name
    }
    file_path = save_to_pdf1(data, temp_dir)  # 获取绝对路径
    print(file_path, temp_dir)

    return jsonify({"download_link": f"/download/{os.path.basename(file_path)}"}) 
        
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):

    temp_dir = get_temp_directory()
    file_path = os.path.join(temp_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
        


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
