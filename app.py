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
    .btn-secondary { background: #6c757d; color: white; padding: 10px; font-size: 14px; }
    .link-back { display: block; text-align: center; margin-top: 15px; color: #666; text-decoration: none; font-size: 14px; }
    hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
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
        return f"{BASE_STYLE}<div class='card'><h3>❌ Acesso Negado</h3><a href='/login' class='btn btn-primary'>Tentar Novamente</a></div>"
    
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="text-align:center; align-self:center;">
            <h2 style="color:#1a73e8;">TicketsZap</h2>
            <p style="color:#666;">Acesse seu painel de promoter</p>
            <form method="POST">
                <input type="tel" name="telefone" placeholder="Seu Telefone (DDD + Número)" required>
                <button type="submit" class="btn btn-primary">Entrar no Sistema</button>
            </form>
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
            msg = urllib.parse.quote(f"Olá {cliente}! Aqui está seu convite: {link_visualizacao}")
            fone_limpo = "".join(filter(str.isdigit, fone))
            if not fone_limpo.startswith("55"): fone_limpo = "55" + fone_limpo
            link_wa = f"https://api.whatsapp.com/send?phone={fone_limpo}&text={msg}"

            return render_template_string(f'''
                {BASE_STYLE}
                <div class="card" style="text-align:center;">
                    <h2 style="color:#28a745;">✅ Sucesso!</h2>
                    <p>Convite para <strong>{cliente}</strong> gerado.</p>
                    <div style="background:#eee; padding:15px; border-radius:10px; margin:15px 0;">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={token_gerado}" style="width:100%; max-width:200px;">
                    </div>
                    <a href="{link_wa}" class="btn btn-whatsapp">📱 Enviar WhatsApp</a>
                    <a href="/" class="link-back">⬅️ Criar outro convite</a>
                </div>
            ''')
        except Exception as e: return f"Erro: {str(e)}"

    res_eventos = supabase.table("promoter_eventos").select("*, eventos(id, nome)").eq("promoter_id", p_id).execute()
    meus_eventos = [item['eventos'] for item in res_eventos.data if item['eventos']]

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3>Olá, {session['promoter_nome']}!</h3>
                <a href="/logout" style="color:red; font-size:12px;">Sair</a>
            </div>
            <a href="/novo_evento" class="btn btn-secondary" style="margin-bottom:15px;">➕ Novo Evento</a>
            <a href="/relatorio" style="display:block; margin-bottom:15px; color:#1a73e8; text-decoration:none; font-weight:bold;">📊 Relatório de Vendas</a>
            <hr>
            <form method="POST">
                <label>Evento:</label>
                <select name="evento_id">
                    {{% for ev in eventos %}}<option value="{{{{ ev.id }}}}">{{{{ ev.nome }}}}</option>{{% endfor %}}
                </select>
                <input type="text" name="nome_cliente" placeholder="Nome do Cliente" required>
                <input type="tel" name="telefone_cliente" placeholder="WhatsApp do Cliente" required>
                <button type="submit" class="btn btn-success">Gerar e Enviar QR Code</button>
            </form>
            <a href="/portaria" class="link-back" style="margin-top:25px; color:#1a73e8; border:1px solid #1a73e8; padding:10px; border-radius:8px;">🛂 Abrir Portaria</a>
        </div>
    ''', eventos=meus_eventos)

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

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <h3>🆕 Novo Evento</h3>
            <form method="POST">
                <input type="text" name="nome_evento" placeholder="Nome do Evento (Ex: Festa VIP)" required>
                <button type="submit" class="btn btn-primary">Cadastrar Evento</button>
            </form>
            <a href="/" class="link-back">⬅️ Voltar</a>
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
    if eid:
        vendas = supabase.table("convites").select("*").eq("evento_id", eid).order("created_at", desc=True).execute().data

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="max-width:600px;">
            <h3>📊 Relatório</h3>
            <form method="GET">
                <select name="evento_id" onchange="this.form.submit()">
                    <option value="">Selecione o Evento...</option>
                    {{% for ev in eventos %}}
                        <option value="{{{{ ev.id }}}}" {{"selected" if ev.id|string == eid else ""}}>{{{{ ev.nome }}}}</option>
                    {{% endfor %}}
                </select>
            </form>
            {{% if vendas %}}
                <p>Total: <strong>{{{{ vendas|length }}}} vendidos</strong></p>
                <div style="overflow-x:auto;">
                    <table style="width:100%; border-collapse:collapse; font-size:14px;">
                        {{% for v in vendas %}}
                        <tr style="border-bottom:1px solid #eee;">
                            <td style="padding:10px 0;">{{{{ v.nome_cliente }}}}<br><small style="color:#888;">{{{{ v.telefone }}}}</small></td>
                            <td style="text-align:right;">
                                <span class="status-badge status-{{{{ v.status|lower }}}}">
                                    {{{{ 'Válido' if v.status else 'Entrou' }}}}
                                </span>
                            </td>
                        </tr>
                        {{% endfor %}}
                    </table>
                </div>
            {{% endif %}}
            <a href="/" class="link-back">⬅️ Voltar</a>
        </div>
    ''', eventos=meus_eventos, vendas=vendas, eid=eid)

@app.route('/v/<token>')
def visualizar_convite(token):
    res = supabase.table("convites").select("*, eventos(nome)").eq("qrcode", token).execute()
    if not res.data: return "Convite Inválido", 404
    convite = res.data[0]
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="text-align:center; border-top: 8px solid #28a745;">
            <h2 style="margin-bottom:5px;">TICKET FLOW</h2>
            <p style="color:#666; margin-bottom:20px;">{convite['eventos']['nome']}</p>
            <div style="background:#f9f9f9; padding:20px; border-radius:12px;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={token}" style="width:100%;">
            </div>
            <p style="margin-top:20px;">Cliente: <strong>{convite['nome_cliente']}</strong></p>
            <p style="font-size:12px; color:#d93025; background:#fff1f0; padding:10px; border-radius:6px;">Apresente este QR Code na entrada do evento.</p>
        </div>
    ''')

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

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="background:#1a1a1a; color:white; text-align:center;">
            <h3 style="color:white;">🛂 Portaria</h3>
            {{% if msg %}}
                <div style="background:{{{{cor}}}}; padding:20px; border-radius:12px; margin-bottom:20px; font-size:20px; font-weight:bold;">{{{{msg}}}}</div>
                <a href="/portaria" class="btn btn-primary">Próximo Cliente</a>
            {{% else %}}
                <div id="reader" style="width:100%; border-radius:12px; overflow:hidden; margin-bottom:20px;"></div>
                <form method="POST" id="form-p"><input type="hidden" name="qrcode_token" id="qct"></form>
                <p style="font-size:14px; color:#888;">Aponte a câmera para o QR Code</p>
            {{% endif %}}
            <a href="/" class="link-back" style="color:#888;">Sair da Portaria</a>
        </div>
        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
            function onScan(t) {{ document.getElementById('qct').value = t; document.getElementById('form-p').submit(); }}
            let scanner = new Html5QrcodeScanner("reader", {{ fps: 10, qrbox: 250 }});
            scanner.render(onScan);
        </script>
    ''', msg=msg, cor=cor)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
   # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True) #permite aceitar conexao de qq lugar.