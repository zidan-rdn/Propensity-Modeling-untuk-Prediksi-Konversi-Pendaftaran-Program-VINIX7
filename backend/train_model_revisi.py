import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, log_loss,
    brier_score_loss, classification_report, confusion_matrix
)

# ==========================================
# 1. KONFIGURASI
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "Konsultasi Karir-9Nov26.xlsx")
# DATA_PATH = os.path.join(BASE_DIR, "..", "data", "Konsultasi Karir-9Nov26.xlsx")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, "vinix7_logistic_model.joblib")
METRIC_PATH = os.path.join(MODEL_DIR, "vinix7_evaluation.json")

print("=" * 60)
print("VINIX7 - LOGISTIC REGRESSION")
print("=" * 60)

# ==========================================
# 2. MEMBACA DATASET
# ==========================================
df = pd.read_excel(DATA_PATH)
print("Dataset:", os.path.basename(DATA_PATH))
print("Jumlah responden:", len(df))

# ==========================================
# 3. FITUR DAN TARGET
# ==========================================
FEATURES = [
    "Perguruan Tinggi",
    "Program Studi",
    "IPK",
    "Semester",
    "Motivasi",
    "Tempat Magang",
]
TARGET = "Ikut Program VINIX7?"

missing = [col for col in FEATURES + [TARGET] if col not in df.columns]
if missing:
    raise ValueError(f"Kolom tidak ditemukan pada dataset: {missing}")

X = df[FEATURES].copy()
y = df[TARGET].astype(str).str.strip().str.lower()

# Rapikan teks agar variasi spasi dan kapitalisasi tidak dianggap kategori berbeda.
def normalize_text(series):
    return (series.astype("string").str.strip().str.lower()
            .str.replace(r"\s+", " ", regex=True))

for col in ["Perguruan Tinggi", "Program Studi", "Motivasi", "Tempat Magang"]:
    X[col] = normalize_text(X[col])

X["Semester"] = pd.to_numeric(X["Semester"], errors="coerce")
X["IPK"] = pd.to_numeric(X["IPK"], errors="coerce")

valid_target = y.isin(["ya", "tidak"])
X = X.loc[valid_target].copy()
y = y.loc[valid_target].copy()

if X.empty:
    raise ValueError("Tidak ada baris data dengan target 'ya' atau 'tidak'.")
if y.nunique() < 2:
    raise ValueError("Target harus memiliki dua kelas: 'ya' dan 'tidak'.")

print("\nFitur yang digunakan:")
for col in FEATURES:
    print("-", col)
print("\nDistribusi target:")
print(y.value_counts())

# ==========================================
# 4. TRAINING DAN TESTING
# ==========================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print("\nData training:", len(X_train))
print("Data testing :", len(X_test))

# ==========================================
# 5. PREPROCESSING
# ==========================================

numeric_features = ["Semester", "IPK"]

categorical_features = [
    "Perguruan Tinggi",
    "Program Studi",
    "Motivasi",
    "Tempat Magang",
]

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    # Kategori baru yang tidak ditemukan saat training tetap bisa diproses,
    # tetapi tidak memiliki pengaruh kategori khusus yang dipelajari model.
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=3000, random_state=42)),
])

# ==========================================
# 6. TRAINING MODEL
# ==========================================
print("\nMemulai training Logistic Regression...")
model.fit(X_train, y_train)
print("Training berhasil!")

# ==========================================
# 7. EVALUASI MODEL
# ==========================================
predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)
classes = list(model.classes_)
ya_index = classes.index("ya")
probability_ya = probabilities[:, ya_index]

accuracy = accuracy_score(y_test, predictions)
balanced_accuracy = balanced_accuracy_score(y_test, predictions)
precision = precision_score(y_test, predictions, pos_label="ya", zero_division=0)
recall = recall_score(y_test, predictions, pos_label="ya", zero_division=0)
f1 = f1_score(y_test, predictions, pos_label="ya", zero_division=0)
auc = roc_auc_score((y_test == "ya").astype(int), probability_ya)
logloss = log_loss(y_test, probabilities, labels=classes)
brier = brier_score_loss((y_test == "ya").astype(int), probability_ya)

print("\n" + "=" * 60)
print("HASIL EVALUASI MODEL")
print("=" * 60)
print("Accuracy          :", round(accuracy, 4))
print("Balanced Accuracy :", round(balanced_accuracy, 4))
print("Precision         :", round(precision, 4))
print("Recall            :", round(recall, 4))
print("F1-Score          :", round(f1, 4))
print("ROC-AUC           :", round(auc, 4))
print("Log Loss          :", round(logloss, 4))
print("Brier Score       :", round(brier, 4))
print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))
print("Confusion Matrix:")
print(confusion_matrix(y_test, predictions, labels=["tidak", "ya"]))

# ==========================================
# 8. SIMPAN MODEL DAN EVALUASI
# ==========================================
joblib.dump(model, MODEL_PATH)
metrics = {
    "algorithm": "Logistic Regression",
    "dataset": os.path.basename(DATA_PATH),
    "total_responden": int(len(X)),
    "training_samples": int(len(X_train)),
    "testing_samples": int(len(X_test)),
    "features": FEATURES,
    "target": TARGET,
    "accuracy": float(accuracy),
    "balanced_accuracy": float(balanced_accuracy),
    "precision": float(precision),
    "recall": float(recall),
    "f1_score": float(f1),
    "roc_auc": float(auc),
    "log_loss": float(logloss),
    "brier_score": float(brier),
}
with open(METRIC_PATH, "w", encoding="utf-8") as file:
    json.dump(metrics, file, indent=4)

print("\n" + "=" * 60)
print("TRAINING SELESAI!")
print("Model:", MODEL_PATH)
print("Evaluasi:", METRIC_PATH)
print("=" * 60)
