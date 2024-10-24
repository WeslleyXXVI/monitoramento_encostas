import os
from flask_migrate import Migrate, upgrade
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
from flask_cors import CORS
from functools import wraps

load_dotenv()

# Configurações MQTT
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT', '8883'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'mysecretkey')

# Configurações de Sessão
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuração do banco de dados PostgreSQL (Railway)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Inicializar o Flask-Migrate

# Função para hash de senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Dicionário para armazenar as últimas 50 leituras
historico_leituras = []

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

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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

"""# Função callback quando uma mensagem MQTT é recebida
def on_message(client, userdata, msg):
    try:
        # Decodificar a mensagem recebida
        payload = json.loads(msg.payload)
        print(f"Mensagem recebida: {payload}")

        # Converter a string data_hora em objeto datetime
        data_hora_str = payload.get("data_hora", None)
        if data_hora_str:
            try:
                data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    print(f"Formato de data inválido na mensagem MQTT: {data_hora_str}")
                    data_hora = datetime.utcnow()
        else:
            data_hora = datetime.utcnow()

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
        traceback.print_exc()"""

# Função callback quando uma mensagem MQTT é recebida
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode('utf-8')
        dados = json.loads(payload)
        
        # Converter a string data_hora em objeto datetime
        data_hora_str = dados.get("data_hora", None)
        if data_hora_str:
            try:
                data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    print(f"Formato de data inválido na mensagem MQTT: {data_hora_str}")
                    data_hora = datetime.utcnow()
        else:
            data_hora = datetime.utcnow()
        
        # Criar um objeto SensorData
        leitura = SensorData(
            data_hora=data_hora,
            umidade=float(dados["umidade"]),
            vibracao=float(dados["vibracao"]),
            deslocamento_x=float(dados["deslocamento_x"]),
            deslocamento_y=float(dados["deslocamento_y"]),
            deslocamento_z=float(dados["deslocamento_z"])
        )
        
        # Adicionar ao histórico de leituras
        historico_leituras.append({
            "data_hora": leitura.data_hora,
            "umidade": leitura.umidade,
            "vibracao": leitura.vibracao,
            "deslocamento_x": leitura.deslocamento_x,
            "deslocamento_y": leitura.deslocamento_y,
            "deslocamento_z": leitura.deslocamento_z
        })
        
        # Limitar o histórico a 50 leituras
        if len(historico_leituras) > 50:
            historico_leituras.pop(0)
        
        # Salvar no banco de dados
        db.session.add(leitura)
        db.session.commit()
        
        print("Leitura adicionada ao histórico e salva no banco de dados.")
    except Exception as e:
        print(f"Erro ao processar a mensagem: {e}")
        import traceback
        traceback.print_exc()

# Rota para login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("password")
        if not email ou não senha:
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

# Rota para logout
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

# Rota para página principal
@app.route("/index")
@login_required
def index():
    ultimo_dado = historico_leituras[-1] if historico_leituras else None
    return render_template('index.html', ultimo_dado=ultimo_dado, leituras=historico_leituras)

# Rota para dados dos gráficos
@app.route('/dados_graficos')
@login_required
def dados_graficos():
    chart_data = {
        'datas': [leitura["data_hora"].strftime('%Y-%m-%d %H:%M:%S') for leitura in historico_leituras],
        'umidades': [leitura["umidade"] for leitura in historico_leituras],
        'vibracoes': [leitura["vibracao"] for leitura in historico_leituras],
        'deslocamentoX': [leitura["deslocamento_x"] for leitura in historico_leituras],
        'deslocamentoY': [leitura["deslocamento_y"] for leitura in historico_leituras],
        'deslocamentoZ': [leitura["deslocamento_z"] for leitura in historico_leituras]
    }
    return jsonify(chart_data)

# Função para atualizar data_hora (opcional se não for necessário)
def atualizar_data_hora():
    print("Iniciando atualização de data_hora")
    with app.app_context():
        sensores = SensorData.query.all()
        for sensor in sensores:
            if isinstance(sensor.data_hora, str):
                try:
                    # Tente converter a string em datetime
                    sensor.data_hora = datetime.strptime(sensor.data_hora, '%Y-%m-%d %H:%M:%S')
                    db.session.add(sensor)
                except ValueError:
                    try:
                        sensor.data_hora = datetime.strptime(sensor.data_hora, '%Y-%m-%d %H:%M:%S.%f')
                        db.session.add(sensor)
                    except ValueError:
                        print(f"Formato de data inválido para o registro ID {sensor.id}: {sensor.data_hora}")
                        continue
        db.session.commit()
        print("Atualização de data_hora concluída.")

# Rota raiz redireciona para login ou index com base na sessão
@app.route('/')
def home():
    if 'usuario' in session:
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

if __name__ == "__main__":
    # Inicializar o banco de dados e aplicar migrações
    with app.app_context():
        try:
            upgrade()
            atualizar_data_hora()
            print("Migrações aplicadas com sucesso.")
        except Exception as e:
            print(f"Erro ao aplicar migrações: {e}")
    
    # Configurar o cliente MQTT
    mqtt_client = mqtt.Client("PostgreSQL_Subscriber")
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.tls_set(certifi.where(), cert_reqs=ssl.CERT_NONE)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Conectar ao broker MQTT e iniciar o loop
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Erro ao conectar ao broker MQTT: {e}")
    
    # Obter a porta do ambiente ou usar 5000 como padrão
    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Erro ao iniciar o servidor Flask: {e}")
