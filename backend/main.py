import os
import json
import joblib
import pandas as pd

from io import StringIO
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ==========================================
# 1. KONFIGURASI
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "Konsultasi Karir-9Nov26.xlsx")
MODEL_PATH = os.path.join(MODEL_DIR, "vinix7_logistic_model.joblib")
EVALUATION_PATH = os.path.join(MODEL_DIR, "vinix7_evaluation.json")

app = FastAPI(
    title="VINIX7 Prediction API",
    description="API Dashboard dan Prediksi Konversi VINIX7",
    version="2.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. MEMUAT DATA DAN MODEL
# ==========================================
try:
    df = pd.read_excel(DATA_PATH)
    model_conversion = joblib.load(MODEL_PATH)
    with open(EVALUATION_PATH, "r", encoding="utf-8") as file:
        evaluation = json.load(file)
    print("Dataset VINIX7 berhasil dimuat!")
    print("Model Logistic Regression berhasil dimuat!")
    print("Evaluasi model berhasil dimuat!")
    print("Akurasi model:", round(evaluation["accuracy"] * 100, 2), "%")
    print("Jumlah responden:", len(df))
except Exception as e:
    raise RuntimeError(f"Gagal memuat dataset, model, atau evaluasi: {e}")

# ==========================================
# 3. VALIDASI KOLOM DATASET
# ==========================================

FEATURES = [
    "Perguruan Tinggi",
    "Program Studi",
    "Semester",
    "IPK",
    "Motivasi",
    "Tempat Magang",
]
TARGET = "Ikut Program VINIX7?"

DISPLAY_COLUMNS = [
    "Perguruan Tinggi", "Program Studi", "Semester", "IPK", "Dream Job",
    "Total Score", "Motivasi", TARGET, "Archetype",
    "Skor M1 (Background)", "Skor M2 (Skills)", "Skor M3 (Industry)",
    "Skor M4 (Interest)", "Skor M5 (Compass)", "Skor M6 (Company)",
    "Skor M7 (Branding)", "Skor M8 (Ambisi)", "Skor M9 (Resiliensi)",
    "Jalur Karir", "Bidang Minat", "Work Values", "Work Style",
    "Cognitive Style", "Ukuran Perusahaan", "Kultur Kerja",
    "Preferensi Lokasi", "Ekspektasi Gaji", "Minat Wirausaha",
    "Rencana S2/Sertifikasi", "Frekuensi Belajar", "Kesiapan Interview",
    "Level Bahasa Inggris", "Verdict Kesiapan",
    "Rekomendasi Industri 1", "Rekomendasi Industri 2",
]

for column in set(FEATURES + [TARGET, "Verdict Kesiapan"] + DISPLAY_COLUMNS):
    if column not in df.columns:
        raise ValueError(f"Kolom dataset tidak ditemukan: {column}")

# ==========================================

# 4. FORMAT INPUT PREDIKSI
# ==========================================
class PredictionInput(BaseModel):
    perguruan_tinggi: str = Field(min_length=1, max_length=200)
    program_studi: str = Field(min_length=1, max_length=200)
    semester: int = Field(ge=1, le=8)
    ipk: float = Field(ge=0, le=4)
    motivasi: str = Field(min_length=1)
    tempat_magang: str = Field(min_length=1, max_length=200)

# ==========================================
# 5. FUNGSI BANTU
# ==========================================
def clean_value(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def distribution(column):
    counts = df[column].dropna().value_counts()
    total_valid = int(counts.sum())
    if total_valid == 0:
        return []
    return [
        {
            "label": str(label),
            "jumlah": int(count),
            "persentase": round(float(count / total_valid * 100), 2),
        }
        for label, count in counts.items()
    ]


def normalize_category(value):
    return " ".join(str(value).strip().lower().split())

# ==========================================
# 6. HALAMAN UTAMA
# ==========================================
@app.get("/")
def home():
    return {
        "status": "success",
        "message": "VINIX7 API aktif",
        "total_responden": len(df),
    }

# ==========================================
# 7. RINGKASAN DASHBOARD
# ==========================================
@app.get("/dashboard")
def dashboard():
    total = len(df)
    yes = int((df[TARGET].astype(str).str.lower().str.strip() == "ya").sum())
    no = int((df[TARGET].astype(str).str.lower().str.strip() == "tidak").sum())
    return {
        "status": "success",
        "total_responden": total,
        "kesediaan": {
            "ya": yes,
            "tidak": no,
            "persentase_ya": round(yes / total * 100, 2) if total else 0,
            "persentase_tidak": round(no / total * 100, 2) if total else 0,
        },
        "rata_rata_score": round(float(df["Total Score"].mean()), 2),
        "distribusi_kesiapan": distribution("Verdict Kesiapan"),
        "distribusi_motivasi": distribution("Motivasi"),
        "distribusi_semester": distribution("Semester"),
        "akurasi_model": round(float(evaluation["accuracy"]) * 100, 2),
    }

# ==========================================
# 8. DATA RESPONDEN
# ==========================================
@app.get("/respondents")
def respondents(
    search: str = "",
    status: str = "",
    semester: str = "",
    motivasi: str = "",
    page: int = Query(1, ge=1),
    limit: int = Query(5, ge=1, le=100),
):
    data = df.copy()
    if search:
        searchable = [c for c in DISPLAY_COLUMNS if c in data.columns]
        mask = data[searchable].astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        data = data[mask]
    if status:
        data = data[data[TARGET].astype(str).str.lower().str.strip() == status.lower().strip()]
    if semester:
        data = data[data["Semester"].astype(str) == semester]
    if motivasi:
        data = data[data["Motivasi"].astype(str).str.lower().str.strip() == motivasi.lower().strip()]

    total = len(data)
    start = (page - 1) * limit
    records = data[DISPLAY_COLUMNS].iloc[start:start + limit].to_dict(orient="records")
    records = [{key: clean_value(value) for key, value in record.items()} for record in records]
    return {
        "status": "success",
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "data": records,
    }

# ==========================================
# 9. ANALISIS DATA
# ==========================================
@app.get("/analytics")
def analytics():
    return {
        "status": "success",
        "distribusi_perguruan_tinggi": distribution("Perguruan Tinggi"),
        "distribusi_program_studi": distribution("Program Studi"),
        "distribusi_semester": distribution("Semester"),
        "distribusi_archetype": distribution("Archetype"),
        "distribusi_m1": distribution("Skor M1 (Background)"),
        "distribusi_m2": distribution("Skor M2 (Skills)"),
        "distribusi_m3": distribution("Skor M3 (Industry)"),
        "distribusi_m4": distribution("Skor M4 (Interest)"),
        "distribusi_m5": distribution("Skor M5 (Compass)"),
        "distribusi_m6": distribution("Skor M6 (Company)"),
        "distribusi_m7": distribution("Skor M7 (Branding)"),
        "distribusi_m8": distribution("Skor M8 (Ambisi)"),
        "distribusi_m9": distribution("Skor M9 (Resiliensi)"),
        "distribusi_jalur_karir": distribution("Jalur Karir"),
        "distribusi_bidang_minat": distribution("Bidang Minat"),
        "distribusi_work_values": distribution("Work Values"),
        "distribusi_work_style": distribution("Work Style"),
        "distribusi_cognitive_style": distribution("Cognitive Style"),
        "distribusi_ukuran_perusahaan": distribution("Ukuran Perusahaan"),
        "distribusi_kultur_kerja": distribution("Kultur Kerja"),
        "distribusi_lokasi": distribution("Preferensi Lokasi"),
        "distribusi_gaji": distribution("Ekspektasi Gaji"),
        "distribusi_wirausaha": distribution("Minat Wirausaha"),
        "distribusi_rencana": distribution("Rencana S2/Sertifikasi"),
        "distribusi_frekuensi_belajar": distribution("Frekuensi Belajar"),
        "distribusi_interview": distribution("Kesiapan Interview"),
        "distribusi_bahasa_inggris": distribution("Level Bahasa Inggris"),
        "distribusi_kesiapan": distribution("Verdict Kesiapan"),
        "distribusi_kesediaan": distribution(TARGET),
        "distribusi_industri_1": distribution("Rekomendasi Industri 1"),
        "distribusi_industri_2": distribution("Rekomendasi Industri 2"),
        "total_responden": len(df),
        "rata_rata_score": round(float(df["Total Score"].mean()), 2),
        "rata_rata_ipk": round(float(df["IPK"].mean()), 2),
    }

# ==========================================
# 10. EKSPOR DATA RESPONDEN
# ==========================================
@app.get("/export")
def export_data():
    output = StringIO()
    df[DISPLAY_COLUMNS].to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=VINIX7_Data_Responden.csv"},
    )

# ==========================================

# 11. PREDIKSI LOGISTIC REGRESSION
# ==========================================
@app.post("/predict")
def predict(data: PredictionInput):
    try:
        input_data = pd.DataFrame([{
            "Perguruan Tinggi": normalize_category(data.perguruan_tinggi),
            "Program Studi": normalize_category(data.program_studi),
            "Semester": data.semester,
            "IPK": data.ipk,
            "Motivasi": normalize_category(data.motivasi),
            "Tempat Magang": normalize_category(data.tempat_magang),
        }], columns=FEATURES)

        prediction = str(model_conversion.predict(input_data)[0]).lower()
        probabilities = model_conversion.predict_proba(input_data)[0]
        classes = model_conversion.classes_

        probability_dict = {
            str(label): round(float(prob) * 100, 2)
            for label, prob in zip(classes, probabilities)
        }

        return {
            "status": "success",
            "hasil_prediksi": {
                "kesediaan": prediction,
                "probabilitas": probability_dict,
                "skor_konversi": probability_dict.get("ya", 0),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediksi gagal: {str(e)}"
        )

