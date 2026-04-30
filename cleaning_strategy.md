# Data Cleaning Strategy

| Column Name | Mechanism | Decision | Reasoning |
| :--- | :--- | :--- | :--- |
| race | MNAR | Impute | Privacy concern, keep as "Unknown" category. |
| medical_specialty | MAR | Group | High missingness; group into "General" vs "Specialty". |
| payer_code | MCAR | Drop | Not relevant to readmission prediction. |

## Execution Code
```python
# 1. DROP the MCAR columns
df = df.drop(columns=['payer_code'])
# 2. IMPUTE the MNAR columns
df['race'] = df['race'].fillna('Unknown')
# 3. GROUP the MAR columns
df['medical_specialty'] = df['medical_specialty'].fillna('General')
