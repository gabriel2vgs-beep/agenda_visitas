"""
scheduler.py
Gerencia a lógica de agendamento e validações relacionadas às visitas técnicas.
Atualmente contém funções básicas, mas já estruturado para evoluir.
"""

from datetime import datetime
from modules.database_manager import connect_db

# ---------------------------
# Verifica se já existe um agendamento no mesmo dia e técnico
# ---------------------------

def verificar_conflito(tecnico_id, data):
    """
    Retorna True se o técnico já possuir uma visita agendada na data informada.
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM agendamentos
        WHERE tecnico_id = ? AND data = ?
    """, (tecnico_id, data))
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado > 0


# ---------------------------
# Gera um resumo de visitas por técnico (para relatórios futuros)
# ---------------------------

def resumo_visitas():
    """
    Retorna uma contagem de visitas por técnico.
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.nome, COUNT(a.id)
        FROM agendamentos a
        JOIN tecnicos t ON a.tecnico_id = t.id
        GROUP BY t.nome
        ORDER BY t.nome
    """)
    data = cursor.fetchall()
    conn.close()

    return [{"tecnico": r[0], "total_visitas": r[1]} for r in data]
