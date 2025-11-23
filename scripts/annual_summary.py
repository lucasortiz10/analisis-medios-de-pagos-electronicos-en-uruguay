# scripts/build_annual_summary.py
# Reqs: pandas, matplotlib
# pip install pandas matplotlib
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# === 1) rutas ===
BASE = Path(".")
RAW = BASE / "data" / "raw"
PROC = BASE / "data" / "processed"
FIGS = BASE / "figures"
PROC.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

# archivo limpio/maestro (NO tocar el raw)
INPUT = PROC / "uruguay_payment_trends.csv"
OUTPUT_ANNUAL = PROC / "annual_summary.csv"
OUTPUT_METHOD = PROC / "annual_by_method.csv"
OUTPUT_CAGR = PROC / "cagr_summary.csv"

# === 2) leer datos ===

if not INPUT.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT}")

if INPUT.suffix == ".xlsx":
    df = pd.read_excel(INPUT)
else:
    df = pd.read_csv(INPUT, sep=";")

# === 2bis) limpiar números crudos ===

# amount_million viene como "$ 700", "$ 2.368", etc.
# - sacar el símbolo $
# - sacar espacios
# - sacar puntos de miles para quedarnos con el número "limpio"
df["amount_million"] = (
    df["amount_million"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(" ", "", regex=False)
    .str.replace(".", "", regex=False)
)

# transaction_count viene como "15.288.227", "46.883.811", etc.
# - sacar puntos de miles y espacios
df["transaction_count"] = (
    df["transaction_count"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(" ", "", regex=False)
)

# === 3) saneo básico
df.columns = [c.strip().replace(" ","").lower() for c in df.columns]
req_cols = {"year", "semester", "payment_method", "amount_million", "transaction_count"}
missing = req_cols - set(df.columns)
if missing:
    raise ValueError(f"Faltan columnas en el input: {missing}")

# normalizar valores
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
df["semester"] = pd.to_numeric(df["semester"], errors="coerce").astype("Int64")
df["payment_method"] = df["payment_method"].astype(str).str.strip()
df["amount_million"] = pd.to_numeric(df["amount_million"], errors="coerce")
df["transaction_count"] = pd.to_numeric(df["transaction_count"], errors="coerce")

# filtrar solo debit/credit (por las dudas)
df = df[df["payment_method"].isin(["Debit Card", "Credit Card"])].copy()
if df.empty:
    raise ValueError("No hay filas para Debit Card / Credit Card después del filtrado.")

# evitar división por cero
df = df[df["transaction_count"] > 0].copy()

# --- etiquetas de año teniendo en cuenta si falta el segundo semestre ---
year_sem = df.groupby("year")["semester"].max()
# año completo = aquel cuyo semestre máximo es 2
full_years = year_sem[year_sem >= 2].index.astype(int)
if len(full_years) > 0:
    LATEST_FULL_YEAR = full_years.max()
else:
    # fallback por si el dataset es raro
    LATEST_FULL_YEAR = int(df["year"].max())

def make_year_labels(index):
    labels = []
    for y in index:
        max_sem = year_sem.get(y, pd.NA)
        # si no sabemos el semestre o tiene 2, lo mostramos como año normal
        if pd.isna(max_sem) or max_sem >= 2:
            labels.append(str(int(y)))
        else:
            # solo primer semestre disponible
            labels.append(f"{int(y)} (1st semester)")
    return labels

# === 3) métricas derivadas (por semestre) ===
# ticket promedio por operación (USD)
df["avg_amount_usd"] = (df["amount_million"] * 1_000_000) / df["transaction_count"]

# === 4) anualizar (sumas por año y método) ===
g = df.groupby(["year", "payment_method"], as_index=False).agg(
    amount_million_year=("amount_million", "sum"),
    transaction_count_year=("transaction_count", "sum")
)

# ticket promedio ponderado anual (USD) = sum(monto)/sum(tx)
g["avg_amount_usd_year"] = (g["amount_million_year"] * 1_000_000) / g["transaction_count_year"]

# === 5) pivot para tener columnas por método ===
pivot_amount = g.pivot(index="year", columns="payment_method", values="amount_million_year").fillna(0)
pivot_tx = g.pivot(index="year", columns="payment_method", values="transaction_count_year").fillna(0)
pivot_avg = g.pivot(index="year", columns="payment_method", values="avg_amount_usd_year").fillna(0)

# total anual (solo débito + crédito)
total_amount = pivot_amount.sum(axis=1)
share = pivot_amount.div(total_amount, axis=0)  # participación por método (0-1)
# filtrar solo años completos para los gráficos anuales
pivot_amount_annual = pivot_amount[pivot_amount.index <= LATEST_FULL_YEAR]
share_annual = share[share.index <= LATEST_FULL_YEAR]
pivot_avg_annual = pivot_avg[pivot_avg.index <= LATEST_FULL_YEAR]


# armar tabla anual final (wide + shares)
annual = pd.DataFrame({
    "year": pivot_amount.index,
    "amount_million_debit": pivot_amount.get("Debit Card", pd.Series(0, index=pivot_amount.index)),
    "amount_million_credit": pivot_amount.get("Credit Card", pd.Series(0, index=pivot_amount.index)),
    "tx_count_debit": pivot_tx.get("Debit Card", pd.Series(0, index=pivot_tx.index)),
    "tx_count_credit": pivot_tx.get("Credit Card", pd.Series(0, index=pivot_tx.index)),
    "avg_usd_debit": pivot_avg.get("Debit Card", pd.Series(0, index=pivot_avg.index)),
    "avg_usd_credit": pivot_avg.get("Credit Card", pd.Series(0, index=pivot_avg.index)),
    "total_amount_million": total_amount,
    "share_debit": share.get("Debit Card", pd.Series(0, index=share.index)),
    "share_credit": share.get("Credit Card", pd.Series(0, index=share.index)),
}).reset_index(drop=True)

# === 6) CAGR (2015 -> 2025) ===
def cagr(series):
    series = series.dropna()
    if series.empty:
        return float("nan")
    series = series.sort_index()
    if len(series) < 2:
        return float("nan")
    start = series.iloc[0]
    end = series.iloc[-1]
    years = series.index.max() - series.index.min()
    if start <= 0 or years <= 0:
        return float("nan")
    return (end / start) ** (1 / years) - 1

years_indexed = pivot_amount.copy()
years_indexed.index = years_indexed.index.astype(int)
years_indexed_full = years_indexed.loc[years_indexed.index <= LATEST_FULL_YEAR]

cagr_debit = cagr(years_indexed_full.get("Debit Card", pd.Series(dtype=float)))
cagr_credit = cagr(years_indexed_full.get("Credit Card", pd.Series(dtype=float)))

annual_full = annual[annual["year"] <= LATEST_FULL_YEAR].set_index("year")
cagr_total = cagr(annual_full["total_amount_million"])

# guardar también una tablita de CAGR
cagr_table = pd.DataFrame({
    "metric": ["amount_million_debit", "amount_million_credit", "total_amount_million"],
    "cagr": [cagr_debit, cagr_credit, cagr_total]
})

# === 7) guardar outputs ===
annual.to_csv(OUTPUT_ANNUAL, index=False)
g.to_csv(OUTPUT_METHOD, index=False)
cagr_table.to_csv(OUTPUT_CAGR, index=False)

def add_watermark():
    plt.text(
        0.5, 0.5,
        "Lucas Ortiz Gómez",
        transform=plt.gca().transAxes,
        fontsize=40,
        color="gray",
        alpha=0.08,
        ha="center",
        va="center",
        rotation=30
    )

# === 8) gráficos estáticos (PNG verticales)
# Nota: no fijo colores para mantener estilo simple; ajustá labels a gusto.

# 8.1 tendencia de montos (USD, millones) – solo años completos
if not pivot_amount_annual.empty:
    plt.figure(figsize=(6, 8))  # formato vertical 4:5 aprox

    for col in ["Debit Card", "Credit Card"]:
        if col in pivot_amount_annual.columns:
            plt.plot(
                pivot_amount_annual.index,
                pivot_amount_annual[col],
                marker="o",
                label=col,
            )

    plt.xlabel("Año")
    plt.ylabel("Monto (millones de USD)")
    plt.title(
        "Uruguay – Uso de tarjetas Crédito/Débito ({}–{})".format(
            int(pivot_amount_annual.index.min()),
            int(pivot_amount_annual.index.max()),
        )
    )
    plt.legend()
    plt.grid(True, alpha=0.3)

    # firma
    add_watermark()

    # labels de año (manejan el tema de semestres, aunque acá solo hay años completos)
    plt.xticks(
        pivot_amount_annual.index,
        make_year_labels(pivot_amount_annual.index),
        rotation=45,
    )

    plt.tight_layout()
    plt.savefig(FIGS / "trend_amount_million_cards.png", dpi=300)

# 8.2 participación (share) – barras apiladas
plt.figure(figsize=(8, 5))

years = share_annual.index
x = range(len(years))

debit_share = share_annual["Debit Card"] * 100 if "Debit Card" in share.columns else pd.Series(0, index=years)
credit_share = share_annual["Credit Card"] * 100 if "Credit Card" in share.columns else pd.Series(0, index=years)

# barra para débito (parte inferior)
plt.bar(x, debit_share, label="Debit Card")

# barra para crédito (apilada encima de débito)
plt.bar(x, credit_share, bottom=debit_share, label="Credit Card")

plt.xlabel("Año")
plt.ylabel("Participación (%)")
plt.title("Uruguay Débito vs Crédito uso sobre total operado")

# usamos las labels que marcan si el año es solo 1er semestre
plt.xticks(x, make_year_labels(years), rotation=45)

plt.ylim(0, 100)  # en principio deberían sumar ~100%
plt.legend()
plt.grid(axis="y", alpha=0.3)

add_watermark()

plt.tight_layout()
plt.savefig(FIGS / "share_debit_credit.png", dpi=300)

# 8.3 ticket promedio (USD por operación) – dividido en dos rangos

if not pivot_avg_annual.empty:
    year_min = int(pivot_avg.index.min())
    year_max = int(pivot_avg.index.max())

    split_year = (year_min + year_max) // 2

    avg_early = pivot_avg[pivot_avg.index <= split_year]
    avg_late = pivot_avg[pivot_avg.index >= split_year]

    def plot_avg_ticket(df_avg, filename_suffix):
        if df_avg.empty:
            return

        plt.figure(figsize=(8, 5))
        if "Debit Card" in df_avg.columns:
            plt.plot(df_avg.index, df_avg["Debit Card"], marker="o", label="Debit Card")
        if "Credit Card" in df_avg.columns:
            plt.plot(df_avg.index, df_avg["Credit Card"], marker="o", label="Credit Card")

        plt.xlabel("Año")
        plt.ylabel("Ticket promedio por txn (USD)")
        plt.title(
            f"Uruguay Ticket promedio (Débito vs Crédito) {int(df_avg.index.min())}–{int(df_avg.index.max())}"
        )
        plt.legend()
        plt.grid(True, alpha=0.3)

        add_watermark()
         
        # acá usamos las labels con info de semestre
        plt.xticks(df_avg.index, make_year_labels(df_avg.index), rotation=45)

        plt.tight_layout()
        plt.savefig(FIGS / f"avg_ticket_usd_{filename_suffix}.png", dpi=300)

    # tramo temprano
    plot_avg_ticket(avg_early, "part1")
    # tramo tardío
    plot_avg_ticket(avg_late, "part2")

# 8.4 análisis pospandemia por semestre (2022–2025)

df_pos = df[(df["year"] >= 2022) & (df["year"] <= 2025)].copy()

if not df_pos.empty:
    # asegurar que año y semestre sean ints "normales"
    df_pos["year_int"] = df_pos["year"].astype(int)
    df_pos["semester_int"] = df_pos["semester"].astype(int)

    # por si hubiera más de una fila por (año, semestre, método), agregamos
    df_pos_grp = df_pos.groupby(
        ["year_int", "semester_int", "payment_method"],
        as_index=False
    )["amount_million"].sum()

    # etiqueta semestral: "2024 S1", "2024 S2", "2025 S1", etc.
    df_pos_grp["sem_label"] = (
        df_pos_grp["year_int"].astype(str)
        + " S"
        + df_pos_grp["semester_int"].astype(str)
    )

    # orden cronológico de etiquetas (año, semestre)
    order = (
        df_pos_grp[["year_int", "semester_int", "sem_label"]]
        .drop_duplicates()
        .sort_values(["year_int", "semester_int"])
    )
    labels = order["sem_label"].tolist()
    x = range(len(labels))

    # pivot con las etiquetas ya en el orden correcto
    pivot_sem_amount = (
        df_pos_grp.pivot(
            index="sem_label",
            columns="payment_method",
            values="amount_million",
        )
        .reindex(labels)   # respetar el orden cronológico
        .fillna(0)
    )

    debit_sem = pivot_sem_amount.get("Debit Card", pd.Series(0, index=labels))
    credit_sem = pivot_sem_amount.get("Credit Card", pd.Series(0, index=labels))

    plt.figure(figsize=(10, 5))
    bar_width = 0.4

    # barras lado a lado: débito y crédito por semestre
    plt.bar(
        [i - bar_width / 2 for i in x],
        debit_sem,
        width=bar_width,
        label="Débito",
    )
    plt.bar(
        [i + bar_width / 2 for i in x],
        credit_sem,
        width=bar_width,
        label="Crédito",
    )

    plt.xlabel("Año / Semestre")
    plt.ylabel("Monto operado (millones de USD)")
    plt.title("Uruguay Monto semestral pospandemia (2022-2025)")

    plt.xticks(x, labels, rotation=45)
    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    add_watermark()

    plt.tight_layout()
    plt.savefig(FIGS / "pospandemia_semester_amount_million_2022_2025.png", dpi=300)

# === 9) resumen de outputs ===
print("Done")
print(f"- Saved: {OUTPUT_ANNUAL}")
print(f"- Saved: {OUTPUT_METHOD}")
print(f"- Saved: {OUTPUT_CAGR}")
print(f"- Figures in: {FIGS}")
