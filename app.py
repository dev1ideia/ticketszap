import io
import base64
import qrcode
import urllib.parse
import os
from flask import Flask, render_template_string, request, session, redirect, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid # No topo do arquivo
from urllib.parse import quote_plus

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
    .btn-secondary { background: #28a745 !important; color: white !important; }

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
@app.route('/gerar_convite/<int:evento_id>/<tipo>')
def gerar_convite(evento_id, tipo):
    # tipo pode ser 'vendedor' ou 'porteiro'
    token = str(uuid.uuid4())[:8] # Gera um código como 'a1b2c3d4'
    
    # Salva no banco (Tabela que você sugeriu ou uma de convites)
    # Aqui você guardaria o token, o evento_id e o tipo de permissão
    supabase.table("convites_pendentes").insert({
        "token": token,
        "evento_id": evento_id,
        "tipo": tipo
    }).execute()

    # Monta a mensagem para o WhatsApp
    link = f"https://ticketszap.com.br/aceitar/{token}" #MUDAR AQUI PARA LIVE
    #link = f"http://127.0.0.1:5000/aceitar/{token}"

    mensagem = f"Olá! Você foi convidado para ser {tipo} no meu evento. Acesse o link para aceitar: {link}"
    
    # Redireciona direto para o zap (sem precisar salvar contato)
    import urllib.parse
    msg_encoded = urllib.parse.quote(mensagem)
    return redirect(f"https://wa.me/?text={msg_encoded}")

@app.route('/aceitar/<token>')
def aceitar_convite(token):
    # 1. Verifica se o token existe no banco
    res = supabase.table("convites_pendentes").select("*").eq("token", token).execute()
    
    if not res.data:
        return "Convite inválido ou expirado! ❌"

    # 2. Mostra um formulário para ele preencher Nome, Telefone e Documento
    return render_template_string('''
<div class="card">
    <h2>🤝 Aceitar Convite</h2>
    <p>Preencha seus dados para começar.</p>
    <form method="POST" action="/finalizar_cadastro_func" onsubmit="return validarTelefone()">
        <input type="hidden" name="token" value="{{token}}">
        <input type="text" name="nome" placeholder="Seu Nome Completo" required>
        
        <input type="tel" id="telefone" name="telefone" 
               placeholder="(00) 00000-0000" 
               maxlength="15" 
               required>
        
        <input type="text" name="documento" placeholder="Seu CPF" required>
        <button type="submit">Confirmar Cadastro</button>
    </form>
</div>

<script>
    const telInput = document.getElementById('telefone');

    // Máscara de Telefone em tempo real
    telInput.addEventListener('input', (e) => {
        let x = e.target.value.replace(/\D/g, '').match(/(\d{0,2})(\d{0,5})(\d{0,4})/);
        e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
    });

    // Validação extra antes de enviar
    function validarTelefone() {
        const valor = telInput.value.replace(/\D/g, ''); // Tira tudo que não é número
        if (valor.length < 11) {
            alert('Por favor, insira o telefone completo com DDD (11 dígitos).');
            return false;
        }
        return true;
    }
</script>
''', token=token)

@app.route('/finalizar_cadastro_func', methods=['POST'])
def finalizar_cadastro_func():
    # 1. PEGA OS DADOS DO FORMULÁRIO
    token = request.form.get('token')
    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    documento = request.form.get('documento')

    try:
        # 2. BUSCA O CONVITE PELO TOKEN PARA SABER QUAL O EVENTO E O CARGO
        convite_res = supabase.table("convites_pendentes").select("*").eq("token", token).execute()
        
        if not convite_res.data:
            return "Erro: Convite expirado ou inválido."

        dados_convite = convite_res.data[0]
        evento_id = dados_convite['evento_id']
        cargo = dados_convite['tipo'] # 'vendedor' ou 'porteiro'

        # 3. CRIA O FUNCIONÁRIO (ou atualiza se já existir pelo telefone)
        # Usamos .upsert para não duplicar se ele já trabalhou em outro evento
        func_res = supabase.table("funcionarios").upsert({
            "nome": nome,
            "telefone": telefone,
            "documento": documento
        }, on_conflict="telefone").execute()
        
        func_id = func_res.data[0]['id']

        # 4. VINCULA O FUNCIONÁRIO AO EVENTO
        # Aqui definimos as flags baseadas no cargo do convite
        is_vendedor = True if cargo == 'vendedor' else False
        is_porteiro = True if cargo == 'porteiro' else False

        supabase.table("evento_funcionarios").insert({
            "evento_id": evento_id,
            "funcionario_id": func_id,
            "ativo": True,
            "vendedor": is_vendedor,
            "porteiro": is_porteiro
        }).execute()

        # 5. DELETA O CONVITE PARA NÃO SER REUTILIZADO
        supabase.table("convites_pendentes").delete().eq("token", token).execute()

        return f'''
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <div style="text-align:center; padding:50px; font-family:sans-serif;">
                <h1 style="color: #28a745;">Sucesso! ✅</h1>
                <p>Tudo pronto, <strong>{nome}</strong>!</p>
                <p>Agora você já pode acessar o painel de {cargo} deste evento.</p>
                <br>
                <a href="/login_funcionario" style="background:#1a73e8; color:white; padding:15px 30px; border-radius:8px; text-decoration:none; font-weight:bold;">Acessar Painel</a>
            </div>
        '''

    except Exception as e:
        return f"Erro ao processar cadastro: {str(e)}"
    
@app.route('/login_funcionario', methods=['GET', 'POST'])
def login_funcionario():
    erro_msg = ""
    # Se o usuário caiu aqui via redirecionamento de erro
    if request.args.get('erro') == 'nao_encontrado':
        erro_msg = '''
            <div style="background: #fee2e2; color: #b91c1c; padding: 12px; border-radius: 10px; 
                        margin-bottom: 20px; font-size: 14px; border: 1px solid #fecaca; text-align: center;">
                <strong>⚠️ Não encontrado!</strong><br> 
                Verifique o telefone ou peça um novo convite.
            </div>
        '''

    if request.method == 'POST':
        telefone = request.form.get('telefone')
        # Limpa o telefone para buscar no banco apenas os números
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        
        # Busca o funcionário pelo telefone (tabela no plural: funcionarios)
        res = supabase.table("funcionarios").select("*").ilike("telefone", f"%{telefone_limpo}%").execute()
        
        if res.data:
            funcionario = res.data[0]
            session['func_id'] = funcionario['id']
            session['func_nome'] = funcionario['nome']
            return redirect(url_for('painel_funcionario'))
        else:
            # Em vez de retornar texto seco, redireciona para a mesma tela com o erro na URL
            return redirect(url_for('login_funcionario', erro='nao_encontrado'))

    return render_template_string(f'''
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-card {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 90%; max-width: 350px; text-align: center; }}
            input {{ width: 100%; padding: 15px; margin: 15px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }}
            button {{ width: 100%; padding: 15px; background: #1a73e8; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 16px; cursor: pointer; }}
        </style>
        <div class="login-card">
            <h2 style="margin-bottom:5px;">TicketsZap Staff</h2>
            <p style="color:#666; margin-bottom:20px;">Acesse com seu WhatsApp</p>
            
            {erro_msg}

            <form method="POST">
                <input type="tel" name="telefone" id="telefone" placeholder="(00) 00000-0000" required autofocus>
                <button type="submit">Entrar no Painel</button>
            </form>
            <p style="margin-top:20px; font-size:13px; color:#999;">Dúvidas? Fale com seu organizador.</p>
        </div>
        <script>
            // Máscara automática
            document.getElementById('telefone').addEventListener('input', (e) => {{
                let x = e.target.value.replace(/\D/g, '').match(/(\d{{0,2}})(\d{{0,5}})(\d{{0,4}})/);
                e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
            }});
        </script>
    ''')

@app.route('/painel_funcionario')
def painel_funcionario():
    # 1. Verifica se o funcionário está logado na sessão
    func_id = session.get('func_id')
    if not func_id:
        return redirect(url_for('login_funcionario'))

    # 2. Busca no banco quais eventos este funcionário está vinculado
    # e quais são as permissões dele (vendedor/porteiro)
    equipe_res = supabase.table("evento_funcionarios")\
        .select("*, eventos(nome, saldo_creditos, pago)")\
        .eq("funcionario_id", func_id)\
        .eq("ativo", True).execute()

    dados_brutos = equipe_res.data if equipe_res.data else []

# --- TRECHO DE LIMPEZA DE DUPLICADOS ---
    eventos_unicos = {}
    for item in dados_brutos:
        ev_id = item.get('evento_id')
        # Se o evento ainda não está no dicionário, adicionamos. 
        # Se já estiver, ele ignora as duplicatas.
        if ev_id and ev_id not in eventos_unicos:
            eventos_unicos[ev_id] = item

# Transformamos o dicionário de volta em uma lista limpa
    eventos_vinculados = list(eventos_unicos.values())

    return render_template_string('''
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #f4f7f6; padding: 15px; }
            .event-card { background: white; padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
            .btn { display: block; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; }
            .badge { font-size: 10px; padding: 3px 8px; border-radius: 10px; color: white; }
        </style>
        
        <h2>Olá, {{ session['func_nome'] }}! 👋</h2>
        <p style="color: #666;">Seus eventos ativos:</p>

        {% for item in eventos %}
        <div class="event-card">
            <strong>{{ item.eventos.nome }}</strong>
            <div style="margin-top: 5px;">
                {% if item.vendedor %}<span class="badge" style="background: #28a745;">Vendedor</span>{% endif %}
                {% if item.porteiro %}<span class="badge" style="background: #007bff;">Porteiro</span>{% endif %}
            </div>

            {% if item.vendedor %}
                <a href="/vendas?evento_id={{ item.evento_id }}" class="btn" style="background: #e8f5e9; color: #2e7d32;">💰 Acessar Vendas</a>
            {% endif %}

            {% if item.porteiro %}
                <a href="/portaria?evento_id={{ item.evento_id }}" class="btn" style="background: #e3f2fd; color: #1565c0;">🛂 Abrir Portaria</a>
            {% endif %}
        </div>
        {% else %}
        <p>Você não tem eventos vinculados no momento.</p>
        {% endfor %}

        <a href="/logout" style="display:block; text-align:center; color:red; margin-top:30px; text-decoration:none; font-size:14px;">Sair do Painel</a>
    ''', eventos=eventos_vinculados)



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
            <a href="/cadastro" class="btn" style="background:#98FB98; color:black; text-decoration:none; display:block; padding:10px; border-radius:8px;">
                ✨ Criar Nova Conta
            </a>

                    <a href="/" style="display: inline-block; background: #ADD8E6; color: black; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; margin-top: 15px;">
                        🏠 Voltar ao Início
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

                    <a href="/login" class="btn-login">CRIAR CONTA</a>
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
    
    if not promoter_info.data:
        session.clear()
        return redirect(url_for('login'))
        
    taxa_unitaria = promoter_info.data[0].get('valor_convite', 2.00)

    if request.method == 'POST':
        evento_id = request.form.get('evento_id')
        cliente = request.form.get('nome_cliente')
        fone = request.form.get('telefone_cliente')
        
        try:
            res_ev = supabase.table("eventos").select("nome, data_evento, pago, saldo_creditos").eq("id", evento_id).execute()
            if not res_ev.data: return "Erro: Evento não encontrado."

            ev_data = res_ev.data[0]
            saldo_atual = ev_data.get('saldo_creditos', 0)
            esta_pago = ev_data.get('pago', False)

            if not esta_pago or saldo_atual <= 0:
                return "❌ Erro: Este evento está bloqueado ou sem saldo. Realize o PIX."
            
            # DESCONTA CRÉDITO
            novo_saldo = saldo_atual - 1
            supabase.table("eventos").update({"saldo_creditos": novo_saldo}).eq("id", evento_id).execute()

            # GERA O CONVITE
            resposta = supabase.table("convites").insert({
                "nome_cliente": cliente, 
                "telefone": fone, 
                "promoter_id": p_id, 
                "evento_id": evento_id
            }).execute()

            token = resposta.data[0]['qrcode']
            link_visualizacao = f"https://ticketszap.com.br/v/{token}"
            
            # Formatação de Data para o Whats
            dt_raw = ev_data.get('data_evento', '')
            data_formatada = "--/--/----"
            if dt_raw and '-' in str(dt_raw):
                p = str(dt_raw).split('-')
                data_formatada = f"{p[2]}/{p[1]}/{p[0]}"

            msg_texto = (
                f"✅ *Seu Convite!*\n\n"
                f"🎈 Evento: *{ev_data.get('nome')}*\n"
                f"📅 Data: *{data_formatada}*\n"
                f"👤 Cliente: {cliente}\n\n"
                f"{link_visualizacao}"
            )
            
            msg_codificada = urllib.parse.quote(msg_texto)
            fone_limpo = "".join(filter(str.isdigit, fone))
            if not fone_limpo.startswith("55"): fone_limpo = "55" + fone_limpo
            link_wa = f"https://api.whatsapp.com/send?phone={fone_limpo}&text={msg_codificada}"

            return render_template_string(f'''
                {BASE_STYLE}
                <div class="card">
                    <h2 style="color:#28a745;">✅ Sucesso!</h2>
                    <p>Convite para <strong>{cliente}</strong> gerado.</p>
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={token}" style="width:180px; margin:15px;">
                    <a href="{link_wa}" target="_blank" class="btn" style="background:#25D366; color:white; display:block; padding:15px; text-decoration:none; border-radius:10px;">📱 Enviar WhatsApp</a>
                    <a href="/painel" style="display:block; margin-top:20px; color:#666;">⬅️ Voltar</a>
                </div>
            ''')
        except Exception as e: 
            return f"Erro crítico: {str(e)}"

    # --- 2. BUSCA EVENTOS DO PROMOTER ---
    res_eventos = supabase.table("promoter_eventos").select("*, eventos(id, nome, pago, data_evento, saldo_creditos)").eq("promoter_id", p_id).execute()
    meus_eventos = []
    
    if res_eventos.data:
        for item in res_eventos.data:
            ev_raw = item.get('eventos')
            if ev_raw:
                contagem = supabase.table("convites").select("id", count="exact").eq("evento_id", ev_raw['id']).execute()
                total_c = contagem.count if contagem.count else 0
                meus_eventos.append({
                    'id': ev_raw['id'],
                    'nome': ev_raw['nome'],
                    'pago': ev_raw['pago'],
                    'data_evento': ev_raw['data_evento'],
                    'saldo_creditos': ev_raw.get('saldo_creditos', 0),
                    'total_pagar': total_c * taxa_unitaria
                })

    # --- 3. HTML (INDENTADO DENTRO DA FUNÇÃO) ---
    # Use f-string para injetar o BASE_STYLE direto no HTML antes de enviar ao Jinja
    html_final = f"""
    {BASE_STYLE}
    <div class="card">
        {{% if not modo_vendedor %}}
            <a href="/novo_evento" class="btn" style="background:#1a73e8; color:white; display:block; text-align:center; text-decoration:none; padding:15px; border-radius:10px; margin-bottom:15px;">➕ Criar Novo Evento</a>
            <a href="/relatorio" style="display:block; text-align:center; margin-bottom:20px; text-decoration:none; color:#1a73e8; font-weight:bold;">📊 Relatórios</a>
        {{% endif %}}

        <h4 style="margin-bottom:10px;">🎟️ Emitir Convite Rápido</h4>
        <form method="POST">
            <select name="evento_id" style="width:100%; padding:12px; border-radius:8px; margin-bottom:10px; border:1px solid #ddd;">
                {{% for ev in eventos %}}
                    <option value="{{{{ ev.id }}}}" {{{{ 'disabled' if not ev.pago or ev.saldo_creditos <= 0 }}}}>
                        {{{{ ev.nome }}}} (Saldo: {{{{ ev.saldo_creditos }}}})
                    </option>
                {{% endfor %}}
            </select>
            <input type="text" name="nome_cliente" placeholder="Nome do Cliente" required style="width:100%; padding:12px; margin-bottom:10px; border-radius:8px; border:1px solid #ddd;">
            <input type="tel" id="telefone_mask" name="telefone_cliente" placeholder="(00) 00000-0000" required 
       style="width:100%; padding:12px; margin-bottom:15px; border-radius:8px; border:1px solid #ddd; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Gerar Convite</button>
        </form>

        <hr style="opacity:0.1; margin: 30px 0;">
        <h4>🛂 Minhas Portarias</h4>
        {{% for ev in eventos %}}
            <div style="border:1px solid #eee; padding:15px; border-radius:12px; margin-bottom:10px; border-left:5px solid {{{{ '#28a745' if ev.pago else '#d93025' }}}}; background:#fff;">
                <strong style="font-size:16px;">{{{{ ev.nome }}}}</strong><br>
                <small style="color:#666;">Saldo: {{{{ ev.saldo_creditos }}}} | Data: {{{{ ev.data_evento }}}}</small>
                
                <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:10px;">
                    <a href="/portaria?evento_id={{{{ ev.id }}}}" style="flex:1; min-width:100px; background:#1a73e8; color:white; text-align:center; padding:10px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:14px;">Portaria</a>
                    
                    <a href="/gerenciar_staff/{{{{ ev.id }}}}" style="flex:1; min-width:100px; background:#f8f9fa; border:1px solid #ddd; text-align:center; padding:10px; border-radius:8px; text-decoration:none; color:#333; font-size:14px;">Equipe</a>
                    
                    <a href="https://api.whatsapp.com/send?text=Olá! Faça parte da equipe do evento *{{{{ ev.nome }}}}*. Clique no link para aceitar: https://ticketszap.com.br/convite_staff/{{{{ ev.id }}}}" 
                       target="_blank"
                       style="flex:1; min-width:100%; background:#25d366; color:white; text-align:center; padding:10px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:14px; margin-top:5px;">
                       ➕ Convidar Staff (WhatsApp)
                    </a>
                </div>
            </div>
        {{% endfor %}}
        
        <a href="/logout" style="color:red; display:block; text-align:center; margin-top:25px; text-decoration:none; font-size:12px; opacity:0.7;">Sair da conta</a>
       <script>
            const telInput = document.getElementById('telefone_mask');

            telInput.addEventListener('input', (e) => {{
                // Note as chaves duplas abaixo:
                let x = e.target.value.replace(/\D/g, '').match(/(\d{{0,2}})(\d{{0,5}})(\d{{0,4}})/);
                e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
            }});

            telInput.addEventListener('blur', (e) => {{
                const num = e.target.value.replace(/\D/g, '');
                if (num.length > 0 && num.length < 10) {{
                    alert('⚠️ Por favor, insira o número completo com DDD.');
                    e.target.value = '';
                }}
            }});
        </script>
    </div>
    """
    return render_template_string(html_final, eventos=meus_eventos, modo_vendedor=modo_vendedor)

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
    # 1. Identifica quem está logado (Promoter ou Funcionário)
    p_id = session.get('promoter_id')
    f_id = session.get('func_id')
    
    if not p_id and not f_id: 
        return redirect(url_for('login'))

    evento_id = request.args.get('evento_id')
    if not evento_id: return redirect(url_for('index'))

    # 2. Busca info do evento
    res_evento = supabase.table("eventos").select("pago, nome").eq("id", evento_id).execute()
    if not res_evento.data: return "Evento não encontrado"
    evento = res_evento.data[0]

    # Trava Financeira
    if not evento['pago']:
        return render_template_string(f'''{BASE_STYLE}<div class="card"><h2>🔒 Bloqueado</h2><p>Realize o pagamento para ativar.</p></div>''')

    msg, cor = None, "transparent"
    
    # 3. Processa o Scan
    if request.method == 'POST':
        token_bruto = request.form.get('qrcode_token')
        token = token_bruto.split('/')[-1] if token_bruto else ""

        res = supabase.table("convites").select("*").eq("qrcode", token).eq("evento_id", evento_id).execute()
        
        if res.data:
            convite = res.data[0]
            if convite['status']:
                # Marcar como usado e você pode adicionar uma coluna 'validado_por' futuramente
                supabase.table("convites").update({"status": False}).eq("qrcode", token).execute()
                msg, cor = f"✅ LIBERADO: {convite['nome_cliente']}", "#28a745"
            else: 
                msg, cor = f"❌ JÁ UTILIZADO POR: {convite['nome_cliente']}", "#d93025"
        else: 
            msg, cor = "⚠️ NÃO ENCONTRADO", "#f29900"

    # 4. Histórico (Busca os últimos 3 que entraram)
    res_hist = supabase.table("convites").select("nome_cliente, updated_at")\
        .eq("evento_id", evento_id)\
        .eq("status", False)\
        .order("updated_at", desc=True)\
        .limit(3).execute()
    historico = res_hist.data if res_hist.data else []

    # Define para onde voltar (Painel Staff ou Painel Promoter)
    url_retorno = "/painel_funcionario" if f_id else "/painel"

    return render_template_string('''
        ''' + BASE_STYLE + '''
        <div class="card" style="background:#1a1a1a; color:white; text-align:center; min-height: 100vh; margin:0; border-radius:0; width:100%; max-width:100%; box-sizing: border-box;">
            
            <div style="display:flex; justify-content:space-between; align-items:center; padding: 15px;">
                <h3 style="color:white; margin:0;">🛂 Portaria</h3>
                <a href="''' + url_retorno + '''" style="color:#888; text-decoration:none; font-size:13px; border:1px solid #444; padding:5px 10px; border-radius:5px;">⬅️ Sair</a>
            </div>

            <p style="color:#888; font-size:14px; margin-bottom:20px;">''' + evento['nome'] + '''</p>
            
            {% if msg %}
                <div style="background: {{ cor }}; padding:40px 20px; border-radius:15px; margin:20px; font-weight:bold; font-size:24px; border: 3px solid white;">
                    {{ msg }}
                </div>
                <div style="padding: 0 20px;">
                    <a href="/portaria?evento_id=''' + str(evento_id) + '''" class="btn" style="background:white; color:black; font-size:18px; width:100%; display:block; padding:15px; border-radius:10px; text-decoration:none; font-weight:bold;">PRÓXIMO CLIENTE</a>
                </div>
            {% else %}
                <div style="padding: 0 10px;">
                    <div id="reader" style="width:100%; border-radius:15px; overflow:hidden; border: 2px solid #333; background:#000;"></div>
                </div>
                <form method="POST" id="form-p">
                    <input type="hidden" name="qrcode_token" id="qct">
                </form>
            {% endif %}

            <div style="margin: 40px 15px 0 15px; text-align: left; background: #222; padding: 15px; border-radius: 12px;">
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
        </div>

        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
            function onScan(t) { 
                document.getElementById('qct').value = t; 
                document.getElementById('form-p').submit(); 
                if(typeof html5QrcodeScanner !== 'undefined') html5QrcodeScanner.clear();
            }
            // qrbox: 250 para facilitar a leitura no celular
            let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: {width: 250, height: 250} });
            html5QrcodeScanner.render(onScan);
        </script>
    ''', evento=evento, msg=msg, cor=cor, historico=historico)
# --- ROTA DO PAINEL ADMIN (MOSTRAR E LIBERAR) ---
@app.route('/painel_admin_secreto', methods=['GET', 'POST'])
def admin_secreto():
    if not session.get('admin_logado'):
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        ev_id = request.form.get('evento_id')
        qtd = int(request.form.get('quantidade', 250))
        try:
            supabase.table("eventos").update({"pago": True, "saldo_creditos": qtd}).eq("id", ev_id).execute()
        except Exception as e:
            return f"Erro: {str(e)}"

    res = supabase.table("eventos").select("*, promoter(nome)").execute()
    eventos = res.data

    html_admin = f'''
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: sans-serif; padding: 15px; background: #f4f7f6; margin: 0; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        
        /* Estilo para transformar a tabela em cards no celular */
        .container {{ display: grid; gap: 15px; }}
        .evento-card {{ 
            background: white; padding: 15px; border-radius: 12px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 5px solid #1a73e8;
        }}
        .evento-info {{ margin-bottom: 10px; font-size: 14px; }}
        .btn-liberar {{ 
            background: #28a745; color: white; border: none; padding: 12px; 
            border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%;
        }}
        input[type="number"] {{ 
            width: 100%; padding: 10px; margin-bottom: 10px; 
            border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; 
        }}
        .status {{ font-weight: bold; float: right; }}
        .logout {{ color: red; text-decoration: none; font-size: 14px; }}
    </style>

    <div class="header">
        <h2 style="font-size: 1.2rem; margin: 0;">🚀 Admin Zap</h2>
        <a href="/logout_admin" class="logout">Sair</a>
    </div>

    <div class="container">
        {{% for ev in eventos %}}
        <div class="evento-card">
            <span class="status" style="color: {{{{ 'green' if ev.pago else 'red' }}}};">
                {{{{ 'ATIVO' if ev.pago else 'PENDENTE' }}}}
            </span>
            <div class="evento-info">
                <strong>{{{{ ev.promoter.nome if ev.promoter else 'N/A' }}}}</strong><br>
                <span style="color: #666;">Evento: {{{{ ev.nome }}}}</span><br>
                <span>Saldo: <strong>{{{{ ev.saldo_creditos }}}}</strong></span>
            </div>
            
            <form method="POST" style="margin-top: 10px;">
                <input type="hidden" name="evento_id" value="{{{{ ev.id }}}}">
                <label style="font-size: 12px; color: #888;">Qtd Créditos:</label>
                <input type="number" name="quantidade" value="250">
                <button type="submit" class="btn-liberar">Liberar Créditos</button>
            </form>
        </div>
        {{% endfor %}}
    </div>
    '''
    return render_template_string(html_admin, eventos=eventos)

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if session.get('admin_logado'):
        return redirect(url_for('admin_secreto'))

    if request.method == 'POST':
        email = request.form.get('email').strip()
        chave = request.form.get('chave').strip()
        res = supabase.table("administrador").select("*").eq("email", email).eq("chave", chave).execute()

        if res.data:
            session['admin_logado'] = True
            session['admin_email'] = email 
            return redirect(url_for('admin_secreto'))
        else:
            return '<script>alert("Erro!"); window.location.href="/login_admin";</script>'
            
    return render_template_string('''
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #f0f2f5; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 20px; }
            .login-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); width: 100%; max-width: 350px; text-align: center; box-sizing: border-box; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
            button { width: 100%; padding: 14px; background: #1a73e8; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        </style>
        <div class="login-card">
            <h2 style="color: #1a73e8; margin: 0 0 10px 0;">Admin Zap</h2>
            <form method="POST">
                <input type="email" name="email" placeholder="E-mail" required>
                <input type="password" name="chave" placeholder="Chave de Acesso" required>
                <button type="submit">Entrar no Painel</button>
            </form>
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

import uuid # Certifique-se de ter o import uuid no topo do arquivo

import uuid
from urllib.parse import quote_plus

@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    evento_id = request.args.get('evento_id') or request.form.get('evento_id')
    f_id = session.get('func_id')
    f_nome = session.get('func_nome', 'Vendedor')

    id_evento_int = int(evento_id)
    id_vendedor_int = int(f_id)
    meu_qrcode = str(uuid.uuid4())

    if not f_id: return redirect(url_for('login_funcionario'))
    if not evento_id: return "Erro: Evento não selecionado.", 400

    # Busca info do evento
    res_ev = supabase.table("eventos").select("*").eq("id", evento_id).single().execute()
    ev = res_ev.data

    alerta_html = ""
    erro = request.args.get('erro')
    if erro == 'saldo_insuficiente':
        alerta_html = '<div style="background:#fee2e2; color:#b91c1c; padding:15px; border-radius:10px; margin-bottom:20px; text-align:center; border:1px solid #fecaca;">❌ <b>Saldo Insuficiente!</b></div>'
    elif erro == 'erro_banco':
        alerta_html = f'<div style="background:#fff7ed; color:#9a3412; padding:15px; border-radius:10px; margin-bottom:20px; text-align:center; border:1px solid #ffedd5;">⚠️ <b>Erro ao Salvar!</b></div>'

    if request.method == 'POST':
        nome_cliente = request.form.get('nome_cliente')
        fone_cliente = request.form.get('telefone_cliente')
        fone_limpo = ''.join(filter(str.isdigit, fone_cliente))
        
        if ev['saldo_creditos'] <= 0:
            return redirect(url_for('vendas', evento_id=evento_id, erro='saldo_insuficiente'))

        try:
            meu_qrcode = str(uuid.uuid4())
            dados_para_banco = {
                "evento_id": id_evento_int,
                "vendedor_id": id_vendedor_int,
                "nome_cliente": nome_cliente,
                "telefone": fone_limpo,
                "qrcode": meu_qrcode,
                "status": True,
                "promoter_id": None
            }

            print(f"Tentando gravar: {dados_para_banco}")
            res_convite = supabase.table("convites").insert(dados_para_banco).execute()

            # Se NÃO houver dados, algo deu errado na inserção
            if not res_convite.data:
                print("O banco não retornou dados.")
                return redirect(url_for('vendas', evento_id=evento_id, erro='erro_banco'))

            # --- SUCESSO: O CÓDIGO ABAIXO FICA FORA DO IF ---
            
            # 1. Atualiza Saldo do Evento
            novo_saldo = ev['saldo_creditos'] - 1
            supabase.table("eventos").update({"saldo_creditos": novo_saldo}).eq("id", id_evento_int).execute()

            # Preparamos o nome para a mensagem
            nome_vendedor = session.get('func_nome', 'Vendedor')

            # Link que o cliente vai clicar
            link_convite = f"https://ticketszap.com.br/v/{meu_qrcode}"


            # 2. Prepara e Redireciona para o WhatsApp
            #link_convite = f"https://ticketszap.com.br/meu_convite/{meu_qrcode}"
            ##msg = f"Olá {nome_cliente}! Seu convite para *{ev['nome']}* chegou: {link_convite}"
            # Mensagem personalizada para o WhatsApp
            msg = f"*TicketsZap | Vendedor: {nome_vendedor}*\n\n"
            msg += f"Olá {nome_cliente}! Seu convite para o evento *{ev['nome']}* está pronto.\n"
            msg += f"Acesse aqui: {link_convite}"
           # return redirect(f"https://api.whatsapp.com/send?phone=55{fone_limpo}&text={quote_plus(msg)}")
            return redirect(f"https://api.whatsapp.com/send?phone=55{fone_limpo}&text={quote_plus(msg)}")
  
        except Exception as e:
          print(f"ERRO NO SUPABASE: {e}")

        return redirect(url_for('vendas', evento_id=evento_id, erro='erro_banco'))

    # ... (Mantenha o mesmo return render_template_string do passo anterior)

    return render_template_string(f'''
        
    <!DOCTYPE html>
    <html>
    <head>
        {BASE_STYLE}

        <meta property="og:type" content="website">
        {{% if convites.vendedor_id %}}
            <title>TicketsZap | Vendedor: {{ vendedor_nome }}</title>
            <meta property="og:title" content="TicketsZap | Vendedor: {{ vendedor_nome }}">
           {{% else %}}
               <title>TicketsZap | Promoter</title>
               <meta property="og:title" content="TicketsZap | Promoter">
           {{% endif %}}

          <meta property="og:description" content="Evento: {{ evento_nome }} | Cliente: {{ cliente_nome }}">
          <meta property="og:image" content="URL_DA_SUA_LOGO_AQUI">
    </head>
    <body>

        <div class="card" style="max-width:450px; margin:auto;">
            <div style="text-align:center; margin-bottom:20px;">
                <span style="background:#e8f5e9; color:#2e7d32; padding:5px 12px; border-radius:15px; font-size:12px; font-weight:bold;">Vendedor: {f_nome}</span>
                <h3 style="margin-top:10px; margin-bottom:5px;">🎟️ {ev['nome']}</h3>
                <p style="color:#666; font-size:14px; margin:0;">Créditos: <strong style="color:#28a745;">{ev['saldo_creditos']}</strong></p>
            </div>
    </body>
    </html>
            {alerta_html}

            <form method="POST">
                <input type="hidden" name="evento_id" value="{evento_id}">
                
                <label style="display:block; font-size:13px; margin-bottom:5px; font-weight:bold;">Nome do Cliente:</label>
                <input type="text" name="nome_cliente" placeholder="Nome Completo" required 
                       style="width:100%; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:15px; box-sizing:border-box; font-size:16px;">

                <label style="display:block; font-size:13px; margin-bottom:5px; font-weight:bold;">WhatsApp (Com DDD):</label>
                <input type="tel" id="fone_venda" name="telefone_cliente" placeholder="(00) 00000-0000" required 
                       style="width:100%; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:20px; box-sizing:border-box; font-size:16px;">

                <button type="submit" style="width:100%; padding:18px; background:#28a745; color:white; border:none; border-radius:12px; font-weight:bold; font-size:16px; cursor:pointer; transition:0.3s;">
                    ✅ GERAR E ENVIAR CONVITE
                </button>
            </form>

            <a href="/painel_funcionario" style="display:block; text-align:center; margin-top:25px; color:#999; text-decoration:none; font-size:14px;">⬅️ Voltar ao Painel</a>
        </div>

        <script>
            document.getElementById('fone_venda').addEventListener('input', (e) => {{
                let x = e.target.value.replace(/\D/g, '').match(/(\d{{0,2}})(\d{{0,5}})(\d{{0,4}})/);
                e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
            }});
        </script>
    ''')

@app.route('/gerenciar_staff/<int:evento_id>')
def gerenciar_staff(evento_id):
    if 'promoter_id' not in session: return redirect(url_for('login'))
    
    # 1. Busca os funcionários vinculados
    # Note que usamos 'funcionarios' (plural) que é o nome da sua tabela
    res = supabase.table("evento_funcionarios")\
        .select("*, funcionarios(id, nome, telefone)")\
        .eq("evento_id", evento_id).execute()
    
    staff_list = res.data if res.data else []

    # 2. Contagem de vendas
    for membro in staff_list:
        # Segurança: se por algum motivo o join com 'funcionarios' falhar, 
        # evitamos que o código quebre ao tentar acessar o nome
        if not membro.get('funcionarios'):
            membro['funcionarios'] = {'nome': 'Usuário Removido'}

        vendas = supabase.table("convites")\
            .select("id", count="exact")\
            .eq("evento_id", evento_id)\
            .eq("vendedor_id", membro['funcionario_id']).execute()
        
        membro['total_vendas'] = vendas.count if vendas.count else 0

    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="max-width:500px; margin:auto;">
            <h3 style="margin-bottom:5px;">👥 Equipe do Evento</h3>
            <p style="font-size:13px; color:#666; margin-bottom:20px;">Desempenho em tempo real</p>
            
            {{% for m in staff %}}
            <div style="background:#f9f9f9; padding:15px; border-radius:12px; margin-bottom:12px; border-left:5px solid #1a73e8; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong style="font-size:16px; color:#333;">{{{{ m.funcionarios.nome }}}}</strong>
                    <div style="display:flex; gap:5px;">
                        {{% if m.vendedor %}}
                            <span style="font-size:10px; background:#e8f5e9; color:#2e7d32; padding:3px 8px; border-radius:8px; font-weight:bold;">VENDEDOR</span>
                        {{% endif %}}
                        {{% if m.porteiro %}}
                            <span style="font-size:10px; background:#e3f2fd; color:#1565c0; padding:3px 8px; border-radius:8px; font-weight:bold;">PORTEIRO</span>
                        {{% endif %}}
                    </div>
                </div>
                <div style="margin-top:10px; display:flex; align-items:center; gap:10px;">
                    <div style="background:#fff; border:1px solid #ddd; padding:8px 15px; border-radius:8px; flex-grow:1;">
                        <span style="font-size:12px; color:#666;">🎫 Vendas:</span> 
                        <strong style="font-size:18px; color:#1a73e8; margin-left:5px;">{{{{ m.total_vendas }}}}</strong>
                    </div>
                </div>
            </div>
            {{% else %}}
                <div style="text-align:center; padding:40px 20px; color:#999;">
                    <p style="font-size:40px; margin-bottom:10px;">🏘️</p>
                    <p>Nenhum staff vinculado a este evento.</p>
                </div>
            {{% endfor %}}
            
            <a href="/painel" style="display:block; text-align:center; margin-top:25px; color:#666; text-decoration:none; font-size:14px;">⬅️ Voltar ao Painel</a>
        </div>
    ''', staff=staff_list)

@app.route('/convite_staff/<int:evento_id>')
def convite_staff(evento_id):
    # 1. Busca o nome do evento para mostrar na tela
    res = supabase.table("eventos").select("nome").eq("id", evento_id).execute()
    if not res.data: return "Evento não encontrado."
    nome_evento = res.data[0]['nome']

    # 2. Se ele já estiver logado, vincula direto e vai pro painel
    if 'func_id' in session:
        f_id = session['func_id']
        # Vincula no banco (usando upsert para não duplicar)
        supabase.table("evento_funcionarios").upsert({
            "evento_id": evento_id,
            "funcionario_id": f_id,
            "vendedor": True
        }).execute()
        return redirect(url_for('painel_funcionario'))

    # 3. Se NÃO estiver logado, mostra uma tela bonita de Boas-vindas
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="text-align:center;">
            <h2 style="color:#25d366;">🙌 Convite Aceito!</h2>
            <p>Você foi convidado para trabalhar no evento:<br><strong>{nome_evento}</strong></p>
            <hr style="opacity:0.1; margin:20px 0;">
            
            <p style="font-size:14px; color:#666;">Para começar a vender e ganhar comissões, escolha uma opção:</p>
            
            <a href="/login_funcionario?next=/convite_staff/{evento_id}" class="btn" style="background:#1a73e8; color:white; text-decoration:none; display:block; margin-bottom:10px; padding:15px; border-radius:10px;">Já tenho conta (Login)</a>
            
            <a href="/cadastro_funcionario?evento_id={evento_id}" class="btn" style="background:#25d366; color:white; text-decoration:none; display:block; padding:15px; border-radius:10px; font-weight:bold;">Sou Novo (Criar Cadastro)</a>
            
            <p style="margin-top:20px; font-size:12px; color:#999;">TicketsZap - Sistema de Staff</p>
        </div>
    ''')

@app.route('/cadastro_funcionario', methods=['GET', 'POST'])
def cadastro_funcionario():
    # Pega o ID do evento da URL para saber onde vincular o vendedor depois
    evento_id = request.args.get('evento_id') 

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email').strip().lower()
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        # Limpa o telefone para salvar apenas números
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        try:
            print(f"Tentando cadastrar: {nome} | {email} | {telefone_limpo}")

            # 1. Insere na tabela de funcionários
            res = supabase.table("funcionarios").insert({
                "nome": nome,
                "email": email,
                "telefone": telefone_limpo,
                "senha": senha
            }).execute()
            
            f_id = None
            if res.data:
                f_id = res.data[0]['id']
                session['func_id'] = f_id
                session['func_nome'] = nome
                
                # 2. Vincula ao evento na tabela de ligação
                if evento_id:
                    try:
                        # Usamos insert aqui pois a trava de duplicidade (unique) vai agir
                        supabase.table("evento_funcionarios").insert({
                            "evento_id": evento_id,
                            "funcionario_id": f_id,
                            "vendedor": True,
                            "ativo": True
                        }).execute()
                    except Exception as e_vinc:
                        # Se o erro for porque ele já está vinculado, apenas ignoramos e seguimos
                        if "unique_vinc_evento_func" in str(e_vinc).lower() or "duplicate key" in str(e_vinc).lower():
                            print("Funcionário já vinculado ao evento.")
                        else:
                            print(f"Erro ao vincular: {e_vinc}")

                return redirect(url_for('painel_funcionario'))
        
        except Exception as e:
            print(f"ERRO CAPTURADO: {e}")
            # Se o erro for e-mail ou telefone duplicado na tabela funcionários
            if "duplicate key" in str(e).lower():
                return f'''
                    <script>
                        alert("Este E-mail ou WhatsApp já está cadastrado! Por favor, faça login.");
                        window.location.href = "/login_funcionario?evento_id={evento_id if evento_id else ''}";
                    </script>
                '''
            return f"Erro no servidor: {e}"
        
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="card" style="max-width: 400px; margin: auto;">
            <h2 style="text-align:center; color: #1a73e8;">📝 Criar Conta Staff</h2>
            <p style="text-align:center; color: #666; font-size: 14px; margin-bottom: 20px;">
                Cadastre-se para começar a vender. Seu WhatsApp será seu login.
            </p>
            
            <form method="POST">
                <div style="margin-bottom: 15px;">
                    <label style="display:block; margin-bottom: 5px; font-size: 14px; font-weight: bold;">Nome Completo:</label>
                    <input type="text" name="nome" placeholder="Ex: João Silva" required 
                           style="width:100%; padding:12px; border-radius:8px; border:1px solid #ddd; box-sizing:border-box; font-size: 16px;">
                </div>

                <div style="margin-bottom: 15px;">
                    <label style="display:block; margin-bottom: 5px; font-size: 14px; font-weight: bold;">WhatsApp (Login):</label>
                    <input type="tel" id="telefone_cad" name="telefone" placeholder="(00) 00000-0000" required 
                           style="width:100%; padding:12px; border-radius:8px; border:1px solid #ddd; box-sizing:border-box; font-size: 16px;">
                </div>

                <div style="margin-bottom: 15px;">
                    <label style="display:block; margin-bottom: 5px; font-size: 14px; font-weight: bold;">E-mail:</label>
                    <input type="email" name="email" placeholder="seu@email.com" required 
                           style="width:100%; padding:12px; border-radius:8px; border:1px solid #ddd; box-sizing:border-box; font-size: 16px;">
                </div>

                <div style="margin-bottom: 20px;">
                    <label style="display:block; margin-bottom: 5px; font-size: 14px; font-weight: bold;">Crie uma Senha:</label>
                    <input type="password" name="senha" placeholder="Mínimo 6 caracteres" required 
                           style="width:100%; padding:12px; border-radius:8px; border:1px solid #ddd; box-sizing:border-box; font-size: 16px;">
                </div>

                <button type="submit" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:10px; font-weight:bold; font-size: 16px; cursor: pointer;">
                    Finalizar e Acessar Painel
                </button>
            </form>
            
            <p style="text-align:center; margin-top: 20px;">
                <a href="/login_funcionario" style="color: #1a73e8; text-decoration: none; font-size: 14px;">Já tenho conta? Fazer Login</a>
            </p>
        </div>

        <script>
            // Máscara para o telefone
            document.getElementById('telefone_cad').addEventListener('input', (e) => {{
                let x = e.target.value.replace(/\D/g, '').match(/(\d{{0,2}})(\d{{0,5}})(\d{{0,4}})/);
                e.target.value = !x[2] ? x[1] : '(' + x[1] + ') ' + x[2] + (x[3] ? '-' + x[3] : '');
            }});
        </script>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)