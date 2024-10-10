from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configurações do banco de dados usando variáveis de ambiente
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = os.environ.get('DB_PORT', 5432)

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String(50))
    umidade = db.Column(db.Float)
    vibracao = db.Column(db.Float)
    inclinacao_x = db.Column(db.Float)
    inclinacao_y = db.Column(db.Float)
    inclinacao_z = db.Column(db.Float)

db.create_all()

@app.route('/sensores', methods=['POST'])
def receber_dados():
    dados = request.json
    novo_dado = SensorData(
        timestamp=dados['dataHora'],
        umidade=dados['umidade'],
        vibracao=dados['vibracao'],
        inclinacao_x=dados['ax'],
        inclinacao_y=dados['ay'],
        inclinacao_z=dados['az']
    )
    db.session.add(novo_dado)
    db.session.commit()
    return jsonify({"message": "Dados recebidos com sucesso!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
