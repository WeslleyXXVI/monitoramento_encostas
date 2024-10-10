import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Definir a URL completa do banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:TXhcBjuVGMExFBSJHEgUONIAcwufdKln@junction.proxy.rlwy.net:59480/railway"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o SQLAlchemy
db = SQLAlchemy(app)

# Definir o modelo da tabela 'sensores'
class SensorData(db.Model):
    __tablename__ = 'sensores'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=db.func.current_timestamp())
    vibracao = db.Column(db.Float)
    umidade = db.Column(db.Float)
    deslocamento_x = db.Column(db.Float)
    deslocamento_y = db.Column(db.Float)
    deslocamento_z = db.Column(db.Float)

# Criar a tabela 'sensores' se não existir
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
