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
    if request.method == 'POST':
        tel = request.form.get('telefone')
        res = supabase.table("promoter").select("*").eq("telefone", tel).eq("ativo", True).execute()
        if res.data:
            session['promoter_id'] = res.data[0]['id']
            session['promoter_nome'] = res.data[0]['nome']
            return redirect(url_for('index'))
        return f"{BASE_STYLE}<div class='card'><h3>❌ Acesso Negado</h3><p>Usuário não encontrado ou inativo.</p><a href='/login' class='btn btn-primary'>Tentar Novamente</a></div>"
    
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="align-self:center;">
            <h2 style="color:#1a73e8;">TicketsZap</h2>
            <p style="color:#666;">Acesse seu painel de promoter</p>
            <form method="POST">
                <input type="tel" name="telefone" placeholder="Seu Telefone (Ex: 5511...)" required>
                <button type="submit" class="btn btn-primary">Entrar no Sistema</button>
            </form>
            <hr>
            <p style="font-size:14px; margin-bottom: 10px;">Ainda não é cadastrado?</p>
            <a href="/cadastro" class="btn btn-secondary">Quero ser Promoter</a>
        </div>
    ''')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        tel = request.form.get('telefone')
        try:
            supabase.table("promoter").insert({"nome": nome, "telefone": tel, "ativo": False}).execute()
            return f"{BASE_STYLE}<div class='card' style='align-self:center;'><h3>🚀 Solicitação Enviada!</h3><p>Aguarde a ativação pelo administrador.</p><a href='/login' class='btn btn-primary'>Voltar ao Login</a></div>"
        except Exception as e:
            return f"Erro ao solicitar cadastro: {str(e)}"

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="align-self:center;">
            <h3>Cadastrar como Promoter</h3>
            <p style="font-size:14px; color:#666;">Preencha seus dados para solicitar acesso.</p>
            <form method="POST">
                <input type="text" name="nome" placeholder="Seu Nome Completo" required>
                <input type="tel" name="telefone" placeholder="Seu WhatsApp (Ex: 5511...)" required>
                <button type="submit" class="btn btn-primary">Solicitar Acesso</button>
            </form>
            <a href="/login" class="link-back">Já tenho cadastro</a>
        </div>
    ''')

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    p_id = session['promoter_id']

    if request.method == 'POST':
        evento_id = request.form.get('evento_id')
        cliente = request.form.get('nome_cliente')
        fone = request.form.get('telefone_cliente')
        try:
            resposta = supabase.table("convites").insert({"nome_cliente": cliente, "telefone": fone, "promoter_id": p_id, "evento_id": evento_id}).execute()
            token_gerado = resposta.data[0]['qrcode']
            
            base_url = request.host_url.rstrip('/')
            link_visualizacao = f"{base_url}/v/{token_gerado}"
            
            # MENSAGEM MELHORADA COM QUEBRAS DE LINHA PARA O LINK FICAR CLICÁVEL
            msg_texto = f"✅ *Seu Convite Chegou!*\n\nOlá {cliente}, aqui está seu QR Code para o evento:\n\n{link_visualizacao}\n\n*Apresente este link na portaria.*"
            msg_codificada = urllib.parse.quote(msg_texto)
            
            fone_limpo = "".join(filter(str.isdigit, fone))
            if not fone_limpo.startswith("55"): fone_limpo = "55" + fone_limpo
            link_wa = f"https://api.whatsapp.com/send?phone={fone_limpo}&text={msg_codificada}"

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

    res_eventos = supabase.table("promoter_eventos").select("*, eventos(id, nome)").eq("promoter_id", p_id).execute()
    meus_eventos = [item['eventos'] for item in res_eventos.data if item['eventos']]

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 15px;">
                <h3 style="margin:0;">Olá, {session['promoter_nome']}!</h3>
                <a href="/logout" style="color:red; font-size:12px; text-decoration:none;">Sair</a>
            </div>
            <a href="/novo_evento" class="btn btn-secondary" style="background:#6c757d; margin-bottom:10px;">➕ Novo Evento</a>
            <a href="/relatorio" style="display:block; margin-bottom:15px; color:#1a73e8; text-decoration:none; font-weight:bold;">📊 Relatório de Vendas</a>
            <hr>
            <form method="POST">
                <label style="display:block; text-align:left; font-size:14px; color:#666;">Selecione o Evento:</label>
                <select name="evento_id">
                    {{% for ev in eventos %}}<option value="{{{{ ev.id }}}}">{{{{ ev.nome }}}}</option>{{% endfor %}}
                </select>
                <input type="text" name="nome_cliente" placeholder="Nome do Cliente" required>
                <input type="tel" name="telefone_cliente" placeholder="WhatsApp do Cliente" required>
                <button type="submit" class="btn btn-success">Gerar e Enviar QR Code</button>
            </form>
            <a href="/portaria" class="link-back" style="margin-top:25px; color:#1a73e8; border:1px solid #1a73e8; padding:12px; border-radius:10px;">🛂 Abrir Portaria</a>
        </div>
    ''', eventos=meus_eventos)

# --- AS DEMAIS ROTAS (RELATORIO, PORTARIA, ETC) CONTINUAM IGUAIS ---
@app.route('/novo_evento', methods=['GET', 'POST'])
def novo_evento():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        nome_ev = request.form.get('nome_evento')
        p_id = session['promoter_id']
        try:
            res_evento = supabase.table("eventos").insert({"nome": nome_ev}).execute()
            supabase.table("promoter_eventos").insert({"promoter_id": p_id, "evento_id": res_evento.data[0]['id']}).execute()
            return redirect(url_for('index'))
        except Exception as e: return f"Erro: {str(e)}"
    return render_template_string(f'{BASE_STYLE}<div class="card"><h3>🆕 Novo Evento</h3><form method="POST"><input type="text" name="nome_evento" placeholder="Nome do Evento" required><button type="submit" class="btn btn-primary">Cadastrar Evento</button></form><a href="/" class="link-back">⬅️ Voltar</a></div>')

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
    msg, cor = None, "black"
    if request.method == 'POST':
        token = request.form.get('qrcode_token')
        res = supabase.table("convites").select("*, eventos(nome)").eq("qrcode", token).execute()
        if res.data:
            convite = res.data[0]
            if convite['status']:
                supabase.table("convites").update({"status": False}).eq("qrcode", token).execute()
                msg, cor = f"✅ LIBERADO: {convite['nome_cliente']}", "#28a745"
            else: msg, cor = "❌ JÁ UTILIZADO", "#d93025"
        else: msg, cor = "⚠️ NÃO ENCONTRADO", "#f29900"
    return render_template_string(f'''{BASE_STYLE}<div class="card" style="background:#1a1a1a; color:white;"><h3>🛂 Portaria</h3>{{% if msg %}}<div style="background:{{{{cor}}}}; padding:20px; border-radius:12px; margin-bottom:20px; font-weight:bold;">{{{{msg}}}}</div><a href="/portaria" class="btn btn-primary">Próximo</a>{{% else %}}<div id="reader"></div><form method="POST" id="form-p"><input type="hidden" name="qrcode_token" id="qct"></form>{{% endif %}}<a href="/" class="link-back" style="color:#888;">Sair</a></div><script src="https://unpkg.com/html5-qrcode"></script><script>function onScan(t) {{ document.getElementById('qct').value = t; document.getElementById('form-p').submit(); }} let scanner = new Html5QrcodeScanner("reader", {{ fps: 10, qrbox: 250 }}); scanner.render(onScan);</script>''', msg=msg, cor=cor)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)