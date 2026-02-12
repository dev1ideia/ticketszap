import io
import base64
import qrcode
import urllib.parse
import os
from flask import Flask, render_template_string, request, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave_padrao_segura')

# --- CONFIGURAÇÃO SUPABASE ---
URL_SUPABASE = os.getenv("URL_SUPABASE")
KEY_SUPABASE = os.getenv("KEY_SUPABASE")
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

# --- CSS BASE ATUALIZADO ---
# --- CSS BASE (Mantendo o seu e apenas somando os novos estilos da Landing) ---
BASE_STYLE = '''
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TicketZap | Gestão de Eventos</title>
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/128/3270/3270184.png">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/128/3270/3270184.png">
    <meta name="theme-color" content="#1a73e8">
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; margin: 0; padding: 15px; min-height: 100vh; }
        .card { background: white; padding: 25px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); width: 100%; max-width: 450px; text-align: center; margin: 0 auto; }
        .btn { width: 100%; padding: 16px; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s; display: inline-block; text-align: center; text-decoration: none; }
        .btn-primary { background: #1a73e8; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-whatsapp { background: #25D366; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        input, select { width: 100%; padding: 14px; margin: 8px 0 16px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; }
        .link-back { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; font-size: 14px; }
        hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
        
        /* Estilos Novos para os Grupos/Cards da Landing */
        .container { max-width: 800px; margin: 0 auto; }
        .feature-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; padding: 20px 0; 
        }
        .feature-card { 
            background: white; padding: 25px; border-radius: 20px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;
        }
        .qr-mockup {
            background: #f8f9fa; border: 2px dashed #1a73e8; border-radius: 20px;
            padding: 20px; display: inline-block; margin: 20px 0;
        }
    </style>
</head>
'''

# --- ROTA 1: LANDING PAGE (VITRINE) ---
@app.route('/')
def home():
    if 'promoter_id' in session: return redirect(url_for('painel'))
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="hero" style="text-align:center; padding: 40px 10px;">
            <div class="container">
                <img src="https://cdn-icons-png.flaticon.com/128/3270/3270184.png" style="width: 70px;">
                <h1 style="color: #1a73e8; font-size: 38px; margin: 15px 0;">TicketZap</h1>
                <p style="color: #555; font-size: 18px;">A solução inteligente para venda e controle de convites via WhatsApp.</p>
                
                <div class="qr-mockup">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=TicketZap" style="width: 120px;">
                    <p style="font-size: 12px; color: #1a73e8; font-weight: bold; margin-top: 10px;">ESCANEIE NA PORTARIA</p>
                </div>

                <div style="margin-top: 25px;">
                    <a href="/cadastro" class="btn btn-primary" style="max-width: 300px;">🚀 Quero ser um Promoter</a>
                    <a href="/login" class="link-back" style="font-weight: bold; color: #1a73e8;">Já tenho conta? Entrar</a>
                </div>
            </div>
        </div>

        <div class="container">
            <div class="feature-grid">
                <div class="feature-card">
                    <div style="font-size: 40px;">📱</div>
                    <h3>Portaria na Mão</h3>
                    <p style="color: #666; font-size: 14px;">Valide ingressos usando a câmera do celular, sem aparelhos extras.</p>
                </div>

                <div class="feature-card">
                    <div style="font-size: 40px;">💬</div>
                    <h3>Direto no Zap</h3>
                    <p style="color: #666; font-size: 14px;">O cliente recebe o convite automaticamente no WhatsApp.</p>
                </div>

                <div class="feature-card">
                    <div style="font-size: 40px;">📊</div>
                    <h3>Relatórios</h3>
                    <p style="color: #666; font-size: 14px;">Controle suas vendas e entradas em tempo real.</p>
                </div>
            </div>
        </div>

        <footer style="text-align: center; padding: 30px; color: #999; font-size: 12px;">
            &copy; 2026 TicketZap
        </footer>
    ''')

# --- ROTA 2: LOGIN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        celular = request.form.get('celular')
        senha = request.form.get('senha')
        res = supabase.table("promoter").select("*").eq("telefone", celular).execute()
        if res.data:
            user = res.data[0]
            if user['senha'] == senha:
                session['promoter_id'] = user['id']
                session['promoter_nome'] = user['nome']
                return redirect(url_for('painel'))
            else: erro = "Senha incorreta!"
        else: erro = "Promoter não encontrado."
            
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <h3>🔐 Acesso Promoter</h3>
            {{% if erro %}}<div style="color:red; margin-bottom:10px;">⚠️ {{{{erro}}}}</div>{{% endif %}}
            <form method="POST">
                <input type="tel" name="celular" placeholder="Seu Celular" required>
                <input type="password" name="senha" placeholder="Sua Senha" required>
                <button type="submit" class="btn btn-primary">Entrar</button>
            </form>
            <a href="/" class="link-back">⬅️ Voltar ao Início</a>
        </div>
    ''', erro=erro)

