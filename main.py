from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
import io
from datetime import date
import json
from pypdf import PdfReader
from docx import Document
app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
USAGE_FILE = "usage.json"
MAX_DAILY_REQUESTS = 20
def check_daily_limit():
    today = str(date.today())
    try:
        with open(USAGE_FILE, "r") as f:
            usage = json.load(f)
    except:
        usage = {}
    if usage.get(today, 0) >= MAX_DAILY_REQUESTS:
        return False
    usage[today] = usage.get(today, 0) + 1
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f)
    return True
def build_prompt(topic):
    return f"""
Generate structured academic subtopics for: {topic}
Rules:
- Give 10 to 15 subtopics
- Numbered list only
- No explanations
- Keep each line short
"""
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/generate", methods=["POST"])
def generate():
    if not check_daily_limit():
        return jsonify({"error": "Daily limit reached. Try again tomorrow."})
    topic = request.json.get("topic") or request.json.get("chapter")
    if not topic or len(topic) > 100:
        return jsonify({"error": "Invalid topic."})

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": build_prompt(topic)}],
            temperature=0,
            max_tokens=300
        )
        output = response.choices[0].message.content
        # Remove any leading/trailing "1. ", "2. " if the AI included them outside the split
        return jsonify({"result": output, "content": output})
    except Exception as e:
        print(f"Error in generate: {str(e)}")
        return jsonify({"error": "Failed to generate subtopics. Please check your API key and connection."}), 500

@app.route("/generate_subtopics", methods=["POST"])
def generate_subtopics():
    return generate()

@app.route("/get_detail", methods=["POST"])
def get_detail():
    topic = request.json.get("topic")
    chapter = request.json.get("chapter")
    prompt = f"Provide detailed academic notes for the subtopic '{topic}' within the context of '{chapter}'. Use markdown formatting."
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800
        )
        output = response.choices[0].message.content
        return jsonify({"result": output, "content": output})
    except Exception as e:
        print(f"Error in get_detail: {str(e)}")
        return jsonify({"error": "Failed to get details. Please try again."}), 500
def extract_text_from_file(file):
    filename = (file.filename or "").lower()
    data = file.read()
    if filename.endswith(".txt") or filename.endswith(".md"):
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    if filename.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(data))
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    continue
            return "\n".join(pages)
        except Exception as e:
            print(f"PDF extract error: {e}")
            return ""
    if filename.endswith(".docx"):
        try:
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            print(f"DOCX extract error: {e}")
            return ""
    return ""

@app.route("/upload_file", methods=["POST"])
def upload_file():
    if not check_daily_limit():
        return jsonify({"error": "Daily limit reached. Try again tomorrow."}), 429
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected."}), 400

    allowed = (".txt", ".md", ".pdf", ".docx")
    if not file.filename.lower().endswith(allowed):
        return jsonify({"error": "Unsupported file type. Use TXT, MD, PDF, or DOCX."}), 400

    text = extract_text_from_file(file)
    if not text or len(text.strip()) < 20:
        return jsonify({"error": "Could not read meaningful text from the file."}), 400

    text = text.strip()[:12000]

    prompt = f"""You are an expert academic note-maker. Read the following document content and produce clear, well-structured study notes in markdown.

Requirements:
- Start with a short title (## heading) inferred from the content
- Provide a brief 2-3 sentence summary
- Then list key concepts as headings (###) with concise bullet points
- Highlight important terms in **bold**
- End with a short "Key Takeaways" section (3-5 bullets)

DOCUMENT CONTENT:
\"\"\"
{text}
\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200,
        )
        notes = response.choices[0].message.content
        return jsonify({"content": notes, "filename": file.filename})
    except Exception as e:
        print(f"Error in upload_file: {e}")
        return jsonify({"error": "Failed to generate notes from file."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
