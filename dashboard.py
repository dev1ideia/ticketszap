# dashboard.py
from flask import render_template_string
from urllib.parse import quote

def renderizar_dashboard(evento_id, supabase, BASE_STYLE):
    # 1. Busca os dados do EVENTO (saldo e quem criou)
    evento_res = supabase.table("eventos").select("nome, saldo_creditos, criado_por").eq("id", evento_id).single().execute()
    
    if not evento_res.data:
        return "Evento não encontrado."
        
    evento_info = evento_res.data
    nome_evento = evento_info.get('nome', 'Evento')
    saldo = evento_info.get('saldo_creditos', 0)
    
    # Garantimos que id_promoter seja tratado como string para evitar o erro de 'int'
    id_promoter_raw = evento_info.get('criado_por', '0')
    id_promoter_str = str(id_promoter_raw)

    # 2. Busca o NOME do Promoter na tabela 'promoter'
    nome_promoter = "Não identificado"
    if id_promoter_raw:
        promoter_res = supabase.table("promoter").select("nome").eq("id", id_promoter_raw).single().execute()
        if promoter_res.data:
            nome_promoter = promoter_res.data.get('nome', 'Não identificado')

    # 3. Busca os dados dos Convites
    res = supabase.table("convites_dashboard").select("*").eq("evento_id", evento_id).execute()
    convites = res.data if res.data else []
    
    # 4. Busca os últimos 5 (já validados)
    recentes_res = supabase.table("convites_dashboard") \
    .select("nome_cliente, data_leitura_formatada") \
    .eq("evento_id", evento_id) \
    .eq("status", False) \
    .not_.is_("data_leitura", "null") \
    .order("data_leitura", desc=True) \
    .limit(5).execute()

    recentes = recentes_res.data if recentes_res.data else []
    
    total = len(convites)
    presentes = len([c for c in convites if c.get('status') == False])
    ausentes = total - presentes
    percentual = (presentes / total * 100) if total > 0 else 0

    # Lógica de cor do saldo
    cor_saldo = "#2ecc71" if saldo > 50 else "#f1c40f" if saldo > 10 else "#e74c3c"

    # Link WhatsApp
    mensagem_zap = f"Olá! Quero recarregar créditos para o Evento: {nome_evento}. (Promoter: {nome_promoter} | ID: {id_promoter_str})"
    link_final = f"https://wa.me/5516996042731?text={quote(mensagem_zap)}"

    # Lista de recentes HTML
    lista_html = ""
    for r in recentes:
        dt = r.get('data_leitura_formatada', '--:--')
        lista_html += f'''
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-size: 13px;">
                <span style="color: #333;">👤 {r['nome_cliente']}</span>
                <span style="color: #25d366; font-weight: bold;">{dt}</span>
            </div>
        '''
    if not recentes:
        lista_html = "<p style='color:#999; font-size:12px;'>Nenhuma entrada registrada ainda.</p>"

    return render_template_string(f'''
        {BASE_STYLE}
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        
        <div class="card" style="text-align:center;">
            <div style="background: #f8f9fa; padding: 15px; border-radius: 15px; border: 1px solid #eee; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                <div style="text-align: left;">
                    <small style="color: #888; font-size: 10px; text-transform: uppercase;">Créditos do Evento</small>
                    <h3 style="margin: 0; color: {cor_saldo};">{saldo}</h3>
                </div>
                <a href="{link_final}" target="_blank" style="text-decoration: none; background: #075E54; color: white; font-size: 10px; padding: 8px 12px; border-radius: 5px; font-weight: bold; text-align: center;">
                    RECARREGAR<br><span style="font-size: 8px; opacity: 0.8;">ID: {id_promoter_str}</span>
                </a>
            </div>

            <h2 style="color: #075E54; margin-bottom:5px;">📊 {nome_evento}</h2>
            <p style="font-size: 12px; color: #666; margin-bottom: 20px;">{percentual:.1f}% preenchida</p>
            
            <div style="width: 180px; margin: 0 auto 20px;">
                <canvas id="graficoPizza"></canvas>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 25px;">
                <div style="background: #e8f5e9; padding: 15px; border-radius: 12px;">
                    <div style="font-size: 20px; font-weight: bold; color: #2e7d32;">{presentes}</div>
                    <div style="font-size: 11px; color: #4caf50; font-weight: bold;">PRESENTES</div>
                </div>
                <div style="background: #ffebee; padding: 15px; border-radius: 12px;">
                    <div style="font-size: 20px; font-weight: bold; color: #c62828;">{ausentes}</div>
                    <div style="font-size: 11px; color: #f44336; font-weight: bold;">AUSENTES</div>
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
                        borderWidth: 0,
                        cutout: '70%'
                    }}]
                }},
                options: {{
                    plugins: {{ legend: {{ display: false }} }},
                    maintainAspectRatio: false
                }}
            }});
        </script>
    ''')