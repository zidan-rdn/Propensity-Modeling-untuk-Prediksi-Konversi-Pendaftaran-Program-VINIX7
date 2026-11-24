
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
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    log_loss,
    brier_score_loss,
    classification_report,
    confusion_matrix
)

# ==========================================
# 1. KONFIGURASI
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    # "..",
    "data",
    "Konsultasi Karir-9Nov26.xlsx"
)

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "vinix7_logistic_model.joblib"
)

METRIC_PATH = os.path.join(
    MODEL_DIR,
    "vinix7_evaluation.json"
)

# ==========================================
# 2. MEMBACA DATASET RESMI
# ==========================================

print("=" * 60)
print("VINIX7 - LOGISTIC REGRESSION")
print("=" * 60)

df = pd.read_excel(DATA_PATH)

print("Dataset:", os.path.basename(DATA_PATH))
print("Jumlah responden:", len(df))

# ==========================================
# 3. MENENTUKAN FITUR DAN TARGET
# ==========================================

FEATURES = [
    "Semester",
    "Total Score",
    "Motivasi",
    "Frekuensi Belajar",
    "Rencana S2/Sertifikasi"
]

TARGET = "Ikut Program VINIX7?"

required_columns = FEATURES + [TARGET]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Kolom tidak ditemukan: {missing_columns}"
    )

X = df[FEATURES].copy()

y = (
    df[TARGET]
    .astype(str)
    .str.strip()
    .str.lower()
)

if not y.isin(["ya", "tidak"]).all():
    raise ValueError("Label target tidak valid.")

# ==========================================
# 4. MEMBERSIHKAN DATA
# ==========================================

numeric_features = [
    "Total Score"
]

categorical_features = [
    "Semester",
    "Motivasi",
    "Frekuensi Belajar",
    "Rencana S2/Sertifikasi"
]

for col in numeric_features:
    X[col] = pd.to_numeric(
        X[col], errors="coerce"
    )

for col in categorical_features:
    X[col] = X[col].astype("string").str.strip()

if X.isnull().any().any():
    raise ValueError(
        "Terdapat data kosong atau tidak valid pada fitur."
    )

print("\nFitur yang digunakan:")
for col in FEATURES:
    print("-", col)

print("\nDistribusi target:")
print(y.value_counts())

# ==========================================
# 5. PEMBAGIAN TRAINING DAN TESTING
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nData training:", len(X_train))
print("Data testing :", len(X_test))

# ==========================================
# 6. PREPROCESSING
# ==========================================

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_pipeline = Pipeline([
    (
        "imputer",
        SimpleImputer(strategy="most_frequent")
    ),
    (
        "encoder",
        OneHotEncoder(handle_unknown="ignore")
    )
])

preprocessor = ColumnTransformer([
    (
        "numeric",
        numeric_pipeline,
        numeric_features
    ),
    (
        "categorical",
        categorical_pipeline,
        categorical_features
    )
])

# ==========================================
# 7. LOGISTIC REGRESSION
# ==========================================

model = Pipeline([
    ("preprocessor", preprocessor),
    (
        "classifier",
        LogisticRegression(
            max_iter=3000,
            random_state=42
        )
    )
])

print("\nMemulai training Logistic Regression...")

model.fit(X_train, y_train)

print("Training berhasil!")

# ==========================================
# 8. EVALUASI MODEL
# ==========================================

predictions = model.predict(X_test)

probabilities = model.predict_proba(X_test)

classes = list(model.classes_)
ya_index = classes.index("ya")

probability_ya = probabilities[:, ya_index]

accuracy = accuracy_score(y_test, predictions)

balanced_accuracy = balanced_accuracy_score(
    y_test, predictions
)

precision = precision_score(
    y_test,
    predictions,
    pos_label="ya",
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    pos_label="ya",
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    pos_label="ya",
    zero_division=0
)

auc = roc_auc_score(
    (y_test == "ya").astype(int),
    probability_ya
)

logloss = log_loss(
    y_test,
    probabilities,
    labels=classes
)

brier = brier_score_loss(
    (y_test == "ya").astype(int),
    probability_ya
)

print("\n" + "=" * 60)
print("HASIL EVALUASI MODEL")
print("=" * 60)

print("Accuracy          :", round(accuracy, 4))
print("Balanced Accuracy :", round(balanced_accuracy, 4))
print("Precision         :", round(precision, 4))
print("Recall            :", round(recall, 4))
print("F1-Score           :", round(f1, 4))
print("ROC-AUC            :", round(auc, 4))
print("Log Loss           :", round(logloss, 4))
print("Brier Score        :", round(brier, 4))

print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))

print("Confusion Matrix:")
print(confusion_matrix(
    y_test,
    predictions,
    labels=["tidak", "ya"]
))

# ==========================================
# 9. MENYIMPAN MODEL DAN EVALUASI
# ==========================================

joblib.dump(model, MODEL_PATH)

metrics = {
    "algorithm": "Logistic Regression",
    "dataset": "Konsultasi Karir-9Nov26.xlsx",
    "total_responden": int(len(df)),
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
    "brier_score": float(brier)
}

with open(METRIC_PATH, "w", encoding="utf-8") as file:
    json.dump(metrics, file, indent=4)

print("\n" + "=" * 60)
print("TRAINING SELESAI!")
print("Algoritma: Logistic Regression")
print("Model:", MODEL_PATH)
print("Evaluasi:", METRIC_PATH)
print("=" * 60)
