import pandas as pd

def get_emails_from_excel(filepath, column_name='Email'):
    try:
        df = pd.read_excel(filepath, engine='openpyxl')
        if column_name not in df.columns:
            available_cols = ", ".join(df.columns)
            return None, f"Coluna '{column_name}' não encontrada. Colunas disponíveis: {available_cols}"
        
        emails = df[column_name].dropna().astype(str).unique().tolist()
        return emails, f"{len(emails)} emails carregados com sucesso."
    except Exception as e:
        return None, f"Erro ao ler o arquivo Excel: {e}"