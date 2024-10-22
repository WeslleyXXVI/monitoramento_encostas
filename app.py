"""import os
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

# Rota para a página principal
@app.route('/')
def index():
    if 'usuario' in session:
        ultimo_dado = SensorData.query.order_by(SensorData.id.desc()).first()
        return render_template('index.html', usuario=session['usuario'], ultimo_dado=ultimo_dado)
    else:
        return redirect(url_for('login'))

#ROTA DE TESTE
# **Nova Rota: Fornece dados para gráficos e última leitura**
@app.route('/dados-sensores')
def dados_sensores():
    if 'usuario' in session:
        # Buscar o último dado dos sensores
        ultimo_dado = SensorData.query.order_by(SensorData.id.desc()).first()

        # Buscar as últimas 30 leituras para os gráficos
        ultimas_leituras = SensorData.query.order_by(SensorData.id.desc()).limit(30).all()[::-1]

        # Preparar os dados para JSON
        dados = {
            "ultimo_dado": {
                "data_hora": ultimo_dado.data_hora,
                "umidade": ultimo_dado.umidade,
                "vibracao": ultimo_dado.vibracao,
                "deslocamento_x": ultimo_dado.deslocamento_x,
                "deslocamento_y": ultimo_dado.deslocamento_y,
                "deslocamento_z": ultimo_dado.deslocamento_z
            },
            "graficos": {
                "datas": [leitura.data_hora for leitura in ultimas_leituras],
                "umidades": [leitura.umidade for leitura in ultimas_leituras],
                "vibracoes": [leitura.vibracao for leitura in ultimas_leituras],
                "deslocamentoX": [leitura.deslocamento_x for leitura in ultimas_leituras],
                "deslocamentoY": [leitura.deslocamento_y for leitura in ultimas_leituras],
                "deslocamentoZ": [leitura.deslocamento_z for leitura in ultimas_leituras]
            }
        }

        return jsonify(dados)
    else:
        return jsonify({"error": "Usuário não autenticado"}), 401

@app.route('/dados-sensores')
def dados_sensores():
    # Recuperar as últimas 30 leituras do banco de dados
    dados = SensorData.query.order_by(SensorData.id.desc()).limit(30).all()
    dados.reverse()  # Reverter para exibir em ordem cronológica

    # Preparar dados para o gráfico
    chart_data = {
        "datas": [d.data_hora for d in dados],
        "umidades": [d.umidade for d in dados],
        "vibracoes": [d.vibracao for d in dados],
        "deslocamentoX": [d.deslocamento_x for d in dados],
        "deslocamentoY": [d.deslocamento_y for d in dados],
        "deslocamentoZ": [d.deslocamento_z for d in dados],
    }

    # Preparar último dado para exibição no card
    ultimo_dado = {
        "data_hora": dados[-1].data_hora,
        "umidade": dados[-1].umidade,
        "vibracao": dados[-1].vibracao,
        "deslocamento_x": dados[-1].deslocamento_x,
        "deslocamento_y": dados[-1].deslocamento_y,
        "deslocamento_z": dados[-1].deslocamento_z,
    }

    return jsonify({"graficos": chart_data, "ultimo_dado": ultimo_dado})

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
    if not ultimos_dados:
        return jsonify({"datas": [], "umidades": [], "vibracoes": [], "deslocamentoX": [], "deslocamentoY": [], "deslocamentoZ": []})
    
    chart_data = {
        "datas": [d.data_hora for d in reversed(ultimos_dados)],
        "umidades": [d.umidade for d in reversed(ultimos_dados)],
        "vibracoes": [d.vibracao for d in reversed(ultimos_dados)],
        "deslocamentoX": [d.deslocamento_x for d in reversed(ultimos_dados)],
        "deslocamentoY": [d.deslocamento_y for d in reversed(ultimos_dados)],
        "deslocamentoZ": [d.deslocamento_z for d in reversed(ultimos_dados)],
    }
    return jsonify(chart_data)

#TESTE COM ROTA QUE O RONALDO ADICIONOU
@app.route('/dados_graficos')
def dados_graficos():
    # Endpoint para fornecer dados via AJAX para atualização dos gráficos
    chart_data = {
        'datas': ['2024-10-18 14:00', '2024-10-18 14:05', '2024-10-18 14:10'],
        'umidades': [50, 55, 60],
        'vibracoes': [115, 120, 115],
        'deslocamentoX': [4, 5, 6],
        'deslocamentoY': [9, 10, 11],
        'deslocamentoZ': [14, 15, 16]
    }
    return jsonify(chart_data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)"""

