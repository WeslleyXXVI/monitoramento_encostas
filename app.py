import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import paho.mqtt.client as mqtt
import json
import ssl
import certifi

# Configurações MQTT
MQTT_BROKER = "e66b9d6c631847079aa74758720c6fbe.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_TOPIC = "sensores/dados"
MQTT_USERNAME = "weslley.almeida"
MQTT_PASSWORD = "Naruto12!"

# Configuração do Flask
app = Flask(__name__)

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

# Criar a tabela 'sensores' se não existir
with app.app_context():
    db.create_all()

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

# Rotas da aplicação Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sensores')
def sensores():
    # Recuperar os dados dos sensores do banco de dados
    dados = SensorData.query.order_by(SensorData.id.desc()).limit(10).all()
    return render_template('sensores.html', dados=dados)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