# --- ROTA 3: CADASTRO (COM LISTA DE CIDADES E VALIDAÇÃO COMPLETA) ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cidade = request.form.get('cidade_promoter')
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        try:
            check = supabase.table("promoter").select("id").eq("telefone", telefone).execute()
            if check.data:
                return "Erro: Este celular já está cadastrado!"

            supabase.table("promoter").insert({
                "nome": nome, 
                "cidade": cidade,
                "telefone": telefone, 
                "senha": senha,
                "valor_convite": 2.00
            }).execute()
            
            return '<script>alert("Cadastro realizado!"); window.location.href = "/login";</script>'
        except Exception as e:
            return f"Erro ao cadastrar: {e}"

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <h3 style="margin-bottom:20px;">📝 Novo Promoter</h3>
            <form method="POST">
                <input type="text" name="nome" placeholder="Nome Completo" required>

                <div style="text-align: left; margin-bottom: 5px;">
                    <label style="font-size: 12px; color: #666; margin-left: 5px;">📍 Cidade de Atuação</label>
                    <input list="cidades_frequentes" name="cidade_promoter" placeholder="Digite ou selecione..." required>
                    <datalist id="cidades_frequentes">
                        <option value="Araraquara - SP">
                        <option value="Américo Brasiliense - SP">
                        <option value="Matão - SP">
                        <option value="Santa Lúcia - SP">
                        <option value="Rincão - SP">
                        <option value="Motuca - SP">
                        <option value="São Carlos - SP">
                        <option value="Ibaté - SP">
                        <option value="Descalvado - SP">
                        <option value="Ribeirão Bonito - SP">
                        <option value="Ribeirão Preto - SP">
                        <option value="Bauru - SP">
                        <option value="Jaú - SP">
                        <option value="Taquaritinga - SP">
                        <option value="Jaboticabal - SP">
                        <option value="São José do Rio Preto - SP">
                        <option value="São Paulo - SP">
                    </datalist>
                </div>
               
                <input type="tel" id="tel_cadastro" name="telefone" placeholder="Celular (WhatsApp)" maxlength="11" required style="margin-bottom: 5px;">
                <p style="text-align: left; font-size: 11px; color: #666; margin: 0 0 15px 5px;">
                   Ex: 16991234567 (Apenas números)
                </p>

                <input type="password" name="senha" placeholder="Crie uma Senha" required>
                
                <button type="submit" class="btn btn-success" style="width:100%; margin-top:10px;">Criar Minha Conta</button>
            </form>
            <hr>
            <a href="/login" style="font-size:14px; color:#1a73e8; text-decoration:none;">Já tem conta? Faça Login</a>
        </div>

        <script>
            // Validação em tempo real: remove tudo que não for número
            const telInput = document.getElementById('tel_cadastro');
            telInput.addEventListener('input', function (e) {{
                e.target.value = e.target.value.replace(/\D/g, '');
            }});

            telInput.addEventListener('paste', function (e) {{
                let pasteData = (e.clipboardData || window.clipboardData).getData('text');
                if (/[^\\d]/.test(pasteData)) {{
                    e.preventDefault();
                    alert("Por favor, cole apenas números no campo de telefone.");
                }}
            }});
        </script>
    ''')

# --- ROTA 4: PAINEL (COM VALIDAÇÃO NO CAMPO DO CLIENTE TAMBÉM) ---
@app.route('/painel', methods=['GET', 'POST'])
def painel():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    p_id = session['promoter_id']
    
    # Busca dados do promoter
    promoter_info = supabase.table("promoter").select("valor_convite").eq("id", p_id).execute()
    if not promoter_info.data: 
        session.clear()
        return redirect(url_for('login'))
        
    taxa_unitaria = promoter_info.data[0].get('valor_convite', 2.00)

    if request.method == 'POST':
        evento_id = request.form.get('evento_id')
        cliente = request.form.get('nome_cliente')
        fone = request.form.get('telefone_cliente')
        
        # BUSCA NOME DO EVENTO
        res_ev = supabase.table("eventos").select("nome, data_evento").eq("id", evento_id).execute()
        nome_evento = res_ev.data[0].get('nome', 'Evento') if res_ev.data else "Evento"

        # GERA O CONVITE NO BANCO
        resposta = supabase.table("convites").insert({
            "nome_cliente": cliente, 
            "telefone": fone, 
            "promoter_id": p_id, 
            "evento_id": evento_id
        }).execute()
        
        token = resposta.data[0]['qrcode']
        link_visualizacao = f"https://ticketszap.com.br/v/{token}"
        
        msg_texto = (f"✅ *Seu Convite Chegou!*\\n\\n🎈 Evento: *{nome_evento}*\\n👤 Cliente: {cliente}\\n\\nAcesse seu QR Code aqui:\\n{link_visualizacao}")
        msg_codificada = urllib.parse.quote(msg_texto)
        
        # Limpeza extra no Python por segurança
        fone_limpo = "".join(filter(str.isdigit, fone))
        if not fone_limpo.startswith("55"): fone_limpo = "55" + fone_limpo
        
        link_wa = f"https://api.whatsapp.com/send?phone={fone_limpo}&text={msg_codificada}"

        return render_template_string(f'''
            {BASE_STYLE}
            <div class="card">
                <h2 style="color:#28a745;">✅ Sucesso!</h2>
                <p>Convite para <strong>{cliente}</strong> gerado.</p>
                <div style="background:#eee; padding:15px; border-radius:10px; margin:15px 0;">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={token}" style="width:100%; max-width:200px;">
                </div>
                <a href="{link_wa}" target="_blank" class="btn btn-whatsapp">📱 Enviar WhatsApp</a>
                <a href="/painel" class="link-back">⬅️ Criar outro</a>
            </div>
        ''')

    # Busca eventos para o painel
    res_eventos = supabase.table("promoter_eventos").select("*, eventos(*)").eq("promoter_id", p_id).execute()
    meus_eventos = []
    for item in res_eventos.data:
        if item['eventos']:
            ev = item['eventos']
            cont = supabase.table("convites").select("id", count="exact").eq("evento_id", ev['id']).execute()
            ev['total_pagar'] = (cont.count or 0) * taxa_unitaria
            meus_eventos.append(ev)

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 15px;">
                <h3 style="margin:0;">Olá, {{{{ session['promoter_nome'] }}}}!</h3>
                <a href="/logout" style="color:red; font-size:12px; text-decoration:none;">Sair</a>
            </div>
            
            <a href="/novo_evento" class="btn btn-secondary" style="margin-bottom:10px;">➕ Novo Evento</a>
            <a href="/relatorio" style="display:block; margin-bottom:15px; color:#1a73e8; text-decoration:none; font-weight:bold;">📊 Relatório de Vendas</a>
            <hr>
            
            <h4 style="text-align:left; margin-bottom:5px;">🎟️ Emitir Convite</h4>
            <form method="POST">
                <select name="evento_id">
                    {{% for ev in eventos %}}
                        <option value="{{{{ ev.id }}}}">{{{{ ev.nome }}}}</option>
                    {{% endfor %}}
                </select>
                <input type="text" name="nome_cliente" placeholder="Nome do Cliente" required>
                <input type="tel" id="tel_cliente" name="telefone_cliente" placeholder="WhatsApp do Cliente" maxlength="11" required>
                <button type="submit" class="btn btn-success">Gerar e Enviar QR Code</button>
            </form>
            <hr>
            </div>
        <script>
            // Validação também no campo de emissão
            const inputCli = document.getElementById('tel_cliente');
            if(inputCli) {{
                inputCli.addEventListener('input', e => {{ e.target.value = e.target.value.replace(/\\D/g, ''); }});
            }}
        </script>
    ''', eventos=meus_eventos)