import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import paho.mqtt.client as mqtt
from flask_session import Session
import hashlib
import ssl
import json
import certifi
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configurações MQTT
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT', '8883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mysecretkey')

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuração do banco de dados PostgreSQL (Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Função para hash de senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Modelos de banco de dados usando SQLAlchemy

class SensorData(db.Model):
    __tablename__ = 'sensores'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    umidade = db.Column(db.Float, nullable=False)
    vibracao = db.Column(db.Float, nullable=False)
    deslocamento_x = db.Column(db.Float, nullable=False)
    deslocamento_y = db.Column(db.Float, nullable=False)
    deslocamento_z = db.Column(db.Float, nullable=False)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    senha = db.Column(db.String(256), nullable=False)

# Criar as tabelas se não existirem
with app.app_context():
    db.create_all()

# Função para verificar se o usuário existe no banco de dados
def usuario_existe(email):
    return Usuario.query.filter_by(email=email).first()

# Função para criar usuário
def criar_usuario(nome, email, senha):
    hashed_password = hash_password(senha)
    novo_usuario = Usuario(nome=nome, email=email, senha=hashed_password)
    db.session.add(novo_usuario)
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

        # Converter a string data_hora em objeto datetime
        data_hora_str = payload["data_hora"]
        # Ajuste o formato da data conforme necessário
        data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S')

        # Criar um novo registro de dados no banco de dados
        sensor_data = SensorData(
            data_hora=data_hora,
            umidade=float(payload["umidade"]),
            vibracao=float(payload["vibracao"]),
            deslocamento_x=float(payload["deslocamento_x"]),
            deslocamento_y=float(payload["deslocamento_y"]),
            deslocamento_z=float(payload["deslocamento_z"])
        )

        # Salvar os dados no banco de dados
        db.session.add(sensor_data)
        db.session.commit()
        print("Dados armazenados no banco de dados.")

    except Exception as e:
        print(f"Erro ao processar a mensagem: {e}")
        import traceback
        traceback.print_exc()

# Função para buscar dados de sensores do banco de dados
def buscar_dados_sensores():
    return SensorData.query.order_by(SensorData.data_hora.asc()).all()

# Função para buscar o último dado
def buscar_ultimo_dado():
    return SensorData.query.order_by(SensorData.data_hora.desc()).first()

def atualizar_data_hora():
    with app.app_context():
        sensores = SensorData.query.all()
        for sensor in sensores:
            if isinstance(sensor.data_hora, str):
                try:
                    # Tente converter a string em datetime
                    sensor.data_hora = datetime.strptime(sensor.data_hora, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Tentar outro formato se necessário
                    try:
                        sensor.data_hora = datetime.strptime(sensor.data_hora, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        print(f"Formato de data inválido para o registro ID {sensor.id}: {sensor.data_hora}")
                        continue  # Pula para o próximo registro
                db.session.add(sensor)
        db.session.commit()
        print("Atualização de data_hora concluída.")


# Rota para login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("password")
        if not email or not senha:
            return render_template("login.html", error="Preencha todos os campos.")
        usuario = usuario_existe(email)
        if usuario:
            if usuario.senha == hash_password(senha):
                session["usuario"] = email
                return redirect(url_for("index"))
            else:
                return render_template("login.html", error="Senha incorreta")
        else:
            return render_template("login.html", error="Usuário não existe. Deseja se cadastrar?")
    return render_template("login.html")

# Rota para cadastro
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if not nome or not email or not senha or not confirm_password:
            error = "Todos os campos são obrigatórios."
            return render_template("cadastro.html", error=error)
        if senha != confirm_password:
            error = "As senhas não coincidem."
            return render_template("cadastro.html", error=error)
        if usuario_existe(email):
            error = "Este e-mail já está cadastrado."
            return render_template("cadastro.html", error=error)
        criar_usuario(nome, email, senha)
        return redirect(url_for("login"))
    return render_template("cadastro.html")

# Rota para receber dados dos sensores
@app.route("/sensores", methods=["POST"])
def recebe_data():
    umidade = request.form.get('umidade')
    vibracao = request.form.get('vibracao')
    deslocamento_x = request.form.get('deslocamento_x')
    deslocamento_y = request.form.get('deslocamento_y')
    deslocamento_z = request.form.get('deslocamento_z')
    if umidade and vibracao and deslocamento_x and deslocamento_y and deslocamento_z:
        try:
            umidade = float(umidade)
            vibracao = float(vibracao)
            deslocamento_x = float(deslocamento_x)
            deslocamento_y = float(deslocamento_y)
            deslocamento_z = float(deslocamento_z)
            data_hora = datetime.now()
            novo_sensor = SensorData(
                data_hora=data_hora,
                umidade=umidade,
                vibracao=vibracao,
                deslocamento_x=deslocamento_x,
                deslocamento_y=deslocamento_y,
                deslocamento_z=deslocamento_z
            )
            db.session.add(novo_sensor)
            db.session.commit()
            return 'Dados obtidos e armazenados com sucesso', 200
        except ValueError as e:
            return f'Erro na conversão dos dados: {e}', 400
        except Exception as e:
            return f'Erro ao inserir dados: {e}', 500
    else:
        return 'Parâmetro(s) ausente(s)', 400

# Rota para página principal
@app.route('/')
def index():
    ultimo_dado = buscar_ultimo_dado()
    # Dados para os gráficos
    sensores = SensorData.query.order_by(SensorData.data_hora.desc()).limit(50).all()
    sensores.reverse()  # Para colocar em ordem ascendente

    chart_data = {
        'datas': [sensor.data_hora.strftime('%Y-%m-%d %H:%M:%S') for sensor in sensores],
        'umidades': [sensor.umidade for sensor in sensores],
        'vibracoes': [sensor.vibracao for sensor in sensores],
        'deslocamentoX': [sensor.deslocamento_x for sensor in sensores],
        'deslocamentoY': [sensor.deslocamento_y for sensor in sensores],
        'deslocamentoZ': [sensor.deslocamento_z for sensor in sensores]
    }

    return render_template('index.html', ultimo_dado=ultimo_dado, chart_data=chart_data)

@app.route('/dados_graficos')
def dados_graficos():
    sensores = SensorData.query.order_by(SensorData.data_hora.desc()).limit(50).all()
    sensores.reverse()  # Para colocar em ordem ascendente

    chart_data = {
        'datas': [sensor.data_hora.strftime('%Y-%m-%d %H:%M:%S') for sensor in sensores],
        'umidades': [sensor.umidade for sensor in sensores],
        'vibracoes': [sensor.vibracao for sensor in sensores],
        'deslocamentoX': [sensor.deslocamento_x for sensor in sensores],
        'deslocamentoY': [sensor.deslocamento_y for sensor in sensores],
        'deslocamentoZ': [sensor.deslocamento_z for sensor in sensores]
    }
    return jsonify(chart_data)

# Rota para logout
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    # Inicializar o banco de dados
    with app.app_context():
        db.create_all()

        # Atualizar os registros existentes
        atualizar_data_hora()

    # Configurar o cliente MQTT
    mqtt_client = mqtt.Client("PostgreSQL_Subscriber")
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.tls_set(certifi.where(), cert_reqs=ssl.CERT_NONE)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Conectar ao broker MQTT e iniciar o loop
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # Obter a porta do ambiente ou usar 5000 como padrão
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



