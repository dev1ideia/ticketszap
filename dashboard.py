
# dashboard.py
from flask import render_template_string

def renderizar_dashboard(evento_id, supabase, BASE_STYLE):
    # 1. Busca os dados gerais para os contadores
    res = supabase.table("convites_dashboard") \
    .select("*") \
    .eq("evento_id", evento_id) \
    .execute()

    convites = res.data if res.data else []
    
   # 2. Busca os últimos 5 que entraram (Somente quem já validou)
    recentes = supabase.table("convites_dashboard") \
    .select("nome_cliente, data_leitura_formatada") \
    .eq("evento_id", evento_id) \
    .eq("status", False) \
    .not_.is_("data_leitura", "null") \
    .order("data_leitura", desc=True) \
    .limit(5) \
    .execute()

    recentes = recentes.data if recentes.data else []
    total = len(convites)
    presentes = len([c for c in convites if c.get('status') == False])
    ausentes = total - presentes
    percentual = (presentes / total * 100) if total > 0 else 0

    # Criando o HTML da lista de recentes
    lista_html = ""
    for r in recentes:
        dt = r.get('data_leitura_formatada')
        # Tenta pegar a hora, se falhar ou for nulo, mostra --:--
        hora =  dt if dt else "--:--"
        
        lista_html += f'''
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-size: 13px;">
                <span style="color: #333;">👤 {r['nome_cliente']}</span>
                <span style="color: #25d366; font-weight: bold;">{hora}</span>
            </div>
        '''
    
    if not recentes:
        lista_html = "<p style='color:#999; font-size:12px;'>Nenhuma entrada registrada ainda.</p>"

    return render_template_string(f'''
        {BASE_STYLE}
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        
        <div class="card" style="text-align:center;">
            <h2 style="color: #075E54; margin-bottom:5px;">📊 Painel do Promoter</h2>
            <p style="font-size: 12px; color: #666; margin-bottom: 20px;">Acompanhamento em Tempo Real</p>
            
            <div style="width: 180px; margin: 0 auto 20px;">
                <canvas id="graficoPizza"></canvas>
            </div>

            <div style="background:#f8f9fa; padding:15px; border-radius:15px; margin-bottom:15px;">
                <span style="font-size:11px; color:#888; text-transform:uppercase;">Status da Casa</span>
                <h1 style="margin:5px 0; color:#25d366;">{presentes} / {total}</h1>
                <p style="font-size: 12px; color: #666;">{percentual:.1f}% preenchida</p>
            </div>

            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <div style="flex:1; background:white; padding:12px; border-radius:12px; border:1px solid #eee;">
                    <small style="color:#dc3545; font-weight:bold;">NÃO CHEGOU</small>
                    <h3 style="margin:5px 0;">{ausentes}</h3>
                </div>
                <div style="flex:1; background:white; padding:12px; border-radius:12px; border:1px solid #eee;">
                    <small style="color:#075E54; font-weight:bold;">VENDIDOS</small>
                    <h3 style="margin:5px 0;">{total}</h3>
                </div>
            </div>

            <div style="text-align: left; background: #fff; padding: 15px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 20px;">
                <p style="color: #075E54; font-size: 11px; font-weight: bold; text-transform: uppercase; margin-top: 0; margin-bottom: 10px; border-bottom: 2px solid #25d366; display: inline-block;">🏃 Recém Chegados</p>
                {lista_html}
            </div>

            <button onclick="location.reload()" style="width:100%; padding:15px; background:#075E54; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🔄 ATUALIZAR</button>
            <br><br>
            <a href="/escolher_dashboard" style="text-decoration:none; color:#999; font-size:12px;">⬅️ Voltar para seleção</a>
        </div>

        <script>
            var ctx = document.getElementById('graficoPizza').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Presentes', 'Ausentes'],
                    datasets: [{{
                        data: [{presentes}, {ausentes}],
                        backgroundColor: ['#25d366', '#ff4d4d'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    cutout: '75%',
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        </script>
    ''')