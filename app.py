from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
import os
import logging
import pandas as pd
from resume_extractor import process_resume, save_to_excel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
EXCEL_FILE = "resume_data.xlsx"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.basicConfig(level=logging.INFO)


# Utility
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Homepage
@app.route("/")
def homepage():
    return render_template("homepage.html")


# Resume builder page
@app.route("/resume_container", endpoint="resume_builder")
def build_resume():
    return render_template("index.html")


# Upload resume
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return "Invalid file", 400

    filename = file.filename
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        extracted = process_resume(file_path)
        save_to_excel(extracted)
    except Exception as e:
        logging.error(f"Resume processing error: {e}")
        return "Error processing resume", 500

    return redirect(url_for("upload_success", filename=filename))


# Upload success
@app.route("/upload_success/<filename>")
def upload_success(filename):
    return render_template("upload_success.html", filename=filename)


# Download/view uploaded file
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# Admin login
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "Gurbani" and password == "1234@":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        return "Invalid credentials", 401
    return render_template("admin.html")


# Admin dashboard: Job description input + scoring
@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    results = []

    if request.method == "POST":
        job_description = request.form.get("job_description")

        if not job_description.strip():
            return render_template("admin_dashboard.html", results=[])

        try:
            df = pd.read_excel(EXCEL_FILE)

            if 'Skills' not in df.columns:
                return render_template("admin_dashboard.html", results=[])

            # Combine relevant fields into a single string per resume
            text_fields = ["Skills", "Experience", "Education", "Certifications", "Leadership", "Projects"]
            df["Resume"] = df[text_fields].fillna("").astype(str).agg(" ".join, axis=1)

            resumes = df["Resume"].fillna("").tolist()
            all_docs = [job_description] + resumes

            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(all_docs)
            cosine_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            scaled_scores = [score * 10 for score in cosine_scores]

            df["score"] = scaled_scores
            results = df[["Full Name", "score", "File Name"]].sort_values(by="score", ascending=False).to_dict(orient="records")

        except Exception as e:
            logging.error(f"Scoring error: {e}")
            results = []

    return render_template("admin_dashboard.html", results=results)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("homepage"))


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
