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
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>TicketsZap | Promoter</title>
    
    <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/128/3270/3270184.png">
    <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/128/3270/3270184.png">
    
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#1a73e8">

    <style>
    * { box-sizing: border-box; }
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
        background: #f0f2f5; margin: 0; padding: 15px; 
        display: flex; flex-direction: column; align-items: center; min-height: 100vh;
    }
    
    .card { 
        background: white; padding: 25px; border-radius: 16px; 
        box-shadow: 0 8px 24px rgba(0,0,0,0.08); width: 100%; max-width: 450px; 
        text-align: center; margin-bottom: 20px;
    }

    /* CORREÇÃO: Input e Select ocupando a largura toda */
    input, select { 
        width: 100% !important; 
        display: block;
        padding: 14px; margin: 8px 0 16px 0; 
        border: 1px solid #ddd; border-radius: 10px; font-size: 16px; 
        background-color: white; /* Garante fundo branco no dropdown */
    }

    /* Botão base */
    .btn { 
        width: 100% !important; 
        display: block;
        padding: 16px; border: none; border-radius: 10px; 
        font-size: 16px; font-weight: bold; cursor: pointer;
        text-decoration: none; text-align: center;
        margin-top: 10px;
    }

    /* Cores específicas dos botões */
    .btn-primary { background: #1a73e8 !important; color: white !important; }
    .btn-success { background: #28a745 !important; color: white !important; } /* O VERDE AQUI */
    .btn-secondary { background: #6c757d !important; color: white !important; }

    /* Estilo dos Grupos Informativos */
    .info-container { width: 100%; max-width: 450px; }
    .info-group {
        background: #d5eaec; padding: 18px; border-radius: 16px; 
        margin-bottom: 12px; display: flex; align-items: center; 
        gap: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); text-align: left;
    }
    .info-icon { font-size: 28px; }
    .info-title { font-weight: bold; color: #1a1a1a; display: block; margin-bottom: 2px; }
    .info-desc { font-size: 13px; color: #010101; line-height: 1.4; }

    .step-item {
        display: flex;
        align-items: flex-start;
        gap: 15px;
        margin-bottom: 20px;
        padding-left: 10px;
        position: relative;
    }

    .step-number {
        background: #1a73e8;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
        flex-shrink: 0;
    }

    .pricing-badge {
        background: #e6f4ea;
        color: #1e7e34;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        font-size: 14px;
        margin-top: 20px;
        border: 1px dashed #28a745;
    }
</style>
</head>
'''
HOW_IT_WORKS_HTML = '''
<div class="info-container">
    <h4 style="text-align: center; color: #666; margin: 20px 0 10px 0;">🚀 Comece em 4 passos:</h4>
    
    <div class="step-item">
        <span class="step-number">1</span>
        <div><span class="info-title">Cadastro Rápido</span><span class="info-desc">Crie sua conta de promoter em segundos.</span></div>
    </div>

    <div class="step-item">
        <span class="step-number">2</span>
        <div><span class="info-title">Configure seu Evento</span><span class="info-desc">Cadastre os detalhes da sua festa ou evento.</span></div>
    </div>

    <div class="step-item">
        <span class="step-number">3</span>
        <div><span class="info-title">Venda e Envie</span><span class="info-desc">Gere o QR Code e envie direto para o WhatsApp do cliente.</span></div>
    </div>

    <div class="step-item">
        <span class="step-number">4</span>
        <div><span class="info-title">Valide na Portaria</span><span class="info-desc">Use nosso app para ler o QR Code e liberar a entrada.</span></div>
    </div>

    <div class="pricing-badge" style="text-align: left; background: #f8f9fa; border: 1px solid #ddd; color: #333;">
        <div style="font-size: 18px; margin-bottom: 8px;">💰 <strong>Como funciona o pagamento:</strong></div>
        <div style="font-size: 14px; line-height: 1.5;">
            Você adquire um pacote inicial de <strong>250 créditos por R$ 250,00</strong> para ativar seu evento. <br><br>
            Cada convite enviado consome 1 crédito. Se precisar de mais, basta recarregar por apenas <strong>R$ 1,00 por convite adicional!</strong>
        </div>
    </div>
</div>
'''
# --- GRUPOS INFORMATIVOS REUTILIZÁVEIS ---
INFO_GROUPS_HTML = '''
<div class="info-container">
    <div class="info-group">
        <span class="info-icon">📱</span>
        <div>
            <span class="info-title">Portaria na Mão</span>
            <span class="info-desc">Valide ingressos usando a câmera do seu celular, sem precisar de cabos.</span>
        </div>
    </div>
    <div class="info-group">
        <span class="info-icon">💬</span>
        <div>
            <span class="info-title">Envio via WhatsApp</span>
            <span class="info-desc">O cliente recebe o QR Code e o link do convite direto no celular dele.</span>
        </div>
    </div>
    <div class="info-group">
        <span class="info-icon">🚀</span>
        <div>
            <span class="info-title">QR Code Seguro</span>
            <span class="info-desc">Cada convite gera um código único que impede fraudes nos seus eventos.</span>
        </div>
    </div>
</div>
'''
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
                return redirect(url_for('index'))
            else:
                erro = "Senha incorreta! Verifique e tente novamente."
        else:
            erro = "Promoter não encontrado em nossa base."
            
    # O SEGREDO ESTÁ AQUI: Somamos a BASE_STYLE no início e a INFO_GROUPS_HTML no fim
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
        ''' + INFO_GROUPS_HTML + '''
        ''' + HOW_IT_WORKS_HTML + '''
    ''', erro=erro)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # 1. Configurações Iniciais
    termos_texto = "" 
    erro_msg = None  
    
    # Busca os termos no banco
    try:
        res = supabase.table("configuracoes_plataforma").select("conteudo").eq("chave", "termos_uso").single().execute()
        termos_texto = res.data['conteudo'] if res.data else "Termos não configurados."
    except Exception as e:
        print(f"Erro ao buscar termos: {e}")
        termos_texto = "Erro ao carregar os termos."

    # 2. Lógica de Recebimento do Formulário
    if request.method == 'POST':
        nome = request.form.get('nome')
        cidade = request.form.get('cidade_promoter')      
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        try:
            # Verifica se o celular já existe
            check = supabase.table("promoter").select("id").eq("telefone", telefone).execute()
            
            if check.data:
                # SE JÁ EXISTE: Define a mensagem e NÃO insere no banco
                erro_msg = "Este celular já está cadastrado!"
            else:
                # SE NÃO EXISTE: Insere o novo promoter
                supabase.table("promoter").insert({
                    "nome": nome, 
                    "cidade": cidade,
                    "telefone": telefone, 
                    "senha": senha,
                    "valor_convite": 2.00
                }).execute()
                
                return '''
                    <script>
                        alert("Cadastro realizado! Use seu celular e senha para entrar.");
                        window.location.href = "/login";
                    </script>
                '''
        except Exception as e:
            erro_msg = f"Erro no banco de dados: {e}"

    # 3. Renderização da Página (Tanto GET quanto POST com erro caem aqui)
    return render_template_string('''
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ''' + BASE_STYLE + '''
        <style>
            .card {
                width: 90% !important;
                max-width: 400px !important;
                margin: 20px auto !important;
                text-align: left !important;
                display: block !important;
            }
            .campo-cidade { -webkit-appearance: listbox !important; appearance: auto !important; }
            .modal-inner {
                background: #fff; padding: 20px; border-radius: 12px;
                width: 90%; max-width: 450px; max-height: 80vh; overflow-y: auto; box-sizing: border-box;
            }
        </style>

        <div class="card">
            {% if erro %}
            <div style="background: #fee2e2; color: #b91c1c; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; border: 1px solid #fecaca; text-align: center; font-family: sans-serif;">
                ⚠️ <strong>Erro:</strong> {{ erro }}
            </div>
            {% endif %}

            <h3 style="margin-bottom:20px; text-align: center;">📝 Novo Promoter</h3>
            <form method="POST" style="width: 100%;">
                
                <input type="text" name="nome" placeholder="Nome Completo" required style="width:100%; padding:12px; margin-bottom:15px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box;">

                <div style="margin-bottom:15px;">
                    <label style="font-size: 13px; color: #666; font-weight: bold;">📍 Cidade de Atuação</label>
                    <input type="text" list="cidades_list" id="cidade_input" name="cidade_promoter" placeholder="Selecione na lista..." required 
                           style="width:100%; padding:12px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box;" class="campo-cidade">
                    <datalist id="cidades_list">
                        <option value="Araraquara - SP">
                        <option value="Américo Brasiliense - SP">
                        <option value="Matão - SP">
                        <option value="Santa Lúcia - SP">
                        <option value="Rincão - SP">
                        <option value="Motuca - SP">
                        <option value="São Carlos - SP">
                        <option value="Ibaté - SP">
                        <option value="Descalvado - SP">
                        <option value="Ribeirão Preto - SP">
                        <option value="São Paulo - SP">
                    </datalist>
                </div>
                
                <input type="tel" id="tel_cadastro" name="telefone" placeholder="WhatsApp (DDD+Número)" maxlength="11" required 
                       style="width:100%; padding:12px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box;">
                
                <input type="password" name="senha" placeholder="Crie uma Senha" required 
                       style="width:100%; padding:12px; margin: 15px 0; border:1px solid #ccc; border-radius:8px; box-sizing:border-box;">
                
                <div style="width: 100%; display: table; margin: 10px 0 20px 0;">
                    <div style="display: table-cell; width: 30px; vertical-align: middle;">
                        <input type="checkbox" id="aceite" name="aceite" required style="width: 20px; height: 20px; cursor: pointer;">
                    </div>
                    <div style="display: table-cell; vertical-align: middle;">
                        <label for="aceite" style="font-size: 14px; color: #444; cursor: pointer;">
                            Eu li e aceito os <a href="javascript:void(0)" onclick="abrirModal()" style="color: #25D366; font-weight: bold; text-decoration: underline;">Termos de Uso</a>
                        </label>
                    </div>
                </div>

                <button type="submit" style="width:100%; padding:15px; background:#25D366; color:white; border:none; border-radius:8px; font-weight:bold; font-size:16px; cursor:pointer;">
                    CRIAR MINHA CONTA
                </button>
            </form>
            
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
            <div style="text-align: center;">
                <a href="/login" style="font-size:14px; color:#1a73e8; text-decoration:none; font-family: sans-serif;">
                    Já tem conta? <strong>Faça Login</strong>
                </a>
            </div>
        </div>

        <div id="modalTermos" style="display:none; position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:9999; justify-content:center; align-items:center; padding: 20px; box-sizing: border-box;">
            <div class="modal-inner">
                <h3 style="margin-top:0;">📋 Políticas</h3>
                <div style="white-space: pre-wrap; font-size: 14px; line-height: 1.6; color: #444; margin: 15px 0;">
                    {{ termos }}
                </div>
                <button type="button" onclick="document.getElementById('modalTermos').style.display='none'" style="width:100%; padding:15px; background:#25D366; color:white; border:none; border-radius:8px; font-weight:bold;">FECHAR</button>
            </div>
        </div>

        <script>
            function abrirModal() { document.getElementById('modalTermos').style.display = 'flex'; }
            document.getElementById('tel_cadastro').addEventListener('input', function (e) {
                e.target.value = e.target.value.replace(/\D/g, '');
            });
            document.getElementById('cidade_input').addEventListener('click', function() {
                this.value = '';
            });
        </script>
    ''', termos=termos_texto, erro=erro_msg)
@app.route('/')
def index():
    # Se já estiver logado, pula a propaganda e vai pro trabalho
    if 'promoter_id' in session:
        return redirect(url_for('painel'))
    
    # Se não, mostra a vitrine bonitona que montamos
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TicketsZap | Sua Bilheteria no WhatsApp</title>
                               
             <link rel="icon" type="image/png" href="https://cdn-icons-png.flaticon.com/128/3270/3270184.png/external-flat-juicy-fish/60/external-tickets-ecommerce-flat-juicy-fish.png">                                           


            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
            <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/128/3270/3270184.png/external-flat-juicy-fish/60/external-tickets-ecommerce-flat-juicy-fish.png">


             ''' + BASE_STYLE + '''
            <style>
                body { background: #0a0a0a; color: #fff; font-family: sans-serif; margin: 0; }
                .container { max-width: 800px; margin: auto; padding: 40px 20px; text-align: center; }
                .blue { color: #007bff; } .green { color: #2ecc71; }
                .headline { font-size: 2.5rem; font-weight: 800; margin-bottom: 40px; line-height: 1.2; }
                .benefits-list { list-style: none; padding: 0; margin: 0 auto 50px auto; max-width:450px; text-align: left; }
                .benefits-list li { font-size: 1.3rem; margin-bottom: 25px; display: flex; align-items: center; }
                .button-group { display: flex; flex-direction: column; align-items: center; gap: 20px; }
                .btn-cta { background: #2ecc71; color: #000; padding: 20px 45px; border-radius: 50px; text-decoration: none; font-weight: 800; width: 100%; max-width: 350px; }
                .btn-login { background: #007bff; color: #fff; padding: 15px 45px; border-radius: 50px; text-decoration: none; font-weight: 700; width: 100%; max-width: 350px; }
                footer { margin-top: 80px; padding: 40px 20px; border-top: 1px solid #1a1a1a; }
            </style>
        </head>
        <body>
            <div class="container">
                <div style="font-weight:800; font-size:2.5rem; margin-bottom:40px;"><span class="blue">Tickets</span><span class="green">Zap</span></div>
                <div class="headline">Venda ingressos pelo WhatsApp de forma <span class="green">profissional.</span></div>
                <ul class="benefits-list">
                    <li>✅ Venda convites online em poucos minutos</li>
                    <li>✅ Controle total de acesso ao evento</li>
                    <li>✅ QR Code único para evitar fraudes</li>
                    <li>✅ Leitura rápida pelo celular na Portaria</li>
                    <li>✅ Pague apenas pelo que usar</li>
                    <li style="color: #FFD700;"><span class="check">🎁</span> <strong>BÔNUS: 50 convites grátis no 1º evento</strong></li>
                </ul>
               <div class="button-group">
                    <a href="https://wa.me/5516996042731?text=Ol%C3%A1!%20Quero%20usar%20o%20TicketsZap%20no%20meu%20evento.%0APode%20me%20explicar%20como%20funciona%3F" 
                    class="btn-cta">
                    SAIBA MAIS, FALE COM UM ATENDENTE
                    </a>

                    <a href="/login" class="btn-login">CRIAR MINHA CONTA</a>
                </div>

                <footer>
                    <div style="margin-bottom:10px; font-weight:800;"><span class="blue">TICKETS</span><span class="green">ZAP</span></div>
                    <a href="https://ticketszap.com.br" style="color:#007bff; text-decoration:none;">👉 TICKETSZAP.COM.BR</a>
                </footer>
            </div>
        </body>
        </html>
    ''')

#@app.route('/', methods=['GET', 'POST'])
#def index():
@app.route('/painel', methods=['GET', 'POST'])
def painel():
    if 'promoter_id' not in session: return redirect(url_for('login'))
    p_id = session['promoter_id']

    # Captura se o modo vendedor está ativo via URL (?modo=vendedor)
    modo_vendedor = request.args.get('modo') == 'vendedor'

    # --- 1. BUSCA DADOS DO PROMOTER COM PROTEÇÃO ---
    promoter_info = supabase.table("promoter").select("valor_convite").eq("id", p_id).execute()
    
    # Proteção contra o erro KeyError: 0
    if not promoter_info.data:
        session.clear()
        return redirect(url_for('login'))
        
    taxa_unitaria = promoter_info.data[0].get('valor_convite', 2.00)

    if request.method == 'POST':
        evento_id = request.form.get('evento_id')
        cliente = request.form.get('nome_cliente')
        fone = request.form.get('telefone_cliente')
        
        # Valores de segurança
        nome_evento = "Evento"
        data_formatada = "--/--/----"     
        
        try:
            # 1. BUSCA DADOS DO EVENTO SELECIONADO (Buscamos direto na tabela 'eventos' para facilitar)
            res_ev = supabase.table("eventos").select("nome, data_evento, pago, saldo_creditos").eq("id", evento_id).execute()
            
            if not res_ev.data:
                return "Erro: Evento não encontrado."

            ev_data = res_ev.data[0]
            saldo_atual = ev_data.get('saldo_creditos', 0)
            esta_pago = ev_data.get('pago', False)

            # 2. TRAVA DE SEGURANÇA (Baseado no seu modelo: Sem saldo ou não pago = Bloqueado)
            if not esta_pago or saldo_atual <= 0:
                return "❌ Erro: Este evento está bloqueado ou sem saldo de convites. Realize o PIX para ativar."
            if saldo_atual <= 0:
                return "❌ Erro: Seu saldo de convites acabou! Por favor, realize uma recarga."
            
            # 3. DESCONTA 1 CRÉDITO PRIMEIRO (Garante a baixa no estoque)
            novo_saldo = saldo_atual - 1
            supabase.table("eventos").update({"saldo_creditos": novo_saldo}).eq("id", evento_id).execute()
            # Prepara os dados para a mensagem do WhatsApp
            nome_evento = ev_data.get('nome', 'Evento')
            dt = ev_data.get('data_evento', '')
            if dt:
                p = dt.split('-')
                data_formatada = f"{p[2]}/{p[1]}/{p[0]}"

            # 3. GERA O CONVITE NO BANCO
            resposta = supabase.table("convites").insert({
                "nome_cliente": cliente, 
                "telefone": fone, 
                "promoter_id": p_id, 
                "evento_id": evento_id
            }).execute()

            if not resposta.data:
                # Caso falhe a inserção, devolvemos o crédito (estorno de segurança)
                supabase.table("eventos").update({"saldo_creditos": saldo_atual}).eq("id", evento_id).execute()
                return "Erro ao gerar convite no banco de dados."

            # --- CONTINUAÇÃO DO SEU CÓDIGO (Gerar Token e Link WhatsApp) ---
            token = resposta.data[0]['qrcode']
            # ... resto do código (link_visualizacao, msg_texto, etc)
                     
            
            base_url = request.host_url.rstrip('/')
            link_visualizacao = f"https://ticketszap.com.br/v/{token}"
            
            if res_ev.data:
                ev_data = res_ev.data[0]
                
                # 1. PEGA O NOME DO EVENTO
                nome_evento = ev_data.get('nome') or 'Evento'
                
                # 2. PEGA E FORMATA A DATA (Tratamento reforçado)
                dt_raw = ev_data.get('data_evento')
                data_formatada = "--/--/----" # Valor padrão caso falhe
                
                if dt_raw:
                    try:
                        # Tenta formatar se vier como YYYY-MM-DD
                        if '-' in str(dt_raw):
                            partes = str(dt_raw).split('-')
                            # Garante que temos 3 partes (ano, mes, dia)
                            if len(partes) == 3:
                                data_formatada = f"{partes[2]}/{partes[1]}/{partes[0]}"
                        else:
                            # Se a data já vier formatada ou em outro padrão, usa ela mesma
                            data_formatada = str(dt_raw)
                    except:
                        data_formatada = str(dt_raw)

            # --- MONTAGEM DA MENSAGEM (LAYOUT CORRETO) ---
            msg_texto = (
                f"✅ *Seu Convite Chegou!*\n\n"
                f"🎈 Evento: *{nome_evento}*\n"
                f"📅 Data: *{data_formatada}*\n"
                f"👤 Cliente: {cliente}\n\n"
                f"Acesse seu QR Code aqui:\n\n"
                f"{link_visualizacao}\n\n"
                f"⚠️ *Apresente este link na portaria.*"
            )
            
            msg_codificada = urllib.parse.quote(msg_texto)
            fone_limpo = "".join(filter(str.isdigit, fone))
            if not fone_limpo.startswith("55"): fone_limpo = "55" + fone_limpo
            
            # USANDO O NOME CORRETO: msg_codificada
            link_wa = f"https://api.whatsapp.com/send?phone={fone_limpo}&text={msg_codificada}"

            link_retorno = "/painel?modo=vendedor" if modo_vendedor else "/painel"
            
            return render_template_string(f'''
                
                {BASE_STYLE}
               
                <div class="card">
                    <h2 style="color:#28a745;">✅ Sucesso!</h2>
                    <p>Convite para <strong>{cliente}</strong> gerado.</p>
                    <p style="font-size:13px; color:#666;">{nome_evento} | {data_formatada}</p>
                    <div style="background:#eee; padding:15px; border-radius:10px; margin:15px 0;">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={token}" style="width:100%; max-width:200px;">
                    </div>
                    <a href="{link_wa}" target="_blank" class="btn btn-whatsapp">📱 Enviar WhatsApp</a>

                    <a href="{link_retorno}" class="link-back">⬅️ Criar outro</a>
                    
                </div>
               
            ''')
        except Exception as e: 
            return f"Erro crítico: {str(e)}"

    # --- 2. BUSCA EVENTOS DO PROMOTER (COM FILTRO E CRÉDITOS) ---
    # Buscamos na tabela de ligação para garantir o filtro por promoter_id
    res_eventos = supabase.table("promoter_eventos")\
        .select("*, eventos(id, nome, pago, data_evento, preco_ingresso, saldo_creditos)")\
        .eq("promoter_id", p_id).execute()
    
    meus_eventos = []
    
    if res_eventos.data:
        for item in res_eventos.data:
            # Aqui garantimos que o evento existe e pegamos os dados dele
            ev_raw = item.get('eventos')
            
            if ev_raw:
                # Criamos um dicionário limpo para o Jinja2 não se perder
                ev_processado = {
                    'id': ev_raw.get('id'),
                    'nome': ev_raw.get('nome'),
                    'pago': ev_raw.get('pago', False),
                    'data_evento': ev_raw.get('data_evento'),
                    'preco_ingresso': ev_raw.get('preco_ingresso', 0),
                    'saldo_creditos': ev_raw.get('saldo_creditos', 0) # Se for None, vira 0
                }
                
                # Busca contagem de convites para o relatório/financeiro
                contagem = supabase.table("convites").select("id", count="exact").eq("evento_id", ev_processado['id']).execute()
                total_convites = contagem.count if contagem.count else 0
                
                ev_processado['total_pagar'] = total_convites * taxa_unitaria
                ev_processado['qtd_emitida'] = total_convites
                
                meus_eventos.append(ev_processado)

   # --- 3. HTML DO PAINEL ATUALIZADO ---
   # --- 3. HTML DO PAINEL ATUALIZADO ---
    html_painel = f'''
        {BASE_STYLE}
        <div class="card">
            
            <div style="text-align: center; margin-bottom: 20px;">
                <h3 style="margin-bottom: 15px;">📍 Terminal de Vendas</h3>
                
                <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
                    <a href="/painel?modo=vendedor" style="flex: 1; background: #28a745; color: white; padding: 12px; border-radius: 10px; text-decoration: none; font-size: 14px; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 5px;">
                        💰 Vendas
                    </a>
                    
                    <a href="#" onclick="irParaPortaria(event)" style="flex: 1; background: #1a73e8; color: white; padding: 12px; border-radius: 10px; text-decoration: none; font-size: 14px; font-weight: bold; display: flex; align-items: center; justify-content: center; gap: 5px;">
                        🛂 Portaria
                    </a>
                </div>

                {{% if not modo_vendedor %}}
                    <a href="/logout" style="color:red; font-size:12px; text-decoration:none; display:block; margin-top:10px;">Sair</a>
                {{% endif %}}
            </div>

            {{% if not modo_vendedor %}}
                <a href="/novo_evento" class="btn btn-secondary" style="background:#6c757d; margin-bottom:10px; display:block; text-align:center; text-decoration:none; padding:10px; border-radius:8px; color:white;">➕ Novo Evento</a>
                <a href="/relatorio" style="display:block; margin-bottom:15px; color:#1a73e8; text-decoration:none; font-weight:bold; text-align:center;">📊 Relatório de Vendas</a>
                
                <div style="background:#f0f7ff; padding:12px; border-radius:10px; margin-bottom:15px; border:1px solid #d0e3ff; text-align:center;">
                    <p style="margin:0 0 8px 0; font-size:11px; color:#555;">Vai entregar o celular para o staff?</p>
                    <a href="/painel?modo=vendedor" style="display:inline-block; background:#007bff; color:#fff; padding:6px 12px; border-radius:20px; font-size:11px; font-weight:bold; text-decoration:none;">
                        🛡️ ATIVAR MODO VENDEDOR
                    </a>
                </div>
                <hr>
            {{% endif %}}

            <h4 style="text-align:left; margin-bottom:5px;">🎟️ Emitir Convite</h4>
            <form method="POST">
                <select name="evento_id">
                    {{% for ev in eventos %}}
                        {{% if ev.pago and ev.saldo_creditos > 0 %}}
                            <option value="{{{{ ev.id }}}}">{{{{ ev.nome }}}} (Saldo: {{{{ ev.saldo_creditos }}}})</option>
                        {{% else %}}
                            <option value="{{{{ ev.id }}}}" disabled>{{{{ ev.nome }}}} (Bloqueado/Sem Saldo)</option>
                        {{% endif %}}
                    {{% endfor %}}
                </select>
                <input type="text" name="nome_cliente" placeholder="Nome do Cliente" required>
                <input type="tel" name="telefone_cliente" placeholder="WhatsApp do Cliente" required>

                <button type="submit" class="btn btn-success" 
                    {{{{ 'disabled style="opacity: 0.5; cursor: not-allowed;"' if not eventos or eventos[0].saldo_creditos <= 0 else '' }}}}>
                    Gerar e Enviar QR Code
                </button>
            </form>

            {{% if not modo_vendedor %}}
                <hr>
                <h4 style="text-align:left; margin-bottom:10px;">🛂 Suas Portarias</h4>
                {{% for ev in eventos %}}
                <div style="border: 1px solid #eee; padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; border-left: 5px solid {{{{ '#28a745' if ev.pago else '#d93025' }}}};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 16px;">{{{{ ev.nome }}}}</strong>
                    </div>
                    
                    <div style="margin: 8px 0; font-size: 12px; color: #666;">
                        📅 {{{{ ev.data_evento if ev.data_evento else 'Sem data' }}}} | 🎫 Saldo: {{{{ ev.saldo_creditos }}}}
                    </div>

                    <a href="/portaria?evento_id={{{{ ev.id }}}}" 
                       style="display: block; text-align: center; margin-top: 10px; padding: 12px; border-radius: 8px; background: {{{{ '#1a73e8' if ev.pago else '#f1f1f1' }}}}; color: {{{{ 'white' if ev.pago else '#999' }}}}; text-decoration: none; font-size: 14px; font-weight: bold;">
                        🛂 Abrir Portaria
                    </a>
                </div>
                {{% endfor %}}
            {{% endif %}}

        </div> <script>
        function irParaPortaria(e) {{
            e.preventDefault();
            const select = document.querySelector('select[name="evento_id"]');
            if (select && select.value) {{
                window.location.href = '/portaria?evento_id=' + select.value + '&modo=vendedor';
            }} else {{
                alert('Selecione um evento primeiro!');
            }}
        }}
        </script>
    '''
     
   # return render_template_string(html_painel, eventos=meus_eventos)
    return render_template_string(html_painel, eventos=meus_eventos, modo_vendedor=modo_vendedor)

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
                "criado_por": p_id,
                "pago": False,  # Já nasce bloqueado
                "saldo_creditos": 0
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
    
    # 1. Busca a lista de eventos para o dropdown
    res_ev = supabase.table("promoter_eventos").select("eventos(id, nome)").eq("promoter_id", session['promoter_id']).execute()
    
    meus_eventos = []
    vistos = set()
    for item in res_ev.data:
        if item['eventos'] and item['eventos']['id'] not in vistos:
            meus_eventos.append(item['eventos'])
            vistos.add(item['eventos']['id'])
    
    vendas = []
    saldo_real = 0
    nome_evento = ""

    # 2. SE um evento foi selecionado, buscamos as VENDAS e o SALDO REAL
    if eid: 
        # Forçamos o eid a ser string para a query
        eid_str = str(eid)
        
        # Busca vendas
        vendas = supabase.table("convites").select("*").eq("evento_id", eid_str).order("created_at", desc=True).execute().data
        
        # Busca o saldo real
        res_info = supabase.table("eventos").select("nome, saldo_creditos").eq("id", eid_str).single().execute()
        if res_info.data:
            saldo_real = res_info.data.get('saldo_creditos', 0)
            nome_evento = res_info.data.get('nome', '')
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card">
            <h3>📊 Relatório</h3>
            
            <form method="GET">

                <select name="evento_id" onchange="this.form.submit()" style="width: 100%; padding: 10px; border-radius: 8px;">
    <option value="">Selecionar Evento...</option>
    {{% for ev in eventos %}}
        <option value="{{{{ ev.id }}}}" {{"selected" if ev.id|string == eid|string else ""}}>
            {{{{ ev.nome }}}}
        </option>
    {{% endfor %}}
</select>
            </form>

            {{% if eid %}}
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; border: 1px solid #e0e0e0; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 14px;">Evento: <strong>{{{{ nome_evento }}}}</strong></p>
                    <h2 style="margin: 5px 0; color: {{{{ '#28a745' if saldo_real > 10 else '#d93025' }}}};">
                        {{{{ saldo_real }}}} <small style="font-size: 12px; color: #999;">convites restantes</small>
                    </h2>
                    <p style="margin: 0; font-size: 13px; color: #666;">Total Vendido: <strong>{{{{ vendas|length }}}}</strong></p>
                </div>

                <table style="width:100%; font-size:13px; border-collapse: collapse; margin-top: 10px;">
                    {{% for v in vendas %}}
                    <tr style="border-bottom:1px solid #eee;">
                        <td style="padding:10px 0; text-align:left;"><strong>{{{{v.nome_cliente}}}}</strong></td>
                        <td style="text-align:center; color:#25D366;">{{{{v.telefone}}}}</td>
                        <td style="text-align:right;">
                            <span style="font-size:10px; padding:3px 8px; border-radius:10px; background:{{{{ '#e6f4ea' if v.status else '#fce8e6' }}}}; color:{{{{ '#1e7e34' if v.status else '#d93025' }}}};">
                                {{{{ 'Válido' if v.status else 'Entrou' }}}}
                            </span>
                        </td>
                    </tr>
                    {{% endfor %}}
                </table>
            {{% endif %}}

            <br>
            <a href="/" class="link-back">⬅️ Voltar</a>
        </div>
    ''', eventos=meus_eventos, vendas=vendas, eid=eid, saldo_real=saldo_real, nome_evento=nome_evento)

@app.route('/v/<token>')
def visualizar_convite(token):
    #res = supabase.table("convites").select("*, eventos(nome)").eq("qrcode", token).execute()
    res = supabase.table("convites").select("*, eventos(nome, data_evento)").eq("qrcode", token).execute()
    
    if not res.data: return "Convite Inválido", 404
    convite = res.data[0]
    
   # 1. Pega os dados do evento de forma segura
    evento_info = convite.get("eventos", {})
    nome_evento = evento_info.get("nome", "Evento não encontrado")

# === COLOQUE O PRINT AQUI ===
    print("-----------------------------------------")
    print(f"DEBUG COMPLETO DO CONVITE: {convite}")
    print(f"O QUE TEM DENTRO DE EVENTOS: {convite.get('eventos')}")
    print("-----------------------------------------")


    # 2. Tenta buscar por 'data_evento' ou apenas 'data'
    data_raw = evento_info.get("data_evento") or evento_info.get("data")
    
    data_exibicao = "--/--/----"
    
    if data_raw:
        data_str = str(data_raw).strip()
        if "-" in data_str:
            # Converte AAAA-MM-DD para DD/MM/AAAA
            partes = data_str.split(' ')[0].split('-') # O .split(' ')[0] remove horas se houver
            if len(partes) == 3:
                data_exibicao = f"{partes[2]}/{partes[1]}/{partes[0]}"
        else:
            data_exibicao = data_str


    #print(f"DEBUG DATA: {convite['eventos']}") # Isso vai sair no seu terminal
    #return render_template_string(f'{BASE_STYLE}<div class="card" style="border-top: 8px solid #28a745;"><h2>TICKETS ZAP</h2><p>{convite["eventos"]["nome"]}</p><img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={token}" style="width:100%; max-width:250px;"><p>Cliente: <strong>{convite["nome_cliente"]}</strong></p></div>')
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="border-top: 8px solid #28a745; padding: 30px;">
            <h1 style="color: #28a745; margin-bottom: 5px; font-size: 24px;">TICKETS ZAP</h1>
            <p style="font-size: 14px; color: #666; margin-bottom: 20px;">Comprovante de Entrada</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #333;">{convite["eventos"]["nome"]}</h3>
                <p style="margin: 5px 0 0 0; color: #1a73e8; font-weight: bold;">📅 Data: {data_exibicao}</p>
            </div>

            <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={token}" 
                 style="width: 100%; max-width: 250px; border: 10px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            
            <div style="margin-top: 20px; border-top: 1px dashed #ddd; padding-top: 15px;">
                <p style="margin: 0; color: #666; font-size: 14px;">Titular do Convite:</p>
                <strong style="font-size: 18px; color: #000;">{convite["nome_cliente"]}</strong>
            </div>
            
            <p style="font-size: 12px; color: #999; margin-top: 20px;">
                ⚠️ Apresente este QR Code na portaria do evento.
            </p>
        </div>
    ''')
@app.route('/portaria', methods=['GET', 'POST'])
def portaria():
    evento_id = request.args.get('evento_id')
    

    if not evento_id: return redirect(url_for('index'))

    # 1. Busca info do evento
    res_evento = supabase.table("eventos").select("pago, nome").eq("id", evento_id).execute()
    if not res_evento.data: return "Evento não encontrado"
    evento = res_evento.data[0]

    # Trava Financeira
    if not evento['pago']:
        return render_template_string(f'''{BASE_STYLE}<div class="card"><h2>🔒 Bloqueado</h2><p>Realize o pagamento para ativar.</p></div>''')

    msg, cor = None, "transparent"
    
    # 2. Processa o Scan
    if request.method == 'POST':
        token_bruto = request.form.get('qrcode_token')
        # Limpeza: Se o scanner ler a URL inteira, pegamos só o código final
        token = token_bruto.split('/')[-1] if token_bruto else ""

        res = supabase.table("convites").select("*").eq("qrcode", token).eq("evento_id", evento_id).execute()
        
        if res.data:
            convite = res.data[0]
            if convite['status']:
                supabase.table("convites").update({"status": False}).eq("qrcode", token).execute()
                msg, cor = f"✅ LIBERADO: {convite['nome_cliente']}", "#28a745"
            else: 
                msg, cor = f"❌ JÁ UTILIZADO POR: {convite['nome_cliente']}", "#d93025"
        else: 
            msg, cor = "⚠️ NÃO ENCONTRADO", "#f29900"

    # 3. Histórico
    res_hist = supabase.table("convites").select("nome_cliente, updated_at")\
        .eq("evento_id", evento_id)\
        .eq("status", False)\
        .order("updated_at", desc=True)\
        .limit(3).execute()
    historico = res_hist.data if res_hist.data else []


    # Captura se veio do modo vendedor
    modo_vendedor = request.args.get('modo') == 'vendedor'
    # IMPORTANTE: Usamos variáveis normais e evitamos o conflito de f-string com Jinja2
    return render_template_string('''
        ''' + BASE_STYLE + '''
        <div class="card" style="background:#1a1a1a; color:white; text-align:center; min-height: 100vh; margin:0; border-radius:0; width:100%; max-width:100%;">
            
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 15px 15px 0 15px;">
                <h3 style="color:white; margin:0;">🛂 Portaria</h3>
                
                {% if modo_vendedor %}
                    <a href="/painel?modo=vendedor" style="color:#888; text-decoration:none; font-size:13px; border:1px solid #444; padding:5px 10px; border-radius:5px;">⬅️ Vendas</a>
                {% else %}
                    <a href="/painel" style="color:#888; text-decoration:none; font-size:13px; border:1px solid #444; padding:5px 10px; border-radius:5px;">⬅️ Painel</a>
                {% endif %}

            </div>

            <p style="color:#888; font-size:14px; margin-bottom:20px;">''' + evento['nome'] + '''</p>
            
            {% if msg %}
                <div style="background: {{ cor }}; padding:40px 20px; border-radius:15px; margin:20px 0; font-weight:bold; font-size:24px; border: 3px solid white;">
                    {{ msg }}
                </div>
                <a href="/portaria?evento_id=''' + str(evento_id) + '''{% if modo_vendedor %}&modo=vendedor{% endif %}" class="btn btn-primary" style="background:white; color:black; font-size:18px;">PRÓXIMO CLIENTE</a>
            {% else %}
                <div id="reader" style="width:100%; border-radius:15px; overflow:hidden; border: 2px solid #333; background:#000;"></div>
                <form method="POST" id="form-p">
                    <input type="hidden" name="qrcode_token" id="qct">
                </form>
            {% endif %}

            <div style="margin-top: 40px; text-align: left; background: #222; padding: 15px; border-radius: 12px; margin-left:10px; margin-right:10px;">
                <p style="color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">Últimos Check-ins</p>
                {% for h in historico %}
                    <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #333; font-size: 14px;">
                        <span style="color: #eee;">👤 {{ h.nome_cliente }}</span>
                        <span style="color: #28a745; font-weight: bold;">OK</span>
                    </div>
                {% else %}
                    <p style="color: #444; font-size: 12px;">Aguardando entrada...</p>
                {% endfor %}
            </div>

            {% if not modo_vendedor %}
                <a href="/logout" 
                   onclick="return confirm('Deseja realmente encerrar a portaria e sair do sistema?')"
                   style="color:#ff4444; display:block; margin:40px 10px 20px 10px; text-decoration:none; font-size:14px; border: 1px solid #333; padding: 12px; border-radius: 10px; font-weight: bold; background: #222;">
                    ⚠️ ENCERRAR E SAIR
                </a>
            {% endif %}
        </div>

        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
            function onScan(t) { 
                document.getElementById('qct').value = t; 
                document.getElementById('form-p').submit(); 
                if(typeof html5QrcodeScanner !== 'undefined') html5QrcodeScanner.clear();
            }
            let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
            html5QrcodeScanner.render(onScan);
        </script>
    ''', evento=evento, modo_vendedor=modo_vendedor, msg=msg, cor=cor, historico=historico)

# --- ROTA DO PAINEL ADMIN (MOSTRAR E LIBERAR) ---
@app.route('/painel_admin_secreto', methods=['GET', 'POST'])
def admin_secreto():
    # 1. TRAVA DE SEGURANÇA: Se não estiver logado como admin, volta pro login
    if not session.get('admin_logado'):
        return redirect(url_for('login_admin'))

    # 2. PROCESSA A LIBERAÇÃO (Quando você clica no botão)
    if request.method == 'POST':
        ev_id = request.form.get('evento_id')
        qtd = int(request.form.get('quantidade', 250))
        
        try:
            # Ativa o evento e define o saldo
            supabase.table("eventos").update({
                "pago": True, 
                "saldo_creditos": qtd
            }).eq("id", ev_id).execute()
            # O código continua abaixo para recarregar a página com sucesso
        except Exception as e:
            return f"Erro ao liberar: {str(e)}"

    # 3. BUSCA OS DADOS PARA A TABELA
    res = supabase.table("eventos").select("*, promoter(nome)").execute()
    eventos = res.data

    html_admin = f'''
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f4f7f6; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px 15px; border-bottom: 1px solid #ddd; text-align: left; }}
        th {{ background: #1a73e8; color: white; }}
        .btn-liberar {{ background: #28a745; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; }}
        .logout {{ color: red; text-decoration: none; font-size: 14px; }}
    </style>

    <div class="header">
        <h2>🚀 Gestão de Créditos TicketsZap</h2>
        <a href="/logout_admin" class="logout">Sair do Admin</a>
    </div>

    <table>
        <thead>
            <tr>
                <th>Promoter</th>
                <th>Evento</th>
                <th>Saldo Atual</th>
                <th>Status</th>
                <th>Ação</th>
            </tr>
        </thead>
        <tbody>
            {{% for ev in eventos %}}
            <tr>
                <td><strong>{{{{ ev.promoter.nome if ev.promoter else 'N/A' }}}}</strong></td>
                <td>{{{{ ev.nome }}}}</td>
                <td>{{{{ ev.saldo_creditos }}}}</td>
                <td>
                    <span style="color: {{{{ 'green' if ev.pago else 'red' }}}}; font-weight: bold;">
                        {{{{ 'ATIVO' if ev.pago else 'PENDENTE' }}}}
                    </span>
                </td>
                <td>
                    <form method="POST">
                        <input type="hidden" name="evento_id" value="{{{{ ev.id }}}}">
                        <input type="number" name="quantidade" value="250" style="width: 60px; padding: 5px;">
                        <button type="submit" class="btn-liberar">Liberar</button>
                    </form>
                </td>
            </tr>
            {{% endfor %}}
        </tbody>
    </table>
    '''
    return render_template_string(html_admin, eventos=eventos)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    # Se já estiver logado, vai direto para o painel
    if session.get('admin_logado'):
        return redirect(url_for('admin_secreto'))

    if request.method == 'POST':
     
        # Mude as linhas do request para isso:
        email = request.form.get('email').strip() # .strip() remove espaços extras
        chave = request.form.get('chave').strip()
        # Busca na sua nova tabela 'administrador'
        res = supabase.table("administrador").select("*").eq("email", email).eq("chave", chave).execute()
        
        print(f"DEBUG LOGIN: {res.data}") # Veja o que aparece no seu terminal preto/azul

        if res.data:
            session['admin_logado'] = True
            # Opcional: guardar o nome do adm na sessão
            session['admin_email'] = email 
            return redirect(url_for('admin_secreto'))
        else:
            # Mensagem de erro simples
            return '''
                <script>alert("E-mail ou Chave incorretos!"); window.location.href="/login_admin";</script>
            '''
            
    return render_template_string('''
        <style>
            body { font-family: sans-serif; background: #f0f2f5; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .login-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); width: 100%; max-width: 350px; text-align: center; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            button:hover { background: #1557b0; }
        </style>
        <div class="login-card">
            <h2 style="color: #1a73e8; margin-top: 0;">TicketsZap Admin</h2>
            <p style="color: #666; font-size: 14px;">Área restrita para liberação de créditos</p>
            <form method="POST">
                <input type="email" name="email" placeholder="E-mail do Administrador" required>
                <input type="password" name="chave" placeholder="Chave de Acesso" required>
                <button type="submit">Acessar Painel</button>
            </form>
            <p style="margin-top: 20px;"><a href="/" style="color: #999; text-decoration: none; font-size: 12px;">← Voltar ao site</a></p>
        </div>
    ''')
@app.route('/logout_admin')
def logout_admin():
    # Remove apenas a chave do admin da sessão
    session.pop('admin_logado', None)
    session.pop('admin_email', None)
    # Redireciona de volta para a tela de login do admin
    return redirect(url_for('login_admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)