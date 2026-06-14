from flask import Flask, render_template, request, jsonify
import sqlite3
from collections import defaultdict
import json
from flask import send_file
app = Flask(__name__)
DATABASE = "church_v3.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def repair_database_entries():
    """
    Automated Data Cleanup Patch:
    Scans the competition_results table and repairs corrupted 'standard' entries
    by safely validating them against the suffix of the tracking participant_id.
    """
    conn = get_connection()
    try:
        rows = conn.execute("SELECT result_id, participant_id FROM competition_results").fetchall()
        repaired_count = 0
        
        for row in rows:
            p_id = str(row["participant_id"]).strip().upper()
            result_id = row["result_id"]
            correct_std = None

            if p_id.endswith("0L"):
                correct_std = "LKG"
            elif p_id.endswith("0U"):
                correct_std = "UKG"
            elif p_id.endswith("01"):
                correct_std = "I"
            elif p_id.endswith("02"):
                correct_std = "II"
            elif p_id.endswith("03"):
                correct_std = "III"
            elif p_id.endswith("04"):
                correct_std = "IV"
            elif p_id.endswith("05"):
                correct_std = "V"
            elif p_id.endswith("06"):
                correct_std = "VI"
            elif p_id.endswith("07"):
                correct_std = "VII"
            elif p_id.endswith("08"):
                correct_std = "VIII"
            elif p_id.endswith("09"):
                correct_std = "IX"
            elif p_id.endswith("10"):
                correct_std = "X"
            elif p_id.endswith("11"):
                correct_std = "XI"
            elif p_id.endswith("12"):
                correct_std = "XII"

            if correct_std:
                conn.execute(
                    "UPDATE competition_results SET standard = ? WHERE result_id = ?",
                    (correct_std, result_id)
                )
                repaired_count += 1
                
        if repaired_count > 0:
            conn.commit()
            print(f"Database Patch Applied: Successfully fixed {repaired_count} standard rows alignment.")
    except Exception as e:
        print(f"Automatic data validation warning: {e}")
    finally:
        conn.close()


