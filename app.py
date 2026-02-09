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

# --- CSS BASE PARA TODAS AS TELAS (RESPONSIVO) ---
BASE_STYLE = '''
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    * { box-sizing: border-box; }
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
        background: #f0f2f5; margin: 0; padding: 15px; 
        display: flex; justify-content: center; align-items: flex-start; min-height: 100vh;
    }
    .card { 
        background: white; padding: 25px; border-radius: 16px; 
        box-shadow: 0 8px 24px rgba(0,0,0,0.08); width: 100%; max-width: 450px; 
        text-align: center;
    }
    h2, h3 { color: #1a1a1a; margin-top: 0; }
    input, select { 
        width: 100%; padding: 14px; margin: 8px 0 16px 0; 
        border: 1px solid #ddd; border-radius: 10px; font-size: 16px; outline: none;
    }
    input:focus { border-color: #1a73e8; box-shadow: 0 0 0 3px rgba(26,115,232,0.1); }
    .btn { 
        width: 100%; padding: 16px; border: none; border-radius: 10px; 
        font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.2s;
        display: inline-block; text-align: center; text-decoration: none;
    }
    .btn-primary { background: #1a73e8; color: white; }
    .btn-success { background: #28a745; color: white; }
    .btn-whatsapp { background: #25D366; color: white; font-size: 18px; margin: 15px 0; }
    .btn-secondary { background: #6c757d; color: white; padding: 14px; font-size: 14px; margin-top: 10px; }
    .link-back { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; font-size: 14px; }
    hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; width: 100%; }
    .status-badge { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
    .status-true { background: #e6f4ea; color: #1e7e34; }
    .status-false { background: #fce8e6; color: #d93025; }
</style>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None # Variável para armazenar a mensagem de erro
    
    if request.method == 'POST':
        celular = request.form.get('celular')
        senha = request.form.get('senha')
        
        res = supabase.table("promoter").select("*").eq("telefone", celular).execute()
        
        if res.data:
            user = res.data[0]
            if user['senha'] == senha:
                session['promoter_id'] = user['id']
                session['promoter_nome'] = user['nome']
                return redirect(url_for('index'))
            else:
                erro = "Senha incorreta! Verifique e tente novamente."
        else:
            erro = "Promoter não encontrado em nossa base."
            
    return render_template_string('''
        ''' + BASE_STYLE + '''
        <div class="card">
            <h3 style="margin-bottom:20px;">🔐 Acesso Promoter</h3>
            
            {% if erro %}
                <div style="background: #fce8e6; color: #d93025; padding: 10px; border-radius: 8px; font-size: 13px; margin-bottom: 15px; border: 1px solid #f1b9b2;">
                    ⚠️ {{ erro }}
                </div>
            {% endif %}

            <form method="POST">
                <input type="tel" name="celular" placeholder="Seu Celular" required style="margin-bottom:10px;">
                <input type="password" name="senha" placeholder="Sua Senha" required style="margin-bottom:20px;">
                <button type="submit" class="btn btn-primary" style="width:100%;">Entrar</button>
            </form>
            
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
            
            <p style="font-size:14px; color:#666;">Novo por aqui?</p>
            <a href="/cadastro" class="btn" style="background:#6c757d; color:white; text-decoration:none; display:block; padding:10px; border-radius:8px;">
                ✨ Criar Nova Conta
            </a>
        </div>
    ''', erro=erro)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        try:
            # 1. Verifica se o celular já existe para evitar duplicados
            check = supabase.table("promoter").select("id").eq("telefone", telefone).execute()
            if check.data:
                return "Erro: Este celular já está cadastrado!"

            # 2. Insere o novo promoter
            supabase.table("promoter").insert({
                "nome": nome, 
                "telefone": telefone, 
                "senha": senha,
                "valor_convite": 2.00  # Taxa padrão inicial
            }).execute()
            
            return '''
                <script>
                    alert("Cadastro realizado! Use seu celular e senha para entrar.");
                    window.location.href = "/login";
                </script>
            '''
        except Exception as e:
            return f"Erro ao cadastrar: {e}"

    return render_template_string('''
        ''' + BASE_STYLE + '''
        <div class="card">
            <h3 style="margin-bottom:20px;">📝 Novo Promoter</h3>
            <form method="POST">
                <input type="text" name="nome" placeholder="Nome Completo" required>
                <input type="tel" name="telefone" placeholder="Celular (WhatsApp)" required>
                <input type="password" name="senha" placeholder="Crie uma Senha" required>
                
                <button type="submit" class="btn btn-success" style="width:100%; margin-top:10px;">Criar Minha Conta</button>
            </form>
            <hr>
            <a href="/login" style="font-size:14px; color:#1a73e8; text-decoration:none;">Já tem conta? Faça Login</a>
        </div>
    ''')

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    p_id = session['promoter_id']

    # --- 1. BUSCA DADOS DO PROMOTER (TAXA POR EMISSÃO) ---
    promoter_info = supabase.table("promoter").select("valor_convite").eq("id", p_id).single().execute()
    taxa_unitaria = promoter_info.data.get('valor_convite', 2.00)

    if request.method == 'POST':
        evento_id = request.form.get('evento_id')
        cliente = request.form.get('nome_cliente')
        fone = request.form.get('telefone_cliente')
        try:
            resposta = supabase.table("convites").insert({
                "nome_cliente": cliente, 
                "telefone": fone, 
                "promoter_id": p_id, 
                "evento_id": evento_id
            }).execute()
            token_gerado = resposta.data[0]['qrcode']
            
            base_url = request.host_url.rstrip('/')
            link_visualizacao = f"{base_url}/v/{token_gerado}"
            
            msg_texto = f"✅ *Seu Convite Chegou!*\n\nOlá {cliente}, aqui está seu QR Code para o evento:\n\n{link_visualizacao}\n\n*Apresente este link na portaria.*"
            msg_codificada = urllib.parse.quote(msg_texto)
            
            fone_limpo = "".join(filter(str.isdigit, fone))
            if not fone_limpo.startswith("55"): fone_limpo = "55" + fone_limpo
            link_wa = f"https://api.whatsapp.com/send?phone={fone_limpo}&text={msg_codified}"

            return render_template_string(f'''
                {BASE_STYLE}
                <div class="card">
                    <h2 style="color:#28a745;">✅ Sucesso!</h2>
                    <p>Convite para <strong>{cliente}</strong> gerado.</p>
                    <div style="background:#eee; padding:15px; border-radius:10px; margin:15px 0;">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={token_gerado}" style="width:100%; max-width:200px;">
                    </div>
                    <a href="{link_wa}" target="_blank" class="btn btn-whatsapp">📱 Enviar WhatsApp</a>
                    <a href="/" class="link-back">⬅️ Criar outro convite</a>
                </div>
            ''')
        except Exception as e: return f"Erro: {str(e)}"

    # --- 2. BUSCA EVENTOS (INCLUINDO DATA E PREÇO DO INGRESSO) ---
    # Buscamos os campos id, nome, pago, data_evento e preco_ingresso
    res_eventos = supabase.table("promoter_eventos").select("*, eventos(id, nome, pago, data_evento, preco_ingresso)").eq("promoter_id", p_id).execute()
    
    meus_eventos = []
    for item in res_eventos.data:
        if item['eventos']:
            ev = item['eventos']
            # Conta convites emitidos para calcular sua taxa (total_pagar)
            contagem = supabase.table("convites").select("id", count="exact").eq("evento_id", ev['id']).execute()
            total_convites = contagem.count if contagem.count else 0
            
            ev['total_pagar'] = total_convites * taxa_unitaria
            ev['qtd_emitida'] = total_convites
            meus_eventos.append(ev)

    # --- 3. HTML ---
    html_painel = '''
        ''' + BASE_STYLE + '''
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 15px;">
                <h3 style="margin:0;">Olá, {{ session['promoter_nome'] }}!</h3>
                <a href="/logout" style="color:red; font-size:12px; text-decoration:none;">Sair</a>
            </div>
            
            <a href="/novo_evento" class="btn btn-secondary" style="background:#6c757d; margin-bottom:10px;">➕ Novo Evento</a>
            <a href="/relatorio" style="display:block; margin-bottom:15px; color:#1a73e8; text-decoration:none; font-weight:bold;">📊 Relatório de Vendas</a>
            
            <hr>
            
            <h4 style="text-align:left; margin-bottom:5px;">🎟️ Emitir Convite</h4>
            <form method="POST">
                <select name="evento_id">
                    {% for ev in eventos %}
                        <option value="{{ ev.id }}">{{ ev.nome }}</option>
                    {% endfor %}
                </select>
                <input type="text" name="nome_cliente" placeholder="Nome do Cliente" required>
                <input type="tel" name="telefone_cliente" placeholder="WhatsApp do Cliente" required>
                <button type="submit" class="btn btn-success">Gerar e Enviar QR Code</button>
            </form>

            <hr>

            <h4 style="text-align:left; margin-bottom:10px;">🛂 Suas Portarias</h4>
            {% for ev in eventos %}
            <div style="border: 1px solid #eee; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; border-left: 5px solid {{ '#28a745' if ev.pago else '#d93025' }};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 16px;">{{ ev.nome }}</strong>
                    <span style="font-size: 10px; padding: 3px 8px; border-radius: 20px; background: {{ '#e6f4ea' if ev.pago else '#fce8e6' }}; color: {{ '#1e7e34' if ev.pago else '#d93025' }}; font-weight: bold;">
                        {{ 'LIBERADO' if ev.pago else 'BLOQUEADO' }}
                    </span>
                </div>

                <div style="margin: 8px 0; font-size: 12px; color: #666;">
                    <span>📅 {{ ev.data_evento if ev.data_evento else 'Sem data' }}</span> | 
                    <span>🎫 Ingresso: R$ {{ "%.2f"|format(ev.preco_ingresso|float) if ev.preco_ingresso else '0.00' }}</span>
                </div>

                {% if not ev.pago %}
                    <div style="background: #fff4f2; padding: 8px; border-radius: 8px; margin-top: 8px;">
                        <p style="margin: 0; font-size: 13px; color: #d93025;">
                            Pendência: <strong>R$ {{ "%.2f"|format(ev.total_pagar) }}</strong>
                        </p>
                        <small style="font-size: 10px; color: #666;">Baseado em {{ ev.qtd_emitida }} convites emitidos.</small>
                    </div>
                {% endif %}

               {% if not ev.pago %}
    <div style="background: #fff4f2; padding: 12px; border-radius: 8px; margin-top: 8px; border: 1px dashed #d93025;">
        <p style="margin: 0; font-size: 13px; color: #d93025; font-weight: bold;">
            🔒 Portaria Bloqueada
        </p>
        <p style="margin: 5px 0; font-size: 13px; color: #333;">
            Pendência: <strong>R$ {{ "%.2f"|format(ev.total_pagar) }}</strong>
        </p>
        <div style="background: #fff; padding: 8px; border-radius: 5px; margin-top: 5px; border: 1px solid #ffcfcc;">
            <small style="display:block; color: #666; font-size: 10px; margin-bottom: 2px;">Chave PIX para liberação:</small>
            <strong style="font-size: 12px; color: #1a73e8; letter-spacing: 0.5px;">CNPJ: 12.458.635/0001-16</strong>
        </div>
        <small style="font-size: 10px; color: #d93025; display: block; margin-top: 5px;">
            * Envie o comprovante para o administrador.
        </small>
    </div>
{% endif %}