# --- ROTAS RESTANTES (RELATORIO, NOVO_EVENTO, PORTARIA, LOGOUT) ---
@app.route('/novo_evento', methods=['GET', 'POST'])
def novo_evento():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        nome, data, preco = request.form.get('nome'), request.form.get('data_evento'), request.form.get('preco_ingresso')
        res = supabase.table("eventos").insert({"nome": nome, "data_evento": data, "preco_ingresso": preco, "pago": False}).execute()
        ev_id = res.data[0]['id']
        supabase.table("promoter_eventos").insert({"promoter_id": session['promoter_id'], "evento_id": ev_id}).execute()
        return redirect(url_for('painel'))
    return render_template_string(f'{BASE_STYLE}<div class="card"><h3>🆕 Novo Evento</h3><form method="POST"><input type="text" name="nome" placeholder="Nome" required><input type="date" name="data_evento" required><input type="number" step="0.01" name="preco_ingresso" placeholder="Preço" required><button type="submit" class="btn btn-success">Criar</button></form><a href="/painel" class="link-back">Voltar</a></div>')

@app.route('/relatorio')
def relatorio():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    eid = request.args.get('evento_id')
    res_ev = supabase.table("promoter_eventos").select("eventos(id, nome)").eq("promoter_id", session['promoter_id']).execute()
    meus_eventos = []
    vistos = set()
    for item in res_ev.data:
        if item['eventos'] and item['eventos']['id'] not in vistos:
            meus_eventos.append(item['eventos']); vistos.add(item['eventos']['id'])
    vendas = supabase.table("convites").select("*").eq("evento_id", eid).order("created_at", desc=True).execute().data if eid else []
    return render_template_string(f'''{BASE_STYLE}<div class="card"><h3>📊 Relatório</h3><form method="GET"><select name="evento_id" onchange="this.form.submit()"><option value="">Selecionar Evento...</option>{{% for ev in eventos %}}<option value="{{{{ ev.id }}}}" {{"selected" if ev.id|string == eid else ""}}>{{{{ ev.nome }}}}</option>{{% endfor %}}</select></form><table style="width:100%; font-size:13px; margin-top:15px;">{{% for v in vendas %}}<tr style="border-bottom:1px solid #eee;"><td style="padding:10px 0; text-align:left;">{{{{v.nome_cliente}}}}</td><td style="text-align:right;">{{{{'Válido' if v.status else 'Entrou'}}}}</td></tr>{{% endfor %}}</table><a href="/painel" class="link-back">⬅️ Voltar</a></div>''', eventos=meus_eventos, vendas=vendas, eid=eid)