@app.route("/save", methods=["POST"])
def save():
    church_name = request.form.get("church_name")
    council = request.form.get("council")
    headquarters_branch = request.form.get("headquarters_branch")
    alphabet_key = request.form.get("alphabet_key").strip().upper()

    dropdown_place = request.form.get("place_dropdown")
    if dropdown_place == "Others":
        place = request.form.get("custom_place", "").strip().upper()
    else:
        place = dropdown_place if dropdown_place else ""

    num_teachers = int(request.form.get("num_teachers", 0))
    raw_teachers = request.form.getlist("teacher_names[]")
    cleaned_teachers = [t.strip() for t in raw_teachers if t.strip()]
    teacher_names_json = json.dumps(cleaned_teachers)

    payment_status = request.form.get("payment_status", "No").strip().capitalize()
    
    amount_due = 0
    if payment_status == "Yes":
        if headquarters_branch == "Headquarters":
            amount_due = 300
        else:
            amount_due = 150

    prefix = generate_prefix(council, headquarters_branch, alphabet_key)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO church_schools (
        church_name, place, council, headquarters_branch, alphabet_key,
        num_teachers, teacher_names, amount_due, payment_status,
        lkg_id, lkg_name, ukg_id, ukg_name,
        std1_id, std1_name, std2_id, std2_name, std3_id, std3_name,
        std4_id, std4_name, std5_id, std5_name, std6_id, std6_name,
        std7_id, std7_name, std8_id, std8_name, std9_id, std9_name,
        std10_id, std10_name, std11_id, std11_name, std12_id, std12_name
    )
    VALUES (
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?
    )
    """,
    (
        church_name, place, council, headquarters_branch, prefix,
        num_teachers, teacher_names_json, amount_due, payment_status,
        prefix + "0L", clean(request.form.get("lkg_name")),
        prefix + "0U", clean(request.form.get("ukg_name")),
        prefix + "01", clean(request.form.get("std1_name")),
        prefix + "02", clean(request.form.get("std2_name")),
        prefix + "03", clean(request.form.get("std3_name")),
        prefix + "04", clean(request.form.get("std4_name")),
        prefix + "05", clean(request.form.get("std5_name")),
        prefix + "06", clean(request.form.get("std6_name")),
        prefix + "07", clean(request.form.get("std7_name")),
        prefix + "08", clean(request.form.get("std8_name")),
        prefix + "09", clean(request.form.get("std9_name")),
        prefix + "10", clean(request.form.get("std10_name")),
        prefix + "11", clean(request.form.get("std11_name")),
        prefix + "12", clean(request.form.get("std12_name"))
    ))

    conn.commit()
    conn.close()

    return """
    <h2>Record Saved Successfully</h2>
    <a href='/data-entry'>Add Another Record</a>
    <br><br>
    <a href='/statistics'>View Statistics</a>
    """


def clean(value):
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def generate_prefix(council, headquarters_branch, alphabet_key):
    council_code = "W" if council == "WEST Council" else "E"
    branch_code = "H" if headquarters_branch == "Headquarters" else "B"
    return council_code + branch_code + alphabet_key.upper()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/data-entry")
def data_entry():
    return render_template("data_entry.html")


@app.route("/statistics")
def statistics():
    conn = get_connection()

    total_churches = conn.execute("SELECT COUNT(*) FROM church_schools").fetchone()[0]
    west_count = conn.execute("SELECT COUNT(*) FROM church_schools WHERE council='WEST Council'").fetchone()[0]
    east_count = conn.execute("SELECT COUNT(*) FROM church_schools WHERE council='EAST Council'").fetchone()[0]
    headquarters_count = conn.execute("SELECT COUNT(*) FROM church_schools WHERE headquarters_branch='Headquarters'").fetchone()[0]
    branch_count = conn.execute("SELECT COUNT(*) FROM church_schools WHERE headquarters_branch='Branch'").fetchone()[0]

    def get_aggregated_matrix(council, hq_b):
        return conn.execute(f"""
            SELECT COUNT(lkg_name), COUNT(ukg_name), COUNT(std1_name), COUNT(std2_name), COUNT(std3_name),
                   COUNT(std4_name), COUNT(std5_name), COUNT(std6_name), COUNT(std7_name), COUNT(std8_name),
                   COUNT(std9_name), COUNT(std10_name), COUNT(std11_name), COUNT(std12_name),
                   IFNULL(SUM(num_teachers), 0), IFNULL(SUM(amount_due), 0)
            FROM church_schools WHERE council='{council}' AND headquarters_branch='{hq_b}'
        """).fetchone()

    west_hq = get_aggregated_matrix("WEST Council", "Headquarters")
    west_branch = get_aggregated_matrix("WEST Council", "Branch")
    east_hq = get_aggregated_matrix("EAST Council", "Headquarters")
    east_branch = get_aggregated_matrix("EAST Council", "Branch")

    west_churches = conn.execute("""
        SELECT * FROM church_schools WHERE council='WEST Council' ORDER BY alphabet_key ASC, church_name ASC
    """).fetchall()

    east_churches = conn.execute("""
        SELECT * FROM church_schools WHERE council='EAST Council' ORDER BY alphabet_key ASC, church_name ASC
    """).fetchall()

    conn.close()

    return render_template(
        "statistics.html",
        total_churches=total_churches,
        west_count=west_count,
        east_count=east_count,
        headquarters_count=headquarters_count,
        branch_count=branch_count,
        west_hq=west_hq,
        west_branch=west_branch,
        east_hq=east_hq,
        east_branch=east_branch,
        west_churches=west_churches,
        east_churches=east_churches
    )


@app.route("/statistics/print-pdf")
def print_statistics_pdf():
    option = request.args.get("option", "1")
    conn = get_connection()
    
    standards_list = ['LKG', 'UKG', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
    
    mapping = {
        "LKG": ("lkg_id", "lkg_name"), "UKG": ("ukg_id", "ukg_name"),
        "I": ("std1_id", "std1_name"), "II": ("std2_id", "std2_name"),
        "III": ("std3_id", "std3_name"), "IV": ("std4_id", "std4_name"),
        "V": ("std5_id", "std5_name"), "VI": ("std6_id", "std6_name"),
        "VII": ("std7_id", "std7_name"), "VIII": ("std8_id", "std8_name"),
        "IX": ("std9_id", "std9_name"), "X": ("std10_id", "std10_name"),
        "XI": ("std11_id", "std11_name"), "XII": ("std12_id", "std12_name")
    }

    ctx = {"option": option, "title": "", "data": {}, "standards": standards_list}

    def get_matrix_tally(council, hq_b):
        return conn.execute(f"""
            SELECT COUNT(lkg_name), COUNT(ukg_name), COUNT(std1_name), COUNT(std2_name), COUNT(std3_name),
                   COUNT(std4_name), COUNT(std5_name), COUNT(std6_name), COUNT(std7_name), COUNT(std8_name),
                   COUNT(std9_name), COUNT(std10_name), COUNT(std11_name), COUNT(std12_name),
                   IFNULL(SUM(num_teachers), 0), IFNULL(SUM(amount_due), 0)
            FROM church_schools WHERE council='{council}' AND headquarters_branch='{hq_b}'
        """).fetchone()

    ctx["overall_summary"] = {
        "West_Headquarters": get_matrix_tally("WEST Council", "Headquarters"),
        "West_Branch": get_matrix_tally("WEST Council", "Branch"),
        "East_Headquarters": get_matrix_tally("EAST Council", "Headquarters"),
        "East_Branch": get_matrix_tally("EAST Council", "Branch")
    }

    ctx["west_churches"] = conn.execute("SELECT * FROM church_schools WHERE council='WEST Council' ORDER BY alphabet_key ASC, church_name ASC").fetchall()
    ctx["east_churches"] = conn.execute("SELECT * FROM church_schools WHERE council='EAST Council' ORDER BY alphabet_key ASC, church_name ASC").fetchall()

    if option == "1":
        ctx["title"] = "Council & Grade Participant Matrix"

    elif option == "2":
        ctx["title"] = "Individual Council & Std."

    elif option == "3":
        ctx["title"] = "Church with Nominated Std."
        
        target_groups = [
            ("WEST Council", "Headquarters", "WEST COUNCIL & HEADQUARTERS MATRIX"),
            ("WEST Council", "Branch", "WEST COUNCIL & BRANCH MATRIX"),
            ("EAST Council", "Headquarters", "EAST COUNCIL & HEADQUARTERS MATRIX"),
            ("EAST Council", "Branch", "EAST COUNCIL & BRANCH MATRIX")
        ]
        
        nested_data = []
        for council_val, hq_val, display_label in target_groups:
            churches = conn.execute("""
                SELECT * FROM church_schools 
                WHERE council = ? AND headquarters_branch = ? 
                ORDER BY alphabet_key ASC, church_name ASC
            """, (council_val, hq_val)).fetchall()
            
            group_churches = []
            for ch in churches:
                roster = []
                # MODIFIED: Always include all 14 standards. Leave name blank if None.
                for std in standards_list:
                    id_col, name_col = mapping[std]
                    raw_name = ch[name_col]
                    display_name = str(raw_name).strip() if (raw_name and str(raw_name).strip()) else ""
                    
                    roster.append({
                        "type": "student",
                        "standard": std,
                        "id": ch[id_col] if ch[id_col] else "",
                        "name": display_name
                    })
                
                teacher_count = ch["num_teachers"] if ch["num_teachers"] else 0
                if ch["teacher_names"]:
                    try:
                        teachers_list = json.loads(ch["teacher_names"])
                        for idx, t_name in enumerate(teachers_list, start=1):
                            roster.append({
                                "type": "teacher",
                                "standard": f"Teacher {idx}",
                                "id": f"{ch['alphabet_key']}-T{idx:02d}",
                                "name": t_name
                            })
                    except Exception:
                        pass
                
                group_churches.append({
                    "meta": ch,
                    "roster": roster,
                    "teacher_count": teacher_count
                })
            
            if group_churches:
                nested_data.append({
                    "label": display_label,
                    "churches": group_churches
                })
                
        ctx["data"] = nested_data

    elif option == "4":
        ctx["title"] = "Standard-Wise Nominee Sheet"
        groups = [
            ("WEST Council", "Headquarters", "West - Headquarters"),
            ("WEST Council", "Branch", "West - Branch"),
            ("EAST Council", "Headquarters", "East - Headquarters"),
            ("EAST Council", "Branch", "East - Branch")
        ]
        
        structured_data = {}
        for council, hq_b, display_group in groups:
            structured_data[display_group] = {}
            for std in standards_list:
                id_col, name_col = mapping[std]
                rows = conn.execute(f"""
                    SELECT {id_col} AS sid, {name_col} AS sname, church_name, place 
                    FROM church_schools 
                    WHERE council = ? AND headquarters_branch = ? AND {name_col} IS NOT NULL AND {name_col} != ''
                    ORDER BY alphabet_key ASC, church_name ASC
                """, (council, hq_b)).fetchall()
                structured_data[display_group][std] = rows
                
        ctx["data"] = structured_data

    conn.close()
    return render_template("statistics_print.html", **ctx)


@app.route("/result-entry")
def result_entry(): return render_template("result_entry.html")

@app.route("/download_db")
def download_db():
    return send_file(
        "church_v3.db",
        as_attachment=True
    )
@app.route("/hello")
def hello():
    return "Hello"
@app.route("/clear_database")
def clear_database():
    conn = sqlite3.connect("church_v3.db")

    conn.execute("DELETE FROM church_schools")
    conn.execute("DELETE FROM competition_results")

    conn.commit()
    conn.close()

    return "Database cleared successfully"
@app.route("/show_churches")
def show_churches():
    conn = sqlite3.connect("church_v3.db")
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM church_schools LIMIT 20"
    ).fetchall()

    conn.close()

    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    repair_database_entries()
    app.run(host="0.0.0.0", port=10000)