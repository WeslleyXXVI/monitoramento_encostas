import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import paho.mqtt.client as mqtt
import json
import hashlib
import ssl
import certifi

# Configurações MQTT
MQTT_BROKER = os.getenv('MQTT_BROKER', "e66b9d6c631847079aa74758720c6fbe.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', "sensores/dados")
MQTT_USERNAME = os.getenv('MQTT_USERNAME', "weslley.almeida")
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', "Naruto12!")  # Isso deve ser substituído por variáveis de ambiente seguras.

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mysecretkey')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Configuração do banco de dados PostgreSQL (Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:TXhcBjuVGMExFBSJHEgUONIAcwufdKln@junction.proxy.rlwy.net:59480/railway')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o SQLAlchemy
db = SQLAlchemy(app)

# Modelo de dados para a tabela 'sensores'
class SensorData(db.Model):
    __tablename__ = 'sensores'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.String(50))
    umidade = db.Column(db.Float)
    vibracao = db.Column(db.Float)
    deslocamento_x = db.Column(db.Float)
    deslocamento_y = db.Column(db.Float)
    deslocamento_z = db.Column(db.Float)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

# Criar a tabela 'sensores' se não existir
with app.app_context():
    db.create_all()

# Função de Hash de Senhas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Função para Verificar se o Usuário Existe
def usuario_existe(email):
    return Usuario.query.filter_by(email=email).first()

# Função de Criação de Usuário
def criar_usuario(nome, email, password):
    usuario = Usuario(nome=nome, email=email, senha=hash_password(password))
    db.session.add(usuario)
    db.session.commit()

# Função callback quando a conexão MQTT é estabelecida
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao broker MQTT")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Falha na conexão com o broker MQTT. Código: {rc}")

# Função callback quando uma mensagem MQTT é recebida
def on_message(client, userdata, msg):
    try:
        # Decodificar a mensagem recebida
        payload = json.loads(msg.payload)
        print(f"Mensagem recebida: {payload}")

        # Criar um novo registro de dados no banco de dados
        sensor_data = SensorData(
            data_hora=payload["data_hora"],
            umidade=payload["umidade"],
            vibracao=payload["vibracao"],
            deslocamento_x=payload["deslocamento_x"],
            deslocamento_y=payload["deslocamento_y"],
            deslocamento_z=payload["deslocamento_z"]
        )

        # Salvar os dados no banco de dados
        db.session.add(sensor_data)
        db.session.commit()
        print("Dados armazenados no banco de dados.")

    except Exception as e:
        print(f"Erro ao processar a mensagem: {e}")

# Configurar o cliente MQTT
mqtt_client = mqtt.Client("PostgreSQL_Subscriber")
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.tls_set(certifi.where(), cert_reqs=ssl.CERT_NONE)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Conectar ao broker MQTT e iniciar o loop
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# Rotas Flask
#ROTA QUE FUNCIONA
"""@app.route('/')
def index():
    if 'usuario' in session:
        ultimo_dado = SensorData.query.order_by(SensorData.id.desc()).first()
        return render_template('index.html', usuario=session['usuario'], ultimo_dado=ultimo_dado)
    else:
        return redirect(url_for('login'))"""

#ROTA DE TESTE
@app.route('/')
def index():
    if 'usuario' in session:
        # Buscar o último dado dos sensores
        ultimo_dado = SensorData.query.order_by(SensorData.id.desc()).first()

        # Buscar as últimas 30 leituras para os gráficos
        ultimas_leituras = SensorData.query.order_by(SensorData.id.desc()).limit(30).all()[::-1]

        # Preparar os dados para exibir nos gráficos
        datas = [leitura.data_hora for leitura in ultimas_leituras]
        umidades = [leitura.umidade for leitura in ultimas_leituras]
        vibracoes = [leitura.vibracao for leitura in ultimas_leituras]
        deslocamentoX = [leitura.deslocamento_x for leitura in ultimas_leituras]
        deslocamentoY = [leitura.deslocamento_y for leitura in ultimas_leituras]
        deslocamentoZ = [leitura.deslocamento_z for leitura in ultimas_leituras]

        # Converter os dados para JSON para serem usados pelo Chart.js
        chart_data = {
            "datas": datas,
            "umidades": umidades,
            "vibracoes": vibracoes,
            "deslocamentoX": deslocamentoX,
            "deslocamentoY": deslocamentoY,
            "deslocamentoZ": deslocamentoZ
        }

        return render_template('index.html', 
                               usuario=session['usuario'], 
                               ultimo_dado=ultimo_dado, 
                               chart_data=json.dumps(chart_data))
    else:
        return redirect(url_for('login'))

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = usuario_existe(email)
        if usuario and usuario.senha == hash_password(password):
            session['usuario'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Usuário ou senha incorretos")
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('cadastro.html', error="As senhas não coincidem")

        if usuario_existe(email):
            return render_template('cadastro.html', error="Usuário já cadastrado")

        criar_usuario(nome, email, password)
        return redirect(url_for('login'))

    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

# Para receber dados novos do banco
@app.route('/update_data', methods=['GET'])
def update_data():
    ultimos_dados = SensorData.query.order_by(SensorData.id.desc()).limit(30).all()
    chart_data = {
        "datas": [d.data_hora for d in reversed(ultimos_dados)],
        "umidades": [d.umidade for d in reversed(ultimos_dados)],
        "vibracoes": [d.vibracao for d in reversed(ultimos_dados)],
        "deslocamentoX": [d.deslocamento_x for d in reversed(ultimos_dados)],
        "deslocamentoY": [d.deslocamento_y for d in reversed(ultimos_dados)],
        "deslocamentoZ": [d.deslocamento_z for d in reversed(ultimos_dados)],
    }
    return jsonify(chart_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
