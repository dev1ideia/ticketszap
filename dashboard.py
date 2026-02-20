
# dashboard.py
from flask import render_template_string

def renderizar_dashboard(evento_id, supabase, BASE_STYLE):
    # 1. Busca os dados
    res = supabase.table("convites").select("*").eq("evento_id", evento_id).execute()
    convites = res.data if res.data else []
    
    total = len(convites)
    presentes = len([c for c in convites if c.get('status') == False])
    ausentes = total - presentes
    percentual = (presentes / total * 100) if total > 0 else 0

    return render_template_string(f'''
        {BASE_STYLE}
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        
        <div class="card" style="text-align:center;">
            <h2 style="color: #075E54;">📊 Painel do Promoter</h2>
            <p style="font-size: 14px; color: #666; margin-bottom: 20px;">Acompanhamento em Tempo Real</p>
            
            <div style="width: 200px; margin: 0 auto 20px;">
                <canvas id="graficoPizza"></canvas>
            </div>

            <div style="background:#f8f9fa; padding:15px; border-radius:15px; margin-bottom:15px;">
                <span style="font-size:12px; color:#888;">STATUS DA CASA</span>
                <h1 style="margin:5px 0; color:#25d366;">{presentes} / {total}</h1>
                <p style="font-size: 12px; color: #666;">{percentual:.1f}% preenchida</p>
            </div>

            <div style="display: flex; gap: 10px;">
                <div style="flex:1; background:white; padding:15px; border-radius:12px; border:1px solid #eee;">
                    <small style="color:#dc3545; font-weight:bold;">NÃO CHEGOU</small>
                    <h3 style="margin:5px 0;">{ausentes}</h3>
                </div>
                <div style="flex:1; background:white; padding:15px; border-radius:12px; border:1px solid #eee;">
                    <small style="color:#075E54; font-weight:bold;">VENDIDOS</small>
                    <h3 style="margin:5px 0;">{total}</h3>
                </div>
            </div>

            <button onclick="location.reload()" style="margin-top:20px; width:100%; padding:15px; background:#075E54; color:white; border:none; border-radius:10px; font-weight:bold;">🔄 ATUALIZAR DADOS</button>
            <br><br>
            <a href="/escolher_dashboard" style="text-decoration:none; color:#999; font-size:12px;">⬅️ Voltar para seleção</a>
        </div>

        <script>
            var ctx = document.getElementById('graficoPizza').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut', // 'doughnut' é o formato pizza com furo (mais moderno)
                data: {{
                    labels: ['Presentes', 'Ausentes'],
                    datasets: [{{
                        data: [{presentes}, {ausentes}],
                        backgroundColor: ['#25d366', '#ff4d4d'],
                        borderWidth: 0,
                        hoverOffset: 4
                    }}]
                }},
                options: {{
                    cutout: '70%', // Faz o furo no meio
                    plugins: {{
                        legend: {{ display: false }} // Esconde a legenda para ficar limpo
                    }}
                }}
            }});
        </script>
    ''')