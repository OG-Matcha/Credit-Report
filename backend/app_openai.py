import os
import uuid
from flask import Flask, request, jsonify, send_file
from utils_openai import extract_texts_from_pdfs ,extract_text_from_image, initialize_retriever, generate_report, save_to_pdf1

app = Flask(__name__)

UPLOAD_FOLDER = "../upload"
REPORT_FOLDER = "../report"

@app.route('/upload', methods=['POST'])
def model_response():

    files = request.files.getlist('files') 
    company_name = request.form['company_name']

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)

    all_texts = []
    for file in files:
        unique_filename = f"{uuid.uuid4().hex}.pdf"
        temp_file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(temp_file_path)

        if file.filename.endswith('.pdf'):
            text = extract_texts_from_pdfs([temp_file_path])

        elif file.filename.endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(temp_file_path)
        elif file.filename.endswith('.mp3'):
            pass # 音檔功能尚未實現
            # text = extract_text_from_audio(temp_file_path)
        else:
            continue

        all_texts.extend(text)

    retriever = initialize_retriever()
    report = generate_report('\n'.join(all_texts), company_name, retriever)

    data = {
        'report': report,
        'company_name': company_name
    }
    file_path = save_to_pdf1(data, REPORT_FOLDER)

    return jsonify({"download_link": f"/download/{os.path.basename(file_path)}"})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(REPORT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
