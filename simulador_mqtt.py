import paho.mqtt.client as mqtt
import random
import time
import json

# Configuração do broker MQTT
mqtt_server = "broker.mqtt-dashboard.com"  # Broker público para testes, você pode usar um próprio se necessário
mqtt_port = 1883
mqtt_topic = "sensores/dados"

# Callback para quando a conexão for estabelecida
def on_connect(client, userdata, flags, rc):
    print(f"Conectado ao broker MQTT com código {rc}")

# Configurar o cliente MQTT
client = mqtt.Client("SimuladorESP32")
client.on_connect = on_connect

# Conectar ao broker MQTT
client.connect(mqtt_server, mqtt_port, 60)

# Loop de simulação de envio de dados
while True:
    # Gerar dados aleatórios para simulação
    data = {
        "data_hora": time.strftime("%Y-%m-%d %H:%M:%S"),
        "umidade": round(random.uniform(10.0, 50.0), 2),
        "vibracao": round(random.uniform(0.1, 5.0), 2),
        "deslocamento_x": round(random.uniform(-1.0, 1.0), 2),
        "deslocamento_y": round(random.uniform(-1.0, 1.0), 2),
        "deslocamento_z": round(random.uniform(-1.0, 1.0), 2),
    }

    # Converter para JSON e enviar via MQTT
    payload = json.dumps(data)
    client.publish(mqtt_topic, payload)
    print(f"Dados enviados: {payload}")

    # Esperar 10 segundos antes de enviar novamente
    time.sleep(10)