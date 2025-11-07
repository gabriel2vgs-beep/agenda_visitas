"""
utils.py
Funções utilitárias gerais do sistema Agenda 2026.
"""

from datetime import datetime

# ---------------------------
# Formatação de datas
# ---------------------------

def formatar_data_br(data_iso):
    """
    Converte uma data no formato ISO (YYYY-MM-DD)
    para o formato brasileiro (DD/MM/YYYY).
    """
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return data_iso


# ---------------------------
# Geração de cores por status
# ---------------------------

def cor_por_status(status):
    """
    Retorna a cor hexadecimal de acordo com o status do agendamento.
    """
    status = status.lower()
    if "confirmado" in status:
        return "#27ae60"  # verde
    elif "cancelado" in status:
        return "#e74c3c"  # vermelho
    elif "reagendado" in status:
        return "#e67e22"  # laranja
    else:
        return "#f1c40f"  # amarelo (pendente)