@app.route('/portaria', methods=['GET', 'POST'])
def portaria():
    evento_id = request.args.get('evento_id')
    if not evento_id: return redirect(url_for('painel'))
    res_evento = supabase.table("eventos").select("pago, nome").eq("id", evento_id).single().execute()
    if not res_evento.data['pago']: return f'{BASE_STYLE}<div class="card"><h2>🔒 Bloqueado</h2><a href="/painel" class="btn btn-primary">Voltar</a></div>'
    msg, cor = None, "black"
    if request.method == 'POST':
        token = request.form.get('qrcode_token')
        res = supabase.table("convites").select("*").eq("qrcode", token).eq("evento_id", evento_id).execute()
        if res.data:
            if res.data[0]['status']:
                supabase.table("convites").update({"status": False}).eq("qrcode", token).execute()
                msg, cor = f"✅ LIBERADO: {res.data[0]['nome_cliente']}", "#28a745"
            else: msg, cor = "❌ JÁ UTILIZADO", "#d93025"
        else: msg, cor = "⚠️ NÃO ENCONTRADO", "#f29900"
    return render_template_string(f'''{BASE_STYLE}<div class="card" style="background:#1a1a1a; color:white;"><h3>🛂 Portaria</h3><p>{res_evento.data['nome']}</p>{{% if msg %}}<div style="background:{{{{cor}}}}; padding:20px; border-radius:12px; margin-bottom:20px;">{{{{msg}}}}</div><a href="/portaria?evento_id={evento_id}" class="btn btn-primary">Próximo</a>{{% else %}}<div id="reader"></div><form method="POST" id="form-p"><input type="hidden" name="qrcode_token" id="qct"></form>{{% endif %}}<a href="/painel" class="link-back">Sair</a></div><script src="https://unpkg.com/html5-qrcode"></script><script>function onScan(t){{document.getElementById('qct').value=t; document.getElementById('form-p').submit();}} let scanner = new Html5QrcodeScanner("reader", {{fps:10, qrbox:250}}); scanner.render(onScan);</script>''', msg=msg, cor=cor)

@app.route('/v/<token>')
def visualizar_convite(token):
    res = supabase.table("convites").select("*, eventos(nome)").eq("qrcode", token).execute()
    if not res.data: return "Inválido", 404
    return render_template_string(f'{BASE_STYLE}<div class="card"><h2>TICKET ZAP</h2><p>{res.data[0]["eventos"]["nome"]}</p><img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={token}" style="width:100%;"><p>Cliente: {res.data[0]["nome_cliente"]}</p></div>')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)