<a href="/portaria?evento_id={{ ev.id }}" 
   style="display: block; text-align: center; margin-top: 10px; padding: 12px; border-radius: 8px; background: {{ '#1a73e8' if ev.pago else '#f1f1f1' }}; color: {{ 'white' if ev.pago else '#999' }}; text-decoration: none; font-size: 14px; font-weight: bold; pointer-events: {{ 'auto' if ev.pago else 'none' }};">
   {{ '🛂 Abrir Portaria' if ev.pago else '🔒 Pagamento Pendente' }}
</a>
            </div>
            {% endfor %}
        </div>
    '''
    return render_template_string(html_painel, eventos=meus_eventos)

# --- AS DEMAIS ROTAS (RELATORIO, PORTARIA, ETC) CONTINUAM IGUAIS ---
@app.route('/novo_evento', methods=['GET', 'POST'])
def novo_evento():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        data = request.form.get('data_evento')
        preco = request.form.get('preco_ingresso')
        p_id = session['promoter_id']
        
        try:
            # 1. Cria o evento com os novos campos
            res = supabase.table("eventos").insert({
                "nome": nome, 
                "data_evento": data, 
                "preco_ingresso": preco,
                "pago": False  # Já nasce bloqueado
            }).execute()
            
            ev_id = res.data[0]['id']
            
            # 2. Vincula o promoter ao evento
            supabase.table("promoter_eventos").insert({
                "promoter_id": p_id, 
                "evento_id": ev_id
            }).execute()
            
            return redirect(url_for('index'))
        except Exception as e:
            return f"Erro ao criar evento: {e}"

    return render_template_string('''
        ''' + BASE_STYLE + '''
        <div class="card">
            <h3>🆕 Novo Evento</h3>
            <form method="POST">
                <input type="text" name="nome" placeholder="Nome do Evento" required>
                
                <label style="display:block; text-align:left; font-size:12px; color:#666;">Data do Evento:</label>
                <input type="date" name="data_evento" required>
                
                <label style="display:block; text-align:left; font-size:12px; color:#666;">Preço do Ingresso (R$):</label>
                <input type="number" step="0.01" name="preco_ingresso" placeholder="Ex: 50.00" required>
                
                <button type="submit" class="btn btn-success">Criar Evento</button>
            </form>
            <a href="/" class="link-back">Voltar</a>
        </div>
    ''')

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
    vendas = []
    if eid: vendas = supabase.table("convites").select("*").eq("evento_id", eid).order("created_at", desc=True).execute().data
    return render_template_string(f'''{BASE_STYLE}<div class="card"><h3>📊 Relatório</h3><form method="GET"><select name="evento_id" onchange="this.form.submit()"><option value="">Selecionar Evento...</option>{{% for ev in eventos %}}<option value="{{{{ ev.id }}}}" {{"selected" if ev.id|string == eid else ""}}>{{{{ ev.nome }}}}</option>{{% endfor %}}</select></form>{{% if vendas %}}<p>Total: {{{{ vendas|length }}}}</p><table style="width:100%; font-size:14px;">{{% for v in vendas %}}<tr style="border-bottom:1px solid #eee;"><td style="padding:10px 0; text-align:left;">{{{{v.nome_cliente}}}}</td><td style="text-align:right;"><span class="status-badge status-{{{{v.status|lower}}}}">{{{{'Válido' if v.status else 'Entrou'}}}}</span></td></tr>{{% endfor %}}</table>{{% endif %}}<a href="/" class="link-back">⬅️ Voltar</a></div>''', eventos=meus_eventos, vendas=vendas, eid=eid)

@app.route('/v/<token>')
def visualizar_convite(token):
    res = supabase.table("convites").select("*, eventos(nome)").eq("qrcode", token).execute()
    if not res.data: return "Convite Inválido", 404
    convite = res.data[0]
    return render_template_string(f'{BASE_STYLE}<div class="card" style="border-top: 8px solid #28a745;"><h2>TICKET FLOW</h2><p>{convite["eventos"]["nome"]}</p><img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={token}" style="width:100%; max-width:250px;"><p>Cliente: <strong>{convite["nome_cliente"]}</strong></p></div>')

@app.route('/portaria', methods=['GET', 'POST'])
def portaria():
    # 1. Pegamos o evento_id da URL (ex: /portaria?evento_id=123)
    evento_id = request.args.get('evento_id')
    
    # Se não selecionou evento, redirecionamos para o painel
    if not evento_id:
        return redirect(url_for('index'))

    # 2. VERIFICAÇÃO FINANCEIRA: O evento está pago?
    res_evento = supabase.table("eventos").select("pago, nome").eq("id", evento_id).single().execute()
    
    if res_evento.data and not res_evento.data['pago']:
        return f'''
        {BASE_STYLE}
        <div class="card" style="text-align:center; border-top: 10px solid #d93025;">
            <h2 style="color:#d93025;">🔒 Portaria Bloqueada</h2>
            <p>O evento <strong>{res_evento.data['nome']}</strong> possui pendências de liberação.</p>
            <p style="font-size:14px; color:#666;">Por favor, realize o pagamento da taxa para ativar o scanner.</p>
            <hr>
            <a href="/" class="btn btn-primary">Voltar ao Painel</a>
        </div>
        '''

    # --- Se chegou aqui, o evento está PAGO. Segue o baile! ---
    msg, cor = None, "black"
    if request.method == 'POST':
        token = request.form.get('qrcode_token')
        # Buscamos o convite e garantimos que ele pertence a este evento
        res = supabase.table("convites").select("*, eventos(nome)").eq("qrcode", token).eq("evento_id", evento_id).execute()
        
        if res.data:
            convite = res.data[0]
            if convite['status']:
                supabase.table("convites").update({"status": False}).eq("qrcode", token).execute()
                msg, cor = f"✅ LIBERADO: {convite['nome_cliente']}", "#28a745"
            else: 
                msg, cor = "❌ JÁ UTILIZADO", "#d93025"
        else: 
            msg, cor = "⚠️ NÃO ENCONTRADO", "#f29900"

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="background:#1a1a1a; color:white; text-align:center;">
            <h3 style="color:white; margin-bottom:5px;">🛂 Portaria</h3>
            <p style="color:#888; font-size:12px; margin-bottom:20px;">Evento: {res_evento.data['nome']}</p>
            
            {{% if msg %}}
                <div style="background:{{{{cor}}}}; padding:20px; border-radius:12px; margin-bottom:20px; font-weight:bold; font-size:18px;">
                    {{{{msg}}}}
                </div>
                <a href="/portaria?evento_id={evento_id}" class="btn btn-primary">Próximo Cliente</a>
            {{% else %}}
                <div id="reader" style="width:100%; border-radius:12px; overflow:hidden;"></div>
                <form method="POST" id="form-p">
                    <input type="hidden" name="qrcode_token" id="qct">
                </form>
                <p style="font-size:14px; color:#888; margin-top:15px;">Aponte para o QR Code</p>
            {{% endif %}}
            <a href="/" class="link-back" style="color:#888; margin-top:20px;">Sair da Portaria</a>
        </div>
        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
            function onScan(t) {{ 
                document.getElementById('qct').value = t; 
                document.getElementById('form-p').submit(); 
            }}
            let scanner = new Html5QrcodeScanner("reader", {{ fps: 10, qrbox: 250 }});
            scanner.render(onScan);
        </script>
    ''', msg=msg, cor=cor)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)