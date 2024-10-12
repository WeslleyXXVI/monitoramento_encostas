import paho.mqtt.client as mqtt
import random
import time
import json
import ssl
import os

# Configurações do broker MQTT no HiveMQ Cloud
MQTT_BROKER = "e66b9d6c631847079aa74758720c6fbe.s1.eu.hivemq.cloud"
MQTT_PORT = 8883  # Porta para conexão TLS/SSL
MQTT_TOPIC = "sensores/dados"
MQTT_USERNAME = "weslley.almeida"  # Seu nome de usuário do HiveMQ Cloud
MQTT_PASSWORD = "Naruto12!"  # Sua senha do HiveMQ Cloud

# Função callback quando a conexão é estabelecida
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado com sucesso ao broker MQTT (código {rc})")
    else:
        print(f"Falha na conexão com o broker (código {rc})")

# Configurar o cliente MQTT
client = mqtt.Client("SimuladorESP32")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
#client.tls_set(ca_certs="C:\\Users\\Weslley\\Desktop\\monitoramento-encostas\\DigiCertGlobalRootCA.pem", cert_reqs=ssl.CERT_REQUIRED)
client.tls_set(ca_certs="C:\\Users\\Weslley\\Desktop\\monitoramento-encostas\\DigiCertGlobalRootCA.pem", cert_reqs=ssl.CERT_NONE)

client.on_connect = on_connect

# Conectar ao broker MQTT
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Iniciar o loop do cliente MQTT para manter a conexão e processar as mensagens
client.loop_start()

# Loop de simulação de envio de dados
try:
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
        result = client.publish(MQTT_TOPIC, payload, qos=0)  # Usar QoS 0 para combinar com o Web Client

        
        # Checar o status da publicação
        if result.rc == 0:
            print(f"Dados enviados: {payload}")
        else:
            print(f"Erro ao enviar dados: {result.rc}")

        # Esperar 10 segundos antes de enviar novamente
        time.sleep(10)
        
except KeyboardInterrupt:
    print("Desconectando...")
    client.loop_stop()
    client.disconnect()
