import os
import paho.mqtt.client as mqtt
import psycopg2
import json

# Configurações do banco de dados PostgreSQL no Railway
DATABASE_URL = "postgresql://postgres:TXhcBjuVGMExFBSJHEgUONIAcwufdKln@junction.proxy.rlwy.net:59480/railway"

# Conectar ao banco de dados PostgreSQL
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Definir a tabela no banco de dados (caso ainda não exista)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensores (
        id SERIAL PRIMARY KEY,
        data_hora TIMESTAMP,
        umidade FLOAT,
        vibracao FLOAT,
        deslocamento_x FLOAT,
        deslocamento_y FLOAT,
        deslocamento_z FLOAT
    );
""")
conn.commit()

# Callback para quando a conexão for estabelecida
def on_connect(client, userdata, flags, rc):
    print(f"Conectado ao broker MQTT com código {rc}")
    # Se inscrever no tópico 'sensores/dados'
    client.subscribe("sensores/dados")

# Callback para quando uma mensagem é recebida
def on_message(client, userdata, msg):
    print(f"Mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")
    try:
        # Decodificar a mensagem JSON
        data = json.loads(msg.payload.decode())

        # Preparar o comando SQL para inserir os dados no banco de dados
        insert_query = """
            INSERT INTO sensores (data_hora, umidade, vibracao, deslocamento_x, deslocamento_y, deslocamento_z)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        values = (
            data['data_hora'],
            data['umidade'],
            data['vibracao'],
            data['deslocamento_x'],
            data['deslocamento_y'],
            data['deslocamento_z']
        )

        # Executar o comando SQL e inserir os dados no banco de dados
        cursor.execute(insert_query, values)
        conn.commit()
        print("Dados inseridos no banco de dados com sucesso!")

    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")

# Configurar o cliente MQTT
client = mqtt.Client("PostgresInserter")
client.on_connect = on_connect
client.on_message = on_message

# Conectar ao broker MQTT
client.connect("broker.mqtt-dashboard.com", 1883, 60)

# Iniciar o loop do cliente MQTT para escutar o tópico
client.loop_forever()
