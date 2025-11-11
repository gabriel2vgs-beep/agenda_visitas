import os
import psycopg2
from urllib.parse import urlparse

# =====================================================
# CONFIGURAÇÃO DA CONEXÃO COM POSTGRESQL
# =====================================================
def connect():
    """Conecta ao banco PostgreSQL usando DATABASE_URL do ambiente"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise Exception("❌ Variável DATABASE_URL não encontrada!")
    result = urlparse(db_url)
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    return conn


# =====================================================
# INICIALIZAÇÃO DO BANCO (garante tabelas existentes)
# =====================================================
def init_db():
    conn = connect()
    c = conn.cursor()

    # CLIENTES
    c.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL
        )
    """)

    # UNIDADES
    c.execute("""
        CREATE TABLE IF NOT EXISTS unidades (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            cliente_id INTEGER NOT NULL REFERENCES clientes(id)
        )
    """)

    # USUÁRIOS
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            codigo_acesso TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('admin', 'cliente')),
            cliente_id INTEGER REFERENCES clientes(id)
        )
    """)

    # TÉCNICOS
    c.execute("""
        CREATE TABLE IF NOT EXISTS tecnicos (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL
        )
    """)

    # AGENDAMENTOS
    c.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            unidade_id INTEGER REFERENCES unidades(id),
            tecnico_id INTEGER REFERENCES tecnicos(id),
            data TEXT,
            status TEXT,
            observacoes TEXT
        )
    """)

    conn.commit()
    conn.close()


# =====================================================
# CLIENTES
# =====================================================
def add_cliente(nome):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nome) VALUES (%s)", (nome,))
    conn.commit()
    conn.close()


def get_all_clientes():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM clientes ORDER BY nome")
    data = c.fetchall()
    conn.close()
    return data


# =====================================================
# UNIDADES
# =====================================================
def add_unidade(nome, cliente_id):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO unidades (nome, cliente_id) VALUES (%s, %s)", (nome, cliente_id))
    conn.commit()
    conn.close()


def get_unidades_por_cliente(cliente_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM unidades WHERE cliente_id = %s ORDER BY nome", (cliente_id,))
    data = c.fetchall()
    conn.close()
    return data


def get_all_unidades():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.nome, c.nome AS cliente
        FROM unidades u
        LEFT JOIN clientes c ON u.cliente_id = c.id
        ORDER BY c.nome, u.nome
    """)
    data = c.fetchall()
    conn.close()
    return data


# =====================================================
# USUÁRIOS
# =====================================================
def add_usuario(nome, codigo_acesso, tipo, cliente_id=None):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO usuarios (nome, codigo_acesso, tipo, cliente_id)
        VALUES (%s, %s, %s, %s)
    """, (nome, codigo_acesso, tipo, cliente_id))
    conn.commit()
    conn.close()


def get_usuario_por_codigo(codigo):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE codigo_acesso = %s", (codigo,))
    user = c.fetchone()
    conn.close()
    return user


# =====================================================
# TÉCNICOS
# =====================================================
def add_tecnico(nome):
    conn = connect()
    c = conn.cursor()
    c.execute("INSERT INTO tecnicos (nome) VALUES (%s)", (nome,))
    conn.commit()
    conn.close()


def get_all_tecnicos():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT * FROM tecnicos ORDER BY nome")
    data = c.fetchall()
    conn.close()
    return data


# =====================================================
# AGENDAMENTOS
# =====================================================
def add_agendamento(cliente_id, unidade_id, tecnico_id, data, status, observacoes):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO agendamentos (cliente_id, unidade_id, tecnico_id, data, status, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (cliente_id, unidade_id, tecnico_id, data, status, observacoes))
    conn.commit()
    conn.close()


def get_all_agendamentos(tecnico_id=None):
    conn = connect()
    c = conn.cursor()

    base_query = """
        SELECT 
            a.id, a.data, a.status, a.observacoes,
            c.nome AS cliente, u.nome AS unidade, t.nome AS tecnico,
            a.cliente_id, a.unidade_id, a.tecnico_id
        FROM agendamentos a
        LEFT JOIN clientes c ON a.cliente_id = c.id
        LEFT JOIN unidades u ON a.unidade_id = u.id
        LEFT JOIN tecnicos t ON a.tecnico_id = t.id
    """

    if tecnico_id:
        base_query += " WHERE t.id = %s ORDER BY a.data ASC"
        c.execute(base_query, (tecnico_id,))
    else:
        base_query += " ORDER BY a.data ASC"
        c.execute(base_query)

    rows = c.fetchall()
    conn.close()

    events = []
    for r in rows:
        color = {
            "Pendente Conf.": "#f1c40f",
            "Confirmado": "#2ecc71",
            "Cancelado": "#e74c3c",
            "Reagendado": "#e67e22"
        }.get(r[2], "#3498db")

        title = f"{r[4]} - {r[5]}" if r[4] and r[5] else "Agendamento"

        events.append({
            "id": r[0],
            "title": title,
            "start": r[1],
            "backgroundColor": color,
            "borderColor": color,
            "extendedProps": {
                "status": r[2],
                "observacoes": r[3],
                "cliente": r[4],
                "unidade": r[5],
                "tecnico": r[6],
                "cliente_id": r[7],
                "unidade_id": r[8],
                "tecnico_id": r[9]
            }
        })
    return events


def update_agendamento(id, cliente_id, unidade_id, tecnico_id, status, observacoes):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        UPDATE agendamentos
        SET cliente_id = %s, unidade_id = %s, tecnico_id = %s, status = %s, observacoes = %s
        WHERE id = %s
    """, (cliente_id, unidade_id, tecnico_id, status, observacoes, id))
    conn.commit()
    conn.close()


def delete_agendamento(id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM agendamentos WHERE id = %s", (id,))
    conn.commit()
    conn.close()
