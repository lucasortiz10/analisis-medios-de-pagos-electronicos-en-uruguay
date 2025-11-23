Análisis de medios de pago con tarjetas en Uruguay (2015–2025)

Este repositorio contiene un análisis exploratorio del uso de tarjetas de débito y crédito en Uruguay, a partir de datos semestrales publicados por el Banco Central del Uruguay (BCU).  

El objetivo es:
- limpiar y procesar la serie de pagos con tarjeta (2015–2025, primer semestre),
- construir métricas anuales y semestrales,
- y generar visualizaciones en PNG listas para usar en presentaciones o publicaciones (por ejemplo, en LinkedIn).

El análisis y el código fueron realizados por Lucas Ortiz Gómez.


📂 Estructura del proyecto

```text
.
├── data
│   ├── raw/          # (opcional) datos crudos originales
│   └── processed/    # datos ya limpios / consolidados
│       └── uruguay_payment_trends.csv
├── figures/          # gráficos generados por el script
└── scripts/
    └── annual_summary.py

Los nombres de carpetas pueden ajustarse, pero la lógica general es:

data/processed/uruguay_payment_trends.csv → archivo maestro de entrada.

scripts/annual_summary.py → script principal de análisis.

figures/ → destino de las imágenes generadas.

🛠 Requisitos

Python 3.9+ (recomendado)

Paquetes de Python:
pandas
matplotlib

Podés instalarlos con: 
pip install pandas matplotlib

Si preferís un entorno virtual: 
python -m venv .venv
source .venv/bin/activate      # Linux / Mac
# o
.\.venv\Scripts\activate       # Windows

pip install pandas matplotlib

El script:

1: Lee el archivo data/processed/uruguay_payment_trends.csv.
2:Limpia y normaliza las columnas numéricas (amount_million, transaction_count).
3:Calcula métricas derivadas por semestre y por año.
4:Genera tablas agregadas (CSV) con los resultados.
5:Produce varias figuras en formato PNG dentro de figures/.

Al finalizar, verás algo similar en la consola:
Done
- Saved: data/processed/annual_summary.csv
- Saved: data/processed/annual_by_method.csv
- Saved: data/processed/cagr_summary.csv
- Figures in: figures

🧾 Descripción de los datos

El archivo principal de entrada es: data/processed/uruguay_payment_trends.csv

Contiene una serie semestral de pagos con tarjeta en Uruguay, con al menos las siguientes columnas:

1:year – Año (ej. 2015, 2016, …, 2025).
2:semester – Semestre (1 o 2).
3:payment_method – Método de pago (Debit Card, Credit Card).
4:amount_million – Monto total operado en millones de USD (texto tipo "$ 6.003" que luego se limpia).
5:transaction_count – Cantidad de transacciones (texto con separador de miles, ej. "239.125.637").

Otras columnas (source, average_amount, etc.) pueden estar presentes pero no son necesarias para correr el script.

Nota: En el dataset actual, el año 2025 solo contiene datos del primer semestre.
El script tiene en cuenta esto para no mezclar años “incompletos” en los gráficos anuales.

📊 Qué hace el script annual_summary.py

A grandes rasgos:

1:Limpieza de datos
2:Quita símbolos ($, puntos de miles, espacios).
3:Convierte columnas numéricas a tipos adecuados.
4:Filtra solo Debit Card y Credit Card.
5:Evita divisiones por cero eliminando filas con transaction_count == 0.
6:Métricas por semestre
7:Calcula el ticket promedio por operación:
\text{avg_amount_usd} = \frac{\text{amount_million} \times 1\,000\,000}{\text{transaction_count}}
8:Agregación anual por método
9:Suma por año y método:
  amount_million_year
  transaction_count_year
10:Ticket promedio ponderado anual:
\text{avg_amount_usd_year} = \frac{\text{amount_million_year} \times 1\,000\,000}{\text{transaction_count_year}}
11:Construcción de tablas anuales
annual_summary.csv
12:Contiene, por año: montos por débito y crédito,cantidad de transacciones por método, ticket promedio por método, monto total, participación de cada método sobre el total.
annual_by_method.csv
Tabla en formato “largo” con agregados anuales por (year, payment_method).
cagr_summary.csv
Tabla con tasas CAGR aproximadas para: montos anuales de débito, montos anuales de crédito, monto total.
13:Distinción entre años completos e incompletos: Identifica cuáles años tienen datos de ambos semestres (1 y 2).

Solo esos años “completos” se utilizan en: gráficos anuales, cálculo de CAGR.

🖼 Visualizaciones generadas

Todas las figuras se guardan en la carpeta figures/ (formato PNG, resolución 300 dpi) e incluyen una marca de agua suave con el nombre “Lucas Ortiz Gómez”.

trend_amount_million_cards.png
Tendencia de montos anuales (millones de USD) para débito y crédito.
Solo incluye años completos (ej. 2015–2024).
share_debit_credit.png
Barras apiladas que muestran la participación porcentual de débito y crédito sobre el total de montos operados cada año (solo años completos).

avg_ticket_usd_part1.png
Ticket promedio anual (USD por transacción) para débito y crédito en el primer sub–rango de años (aprox. primera mitad de la serie).

avg_ticket_usd_part2.png
Mismo análisis de ticket promedio, pero para el segundo sub–rango de años (aprox. la parte más reciente de la serie).

pospandemia_semester_amount_million_2022_2025.png
Análisis pospandemia:

Montos semestrales (millones de USD)

Desde 2022 S1 hasta 2025 S1

Barras lado a lado para débito y crédito, permitiendo ver la evolución en el período reciente.

💡 Ideas de análisis / insights

Algunos ejemplos de preguntas que pueden explorarse con estas figuras:

¿Cómo evolucionó el uso de tarjetas de débito vs crédito en Uruguay entre 2015 y 2024?

¿En qué medida cambió la participación de débito sobre el total pospandemia (2022–2025)?

¿El ticket promedio por operación crece, se mantiene o cae en el tiempo?

¿Hay cambios estructurales visibles alrededor del período de pandemia y pospandemia?


👤 Autor

Lucas Ortiz Gómez

Estudiante de Ingeniería en Biotecnología y Bioinformática

Interesado en análisis de datos, ciencias, finanzas y tecnología.

Este proyecto fue desarrollado como ejercicio de análisis y visualización de datos con Python.