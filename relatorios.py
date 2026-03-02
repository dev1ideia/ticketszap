# relatorios.py
from flask import Blueprint, render_template, session, redirect, url_for
from database import supabase

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/relatorio/vendas/<evento_id>')
def vendas_vendedor(evento_id):
    try:
        id_numerico = int(str(evento_id).strip())
        
        # 1. Busca dados do evento
        res_ev = supabase.table("eventos").select("nome").eq("id", id_numerico).single().execute()
        nome_evento = res_ev.data.get('nome', 'Evento') if res_ev.data else "Evento"

        # 2. Busca convites, funcionários e lotes
        res_conv = supabase.table("convites").select("vendedor_id, valor, lote_id").eq("evento_id", id_numerico).execute()
        res_func = supabase.table("funcionarios").select("id, nome").execute()
        res_lotes = supabase.table("lotes").select("id, nome, quantidade_total").eq("evento_id", id_numerico).execute()

        convites = res_conv.data or []
        nomes_funcs = {str(f['id']): f['nome'] for f in res_func.data} if res_func.data else {}
        
        # AJUSTE AQUI: Garantimos que o limite seja sempre um número (int), evitando o erro de 'dict object'
        info_lotes_map = {}
        if res_lotes.data:
            for l in res_lotes.data:
                # Se quantidade_total for None, vira 0. Se não, vira int.
                limite_val = int(l.get('quantidade_total') or 0)
                info_lotes_map[l['id']] = {'nome': l['nome'], 'limite': limite_val}

        # 3. Processamento de indicadores
        vendedores_stats = {}
        stats_lotes = {}
        total_financeiro = 0.0

        for c in convites:
            valor_venda = float(c.get('valor') or 0)
            total_financeiro += valor_venda

            # Agrupamento por Vendedor
            v_id = str(c.get('vendedor_id'))
            nome_v = nomes_funcs.get(v_id, "Venda Direta / Admin")
            if nome_v not in vendedores_stats:
                vendedores_stats[nome_v] = {'qtd': 0, 'financeiro': 0.0}
            vendedores_stats[nome_v]['qtd'] += 1
            vendedores_stats[nome_v]['financeiro'] += valor_venda

            # Agrupamento por Lote
            l_id = c.get('lote_id')
            lote_data = info_lotes_map.get(l_id, {'nome': "Lote Único / S.Lote", 'limite': 0})
            nome_l = lote_data['nome']
            
            if nome_l not in stats_lotes:
                stats_lotes[nome_l] = {
                    'qtd': 0, 
                    'total': 0.0, 
                    'limite': lote_data['limite']
                }
            stats_lotes[nome_l]['qtd'] += 1
            stats_lotes[nome_l]['total'] += valor_venda

        return render_template('relatorio_vendas.html', 
                               stats=vendedores_stats, 
                               stats_lotes=stats_lotes,
                               total=total_financeiro,
                               total_qtd=len(convites),
                               nome_evento=nome_evento)

    except Exception as e:
        return f"Erro ao processar relatório: {str(e)}", 500
    
# Rota da Portaria dentro do relatorios.py
@relatorios_bp.route('/portaria/<evento_id>')
def portaria(evento_id): # <--- O ID entra direto aqui como argumento
    try:
        # Converte para int (o segredo que aprendemos!)
        id_numerico = int(str(evento_id).strip())
        
        # 1. Busca dados do evento
        res_ev = supabase.table("eventos").select("*").eq("id", id_numerico).single().execute()
        evento_info = res_ev.data
        
        # 2. Busca os funcionários (para saber quem validou o ingresso)
        res_func = supabase.table("funcionarios").select("id, nome").execute()
        nomes_funcs = {str(f['id']): f['nome'] for f in res_func.data}

        # 3. Busca os convites deste evento
        res_conv = supabase.table("convites").select("*").eq("evento_id", id_numerico).execute()
        convites = res_conv.data if res_conv.data else []

        return render_template('portaria.html', 
                       evento=evento_info, 
                       convites=convites, 
                       nomes_funcs=nomes_funcs)

    except Exception as e:
        return f"Erro: {str(e)}"    