document.addEventListener('DOMContentLoaded', function () {

    // =====================================================
    // ELEMENTOS PRINCIPAIS
    // =====================================================
    const calendarEl = document.getElementById('calendar');
    const modalNovo = new bootstrap.Modal(document.getElementById('modalNovoAgendamento'));
    const modalEdit = new bootstrap.Modal(document.getElementById('modalDetalhes'));
    const modalDup = new bootstrap.Modal(document.getElementById('modalDuplicar'));

    const formNovo = document.getElementById('formNovoAgendamento');
    const formEdit = document.getElementById('formEditarAgendamento');
    const formDup = document.getElementById('formDuplicar');

    // =====================================================
    // FUNÇÃO DE RECARREGAR O CALENDÁRIO
    // =====================================================
    const refreshCalendar = () => {
        calendar.refetchEvents();
    };

    // =====================================================
    // CONFIGURAÇÃO DO CALENDÁRIO
    // =====================================================
    const calendar = new FullCalendar.Calendar(calendarEl, {
        locale: 'pt-br',
        themeSystem: 'bootstrap5',
        initialView: 'dayGridMonth',
        height: 'auto',
        selectable: true,
        editable: false,
        events: '/api/agendamentos',

        dateClick: function (info) {
            document.getElementById('novaData').value = info.dateStr;
            modalNovo.show();
        },

        eventClick: function (info) {
            const event = info.event;

            // Preenche modal de edição
            document.getElementById('editAgendamentoId').value = event.extendedProps.id;
            document.getElementById('editCliente').value = event.extendedProps.cliente_id || "";
            document.getElementById('editStatus').value = event.extendedProps.status;
            document.getElementById('editObservacoes').value = event.extendedProps.observacoes || "";

            // Atualiza lista de unidades
            fetch(`/api/unidades/${event.extendedProps.cliente_id}`)
                .then(r => r.json())
                .then(unidades => {
                    const sel = document.getElementById('editUnidade');
                    sel.innerHTML = '';
                    unidades.forEach(u => {
                        const opt = document.createElement('option');
                        opt.value = u[0];
                        opt.textContent = u[1];
                        sel.appendChild(opt);
                    });
                    sel.value = event.extendedProps.unidade_id;
                });

            document.getElementById('editTecnico').value = event.extendedProps.tecnico_id || "";
            modalEdit.show();
        },

        eventContent: function (arg) {
            const status = arg.event.extendedProps.status || "";
            const title = arg.event.title;
            let color = "";

            switch (status) {
                case "Pendente Conf.":
                    color = "#f1c40f";
                    break;
                case "Confirmado":
                    color = "#27ae60";
                    break;
                case "Cancelado":
                    color = "#e74c3c";
                    break;
                case "Reagendado":
                    color = "#e67e22";
                    break;
                default:
                    color = "#3498db";
            }

            return {
                html: `<div style="background:${color};color:white;border-radius:4px;padding:2px 4px;font-size:0.8rem;">${title}</div>`
            };
        },

        eventDidMount: function (info) {
            new bootstrap.Tooltip(info.el, {
                title: `
                    <b>Cliente:</b> ${info.event.extendedProps.cliente}<br>
                    <b>Unidade:</b> ${info.event.extendedProps.unidade}<br>
                    <b>Status:</b> ${info.event.extendedProps.status}<br>
                    <b>Técnico:</b> ${info.event.extendedProps.tecnico}<br>
                    <b>Obs:</b> ${info.event.extendedProps.observacoes || ''}
                `,
                html: true,
                placement: 'top',
                trigger: 'hover'
            });
        }
    });

    calendar.render();

    // =====================================================
    // FORM NOVO AGENDAMENTO
    // =====================================================
    formNovo.addEventListener('submit', e => {
        e.preventDefault();

        const formData = new FormData(formNovo);
        fetch('/add_agendamento', {
            method: 'POST',
            body: formData
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    modalNovo.hide();
                    refreshCalendar();
                } else {
                    alert("Erro ao salvar agendamento!");
                }
            });
    });

    // =====================================================
    // FORM EDITAR AGENDAMENTO
    // =====================================================
    formEdit.addEventListener('submit', e => {
        e.preventDefault();

        const agId = document.getElementById('editAgendamentoId').value;
        const formData = new FormData(formEdit);

        fetch(`/update_agendamento/${agId}`, {
            method: 'POST',
            body: formData
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    modalEdit.hide();
                    refreshCalendar();
                } else {
                    alert("Erro ao atualizar!");
                }
            });
    });

    // =====================================================
    // EXCLUIR AGENDAMENTO
    // =====================================================
    document.getElementById('btnExcluir').addEventListener('click', () => {
        const agId = document.getElementById('editAgendamentoId').value;
        if (!confirm("Tem certeza que deseja excluir este agendamento?")) return;

        fetch(`/delete_agendamento/${agId}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    modalEdit.hide();
                    refreshCalendar();
                } else {
                    alert("Erro ao excluir!");
                }
            });
    });

    // =====================================================
    // DUPLICAR AGENDAMENTO
    // =====================================================
    document.getElementById('btnDuplicar').addEventListener('click', () => {
        const agId = document.getElementById('editAgendamentoId').value;
        document.getElementById('dupId').value = agId;
        modalEdit.hide();
        modalDup.show();
    });

    formDup.addEventListener('submit', e => {
        e.preventDefault();
        const agId = document.getElementById('dupId').value;
        const formData = new FormData(formDup);

        fetch(`/duplicate_agendamento/${agId}`, {
            method: 'POST',
            body: formData
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    modalDup.hide();
                    refreshCalendar();
                } else {
                    alert("Erro ao duplicar!");
                }
            });
    });

    // =====================================================
    // CLIENTE -> UNIDADE DINÂMICO (NOVO)
    // =====================================================
    const novoClienteSelect = document.getElementById('novoCliente');
    const novaUnidadeSelect = document.getElementById('novaUnidade');

    if (novoClienteSelect) {
        novoClienteSelect.addEventListener('change', function () {
            const clienteId = this.value;
            novaUnidadeSelect.innerHTML = '<option>Carregando...</option>';

            fetch(`/api/unidades/${clienteId}`)
                .then(res => res.json())
                .then(data => {
                    novaUnidadeSelect.innerHTML = '';
                    data.forEach(u => {
                        const opt = document.createElement('option');
                        opt.value = u[0];
                        opt.textContent = u[1];
                        novaUnidadeSelect.appendChild(opt);
                    });
                });
        });
    }

    // CLIENTE -> UNIDADE DINÂMICO (EDIT)
    const editClienteSelect = document.getElementById('editCliente');
    const editUnidadeSelect = document.getElementById('editUnidade');

    if (editClienteSelect) {
        editClienteSelect.addEventListener('change', function () {
            const clienteId = this.value;
            editUnidadeSelect.innerHTML = '<option>Carregando...</option>';

            fetch(`/api/unidades/${clienteId}`)
                .then(res => res.json())
                .then(data => {
                    editUnidadeSelect.innerHTML = '';
                    data.forEach(u => {
                        const opt = document.createElement('option');
                        opt.value = u[0];
                        opt.textContent = u[1];
                        editUnidadeSelect.appendChild(opt);
                    });
                });
        });
    }
});
