# Credit Report

# 使用說明
首先請在你的程式編輯器 (希望是 VsCode) 建立 Python 的 venv (virtual environment)，並選擇導入 requirements.txt 內的模組

# OpenAI 版本 (如果你有金鑰的話)
1. 先按照 .env.example 的格式，創建一個自己的 .env 檔案 (這個檔案不會上 Github)，然後在 `OPENAI_API_KEY = ""` 中填入你的金鑰
2. 確定你的 console 在虛擬環境中
3. 執行前端 `cd ./frontend`, `python grad_openai.py`，console 會出現可以開啟的網址
4. 執行後端 `cd ./backend`, `python app_openai.py`，確定啟動即可開始在網頁上操作
   
# LLaMA 版本 (如果你電腦很棒的話)
1. 確認你有安裝 Ollama 且可以使用，並且有安裝 LLama3-8b 的模型
1. 確定你的 console 在虛擬環境中
3. 執行前端 `cd ./frontend`, `python grad_llama.py`，console 會出現可以開啟的網址
4. 執行後端 `cd ./backend`, `python app_llama.py`，確定啟動即可開始在網頁上操作
