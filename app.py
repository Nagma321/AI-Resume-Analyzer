from flask import Flask, render_template, request, send_file, redirect
import os
from resume_parser import extract_text
from analyze import analyze_resume
import mysql.connector
import config
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter



app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_resume_route():
    file = request.files["resume"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Extract text
    extracted_text = extract_text(filepath)

    # Analyze resume
    analysis_result = analyze_resume(extracted_text)

    global last_result
    last_result = analysis_result

    

    # Save to MySQL
    db = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = db.cursor()

    sql = "INSERT INTO resumes (file_name, extracted_text, skills, score) VALUES (%s, %s, %s, %s)"
    val = (
    file.filename,
    extracted_text,
    analysis_result.get("skills", ""),
    analysis_result.get("ats_score", 0)
)

    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

    return render_template("result.html", result=analysis_result)

@app.route("/download_report")
def download_report():
    file_path = "report.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    text = c.beginText(40, 750)
    text.setFont("Helvetica", 10)

    text.textLine("AI Resume Analysis Report")
    text.textLine("----------------------------------------")
    text.textLine("")

    text.textLine(f"ATS Score: {last_result.get('ats_score', 'N/A')}")
    if last_result.get("match_percent") is not None:
        text.textLine(f"Job Match: {last_result.get('match_percent')}%")
    text.textLine("")

    text.textLine("Skills:")
    text.textLine(last_result.get("skills", 'N/A'))
    text.textLine("")

    text.textLine("Missing Skills:")
    text.textLine(last_result.get("missing_skills", 'None'))
    text.textLine("")

    text.textLine("Sections:")
    for sec, content in last_result.get("sections", {}).items():
        if content:
            text.textLine(f"--- {sec.upper()} ---")
            for line in content.split("\n"):
                text.textLine(line)
            text.textLine("")

    c.drawText(text)
    c.save()

    return send_file(file_path, as_attachment=True)

@app.route("/history")
def history():
    db = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, file_name, skills, score, created_at FROM resumes ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("history.html", data=rows)




@app.route("/delete/<int:resume_id>")
def delete_record(resume_id):
    db = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = db.cursor()
    cursor.execute("DELETE FROM resumes WHERE id = %s", (resume_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/history")

# -------------------- RESUME COMPARISON FEATURE --------------------
@app.route("/compare")
def compare_page():
    return render_template("compare.html")

@app.route("/compare", methods=["POST"])
def compare_route():
    resume_a = request.files.get("resume_a")
    resume_b = request.files.get("resume_b")
    job_desc = request.form.get("job_description", "")

    if not resume_a or not resume_b:
        return "Please upload both resumes!", 400

    # Save resumes
    path_a = os.path.join(UPLOAD_FOLDER, resume_a.filename)
    path_b = os.path.join(UPLOAD_FOLDER, resume_b.filename)
    resume_a.save(path_a)
    resume_b.save(path_b)

    # Extract text
    text_a = extract_text(path_a)
    text_b = extract_text(path_b)

    # Analyze
    result_a = analyze_resume(text_a, job_desc)
    result_b = analyze_resume(text_b, job_desc)

    return render_template("compare_result.html",
                           result_a=result_a,
                           result_b=result_b,
                           jd=job_desc)

@app.route("/compare_result", methods=["POST"])
def compare_result():
    file_a = request.files["resume_a"]
    file_b = request.files["resume_b"]
    jd = request.form.get("job_description", "")

    path_a = os.path.join(UPLOAD_FOLDER, file_a.filename)
    path_b = os.path.join(UPLOAD_FOLDER, file_b.filename)

    file_a.save(path_a)
    file_b.save(path_b)

    text_a = extract_text(path_a)
    text_b = extract_text(path_b)

    result_a = analyze_resume(text_a, jd)
    result_b = analyze_resume(text_b, jd)

    # Save to DB
    db = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = db.cursor()

    sql = "INSERT INTO comparisons (resume_a, resume_b, jd, score_a, score_b, match_a, match_b) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    val = (
        file_a.filename,
        file_b.filename,
        jd,
        result_a.get("ats_score", 0),
        result_b.get("ats_score", 0),
        result_a.get("match_percent", 0),
        result_b.get("match_percent", 0),
    )
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()

    return render_template("compare_result.html",
                           A=result_a,
                           B=result_b,
                           file_a=file_a.filename,
                           file_b=file_b.filename)


@app.route("/compare_history")
def compare_history():
    db = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM comparisons ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("compare_history.html", data=rows)


@app.route("/delete_compare/<int:comp_id>")
def delete_compare(comp_id):
    db = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB
    )
    cursor = db.cursor()
    cursor.execute("DELETE FROM comparisons WHERE id = %s", (comp_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect("/compare_history")


if __name__ == "__main__":
    app.run(debug=False)
