import os
import uuid
from flask import Flask, request, jsonify, send_file
from .utils_llama import extract_text_from_pdf, initialize_retriever, generate_report, save_to_pdf1

app = Flask(__name__)

UPLOAD_FOLDER = "../upload"

@app.route('/upload', methods=['POST'])
def model_response():

    file = request.files['file']
    company_name = request.form['company_name']

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    original_filename = os.path.basename(file.filename)
    temp_file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{original_filename}")
    file.save(temp_file_path)

    text = extract_text_from_pdf(temp_file_path)

    # 初始化檢索器
    retriever = initialize_retriever()
    report = generate_report(text, company_name, retriever)
    data = {
        'report': report,
        'company_name': company_name
    }
    file_path = save_to_pdf1(data, UPLOAD_FOLDER)  # 获取绝对路径
    print(file_path, UPLOAD_FOLDER)

    return jsonify({"download_link": f"/download/{os.path.basename(file_path)}"})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
