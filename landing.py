from flask import Flask, render_template_string

app = Flask(__name__)

# Reutilizando o seu estilo base para manter a identidade
BASE_STYLE = '''
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TicketZap | Bem-vindo</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 0; }
        .hero { padding: 80px 20px; text-align: center; background: white; border-bottom: 5px solid #1a73e8; }
        .btn { display: inline-block; padding: 15px 30px; border-radius: 10px; text-decoration: none; font-weight: bold; transition: 0.3s; }
        .btn-primary { background: #1a73e8; color: white; }
        .feature-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 50px 20px; }
        .feature-card { background: white; padding: 30px; border-radius: 20px; width: 280px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); text-align: center; }
        .icon { font-size: 40px; margin-bottom: 15px; display: block; }
    </style>
</head>
'''

@app.route('/')
def home():
    return render_template_string(f'''
        {BASE_STYLE}
        <div class="hero">
            <h1 style="font-size: 40px; color: #1a1a1a;">🚀 TicketZap</h1>
            <p style="font-size: 20px; color: #666; max-width: 600px; margin: 20px auto;">
                A plataforma definitiva para promoters venderem convites via WhatsApp com total segurança e controle.
            </p>
            <div style="margin-top: 40px;">
                <a href="#" class="btn btn-primary">Começar Agora</a>
            </div>
        </div>

        <div class="feature-grid">
            <div class="feature-card">
                <span class="icon">⚡</span>
                <h3>Agilidade</h3>
                <p>Gere QR Codes em segundos e envie direto para o cliente.</p>
            </div>
            <div class="feature-card">
                <span class="icon">🔍</span>
                <h3>Transparência</h3>
                <p>Relatórios detalhados de cada venda e entrada no evento.</p>
            </div>
            <div class="feature-card">
                <span class="icon">📱</span>
                <h3>Portaria na Mão</h3>
                <p>Valide ingressos usando apenas a câmera do seu celular.</p>
            </div>
        </div>

        <footer style="text-align: center; padding: 30px; color: #aaa;">
            © 2026 TicketZap - O Futuro dos Eventos
        </footer>
    ''')

if __name__ == '__main__':
    app.run(debug=True, port=5001) # Usando porta 5001 para não dar conflito com o outro