from flask import Flask, render_template, request,redirect, url_for
import pandas as pd
from sqlalchemy import create_engine,text

app = Flask(__name__)

# SQLite 資料庫
engine = create_engine("sqlite:///database.db")


@app.route("/", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        if "file" not in request.files:
            return render_template("upload.html", error="沒有選擇檔案")

        file = request.files["file"]

        if file.filename == "":
            return render_template("upload.html", error="請選擇 CSV 檔案")

        try:
            df = pd.read_csv(
                file,
                dtype={"欠款人編號": str, "欠款流水號": str},
                encoding="utf-8-sig"
            )

            df.columns = df.columns.str.strip()
            df["欠款日期"] = pd.to_datetime(df["欠款日期"])

            today = pd.Timestamp("2026-04-08")

            df["欠款天數"] = (today - df["欠款日期"]).dt.days
            df["欠款日期"] = df["欠款日期"].dt.strftime("%Y-%m-%d")

            # 存資料庫
            df.to_sql("csv_data", engine, if_exists="append", index=False)

            return render_template("csvupload.html")

        except Exception as e:
            return render_template("upload.html", error=f"檔案處理錯誤: {str(e)}")

    return render_template("upload.html")



@app.route("/data")
def show_data():

    df = pd.read_sql("SELECT * FROM csv_data", engine)

    return render_template("table.html", tables=df.to_html() )

@app.route("/clear", methods=["POST"])
def clear_data():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM csv_data"))
        conn.commit()
    return redirect(url_for("show_data"))

@app.route("/dashboard")
def dashboard():
        
        df = pd.read_sql("SELECT * FROM csv_data", engine)
        
        labels = df["欠款流水號"].tolist()
        values = df["欠款天數"].tolist()
        chart_data = {"labels": labels, "values": values}
        person_sum = df.groupby("欠款人編號")["金額"].sum().sort_values(ascending=False)
        person_chart = {
        "labels": person_sum.index.tolist(),
        "values": person_sum.values.tolist()
        }

        return render_template(
        "dash.html",

        today="2026-04-08",

        total_count=len(df),

        total_amount=df["金額"].sum(),

        avg_days=round(df["欠款天數"].mean(),2),

        max_days=df["欠款天數"].max(),

        data=df.to_dict(orient="records"),

        chart_data=chart_data,
        person_chart=person_chart
        
    )


if __name__ == "__main__":
    app.run(debug=True)