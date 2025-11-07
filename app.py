from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from modules.database_manager import (
    init_db, connect,
    get_all_clientes, add_cliente,
    get_all_unidades, add_unidade, get_unidades_por_cliente,
    add_usuario, get_usuario_por_codigo,
    get_all_tecnicos, add_tecnico,
    add_agendamento, get_all_agendamentos,
    update_agendamento, delete_agendamento
)
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"
init_db()

# =====================================================
# LOGIN / LOGOUT
# =====================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        codigo = request.form['codigo']
        user = get_usuario_por_codigo(codigo)

        if user:
            session['usuario_id'] = user[0]
            session['nome'] = user[1]
            session['codigo'] = user[2]
            session['tipo'] = user[3]
            session['cliente_id'] = user[4]
            if user[3] == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('agenda_cliente'))
        else:
            flash("Código de acesso inválido!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso!", "info")
    return redirect(url_for('login'))

# =====================================================
# PAINEL ADMIN
# =====================================================
@app.route('/')
def index():
    if 'tipo' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))

    clientes = get_all_clientes()
    unidades = get_all_unidades()
    tecnicos = get_all_tecnicos()

    # Buscar todos os usuários com nome do cliente vinculado
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT u.id, u.nome, u.codigo_acesso, u.tipo, c.nome AS cliente, u.cliente_id
        FROM usuarios u
        LEFT JOIN clientes c ON u.cliente_id = c.id
        ORDER BY u.nome
    """)
    usuarios = c.fetchall()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        clientes=clientes,
        unidades=unidades,
        tecnicos=tecnicos,
        usuarios=usuarios
    )

# =====================================================
# PAINEL CLIENTE
# =====================================================
@app.route('/agenda_cliente')
def agenda_cliente():
    if 'tipo' not in session or session['tipo'] != 'cliente':
        return redirect(url_for('login'))

    cliente_id = session['cliente_id']
    unidades = get_unidades_por_cliente(cliente_id)
    return render_template(
        'agenda_cliente.html',
        cliente_nome=session['nome'],
        unidades=unidades
    )

# =====================================================
# CRUD ADMIN - CLIENTES, UNIDADES, USUÁRIOS, TÉCNICOS
# =====================================================
@app.route('/add_cliente', methods=['POST'])
def add_cliente_route():
    nome = request.form['nome']
    add_cliente(nome)
    flash("Cliente cadastrado com sucesso!", "success")
    return redirect(url_for('index'))


@app.route('/add_unidade', methods=['POST'])
def add_unidade_route():
    nome = request.form['nome']
    cliente_id = request.form['cliente_id']
    add_unidade(nome, cliente_id)
    flash("Unidade cadastrada com sucesso!", "success")
    return redirect(url_for('index'))


@app.route('/add_usuario', methods=['POST'])
def add_usuario_route():
    nome = request.form['nome']
    codigo = request.form['codigo']
    tipo = request.form['tipo']
    cliente_id = request.form.get('cliente_id') or None
    add_usuario(nome, codigo, tipo, cliente_id)
    flash("Usuário criado com sucesso!", "success")
    return redirect(url_for('index'))


@app.route('/add_tecnico', methods=['POST'])
def add_tecnico_route():
    nome = request.form['nome']
    add_tecnico(nome)
    flash("Técnico cadastrado com sucesso!", "success")
    return redirect(url_for('index'))

# =====================================================
# EDIÇÃO E EXCLUSÃO - CLIENTES, UNIDADES, USUÁRIOS
# =====================================================
@app.route('/update_cliente/<int:id>', methods=['POST'])
def update_cliente_route(id):
    nome = request.form['nome']
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE clientes SET nome=? WHERE id=?", (nome, id))
    conn.commit()
    conn.close()
    flash("Cliente atualizado com sucesso!", "success")
    return jsonify({'success': True})


@app.route('/delete_cliente/<int:id>', methods=['DELETE'])
def delete_cliente_route(id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/update_unidade/<int:id>', methods=['POST'])
def update_unidade_route(id):
    nome = request.form['nome']
    cliente_id = request.form['cliente_id']
    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE unidades SET nome=?, cliente_id=? WHERE id=?", (nome, cliente_id, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/delete_unidade/<int:id>', methods=['DELETE'])
def delete_unidade_route(id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM unidades WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/update_usuario/<int:id>', methods=['POST'])
def update_usuario_route(id):
    data = request.get_json()
    conn = connect()
    c = conn.cursor()
    c.execute("""
        UPDATE usuarios
        SET nome=?, codigo_acesso=?, tipo=?, cliente_id=?
        WHERE id=?
    """, (data['nome'], data['codigo'], data['tipo'], data['cliente_id'] or None, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/delete_usuario/<int:id>', methods=['DELETE'])
def delete_usuario_route(id):
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# =====================================================
# AGENDAMENTOS (com filtro por técnico)
# =====================================================
@app.route('/add_agendamento', methods=['POST'])
def add_agendamento_route():
    data = request.form['data']
    cliente_id = request.form['cliente_id']
    unidade_id = request.form['unidade_id']
    tecnico_id = request.form['tecnico_id']
    status = request.form['status']
    observacoes = request.form['observacoes']
    add_agendamento(cliente_id, unidade_id, tecnico_id, data, status, observacoes)
    return jsonify({'success': True})


@app.route('/update_agendamento/<int:ag_id>', methods=['POST'])
def update_agendamento_route(ag_id):
    cliente_id = request.form['cliente_id']
    unidade_id = request.form['unidade_id']
    tecnico_id = request.form['tecnico_id']
    status = request.form['status']
    observacoes = request.form['observacoes']
    update_agendamento(ag_id, cliente_id, unidade_id, tecnico_id, status, observacoes)
    return jsonify({'success': True})


@app.route('/delete_agendamento/<int:ag_id>', methods=['DELETE'])
def delete_agendamento_route(ag_id):
    delete_agendamento(ag_id)
    return jsonify({'success': True})


@app.route('/duplicate_agendamento/<int:ag_id>', methods=['POST'])
def duplicate_agendamento_route(ag_id):
    data_nova = request.form['data']
    todos = get_all_agendamentos()
    for ev in todos:
        if ev["id"] == ag_id:
            cliente_id = ev["extendedProps"]["cliente_id"]
            unidade_id = ev["extendedProps"]["unidade_id"]
            tecnico_id = ev["extendedProps"]["tecnico_id"]
            status = ev["extendedProps"]["status"]
            observacoes = ev["extendedProps"]["observacoes"]
            add_agendamento(cliente_id, unidade_id, tecnico_id, data_nova, status, observacoes)
            return jsonify({'success': True})
    return jsonify({'success': False}), 404

# =====================================================
# 🔧 CORRIGIDO: API DE AGENDAMENTOS
# =====================================================
@app.route('/api/agendamentos')
def api_agendamentos():
    tipo = session.get('tipo')
    cliente_id_sessao = session.get('cliente_id')
    tecnico_id = request.args.get('tecnico_id')
    eventos = get_all_agendamentos(tecnico_id=tecnico_id) if tecnico_id else get_all_agendamentos()

    # Admin vê tudo
    if tipo == 'admin':
        return jsonify(eventos)

    # Cliente vê só seus eventos
    eventos_filtrados = []
    for ev in eventos:
        if ev['extendedProps']['cliente_id'] == cliente_id_sessao:
            eventos_filtrados.append(ev)
        else:
            eventos_filtrados.append({
                "title": "Data indisponível",
                "start": ev["start"],
                "backgroundColor": "#95a5a6",
                "borderColor": "#95a5a6"
            })
    return jsonify(eventos_filtrados)


@app.route('/api/unidades/<int:cliente_id>')
def api_unidades(cliente_id):
    unidades = get_unidades_por_cliente(cliente_id)
    return jsonify(unidades)

# =====================================================
# EXECUÇÃO
# =====================================================
if __name__ == '__main__':
    app.run(debug=True)
