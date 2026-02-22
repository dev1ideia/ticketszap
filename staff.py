
from flask import render_template_string

def renderizar_gerenciamento_staff(evento_id, staff_list, BASE_STYLE):
    # Removido o 'f' antes das aspas triplas para evitar conflito de chaves
    return render_template_string('''
        ''' + BASE_STYLE + '''
        <style>
            .btn-status {
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 11px;
                font-weight: bold;
                text-decoration: none;
                transition: 0.3s;
                display: inline-block;
                text-align: center;
                min-width: 90px;
            }
            /* Cores para o status Ativo (Verde) */
            .ativo { background: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32; }
            /* Cores para o status Pausado (Vermelho) */
            .pausado { background: #ffebee; color: #c62828; border: 1px solid #c62828; }
            
            .card-staff {
                background:#f9f9f9; 
                padding:15px; 
                border-radius:12px; 
                margin-bottom:12px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
        </style>

        <div class="card" style="max-width:500px; margin:auto; background:#fff; padding: 20px; border-radius: 15px; box-sizing: border-box;">
            <h3 style="margin-bottom:5px; color:#333; text-align: center;">👥 Equipe do Evento</h3>
            <p style="font-size:13px; color:#666; margin-bottom:20px; text-align: center;">Controle de acesso e desempenho</p>
            
            {% for m in staff %}
            <div class="card-staff" style="border-left: 5px solid {{ '#2ecc71' if m.funcionarios.ativo else '#e74c3c' }};">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <strong style="font-size:16px; color:#333; display:block;">{{ m.funcionarios.nome }}</strong>
                        <span style="font-size:12px; color:{{ '#2ecc71' if m.funcionarios.ativo else '#e74c3c' }}; font-weight:bold;">
                            ● {{ 'VENDAS LIBERADAS' if m.funcionarios.ativo else 'VENDAS PAUSADAS' }}
                        </span>
                    </div>
                    
                    <a href="/status_vendedor/{{ m.funcionarios.id }}/{{ evento_id }}" 
                       class="btn-status {{ 'ativo' if m.funcionarios.ativo else 'pausado' }}">
                        {{ '🚫 PAUSAR' if m.funcionarios.ativo else '▶️ ATIVAR' }}
                    </a>
                </div>

                <div style="background:#fff; border:1px solid #ddd; padding:10px 15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:12px; color:#666;">🎫 Total de Vendas:</span> 
                    <strong style="font-size:18px; color:#1a73e8;">{{ m.total_vendas }}</strong>
                </div>
            </div>
            {% else %}
                <div style="text-align:center; padding:40px 20px; color:#999;">
                    <p style="font-size:40px; margin-bottom:10px;">🏘️</p>
                    <p>Nenhum staff vinculado.</p>
                </div>
            {% endfor %}
            
            <a href="/painel" style="display:block; text-align:center; margin-top:25px; color:#666; text-decoration:none; font-size:14px; font-weight: bold;">⬅️ Voltar ao Painel</a>
        </div>
    ''', staff=staff_list, evento_id=evento_id)