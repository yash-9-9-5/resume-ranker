from flask import Flask, render_template, request, redirect, url_for, send_file
import os
from werkzeug.utils import secure_filename
from resume_processor import extract_text_from_pdf, calculate_scores, generate_report

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rank", methods=["POST"])
def rank_resumes():
    job_desc = request.form["job_description"]
    resume_files = request.files.getlist("resumes")
    filenames, resume_texts = [], []
    for file in resume_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            filenames.append(filename)
            resume_texts.append(extract_text_from_pdf(filepath))
    scores = calculate_scores(job_desc, resume_texts)
    ranked_data = sorted(
        zip(filenames, scores),
        key=lambda x: x[1],
        reverse=True
    )
    ranked_resumes = [
        (data[0], f"{data[1]:.2f}%", rank+1)
        for rank, data in enumerate(ranked_data)
    ]
    report_path = generate_report(ranked_resumes)
    return render_template(
        "results.html",
        results=ranked_resumes,
        report=report_path
    )

@app.route("/download")
def download_report():
    report = request.args.get("report")
    return send_file(
        report,
        mimetype="text/csv",
        as_attachment=True,
        download_name="resume_rankings.csv"
    )

if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.run(debug=True)  