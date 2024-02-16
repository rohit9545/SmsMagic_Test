from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='company', lazy=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

class ClientUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)


@app.route('/users', methods=['GET'])
def list_users():
    username = request.args.get('username')
    if username:
        users = User.query.filter_by(username=username).all()
    else:
        users = User.query.all()
    return jsonify([user.username for user in users])

@app.route('/users', methods=['PUT'])
def update_user():
    data = request.get_json()
    username = data.get('username')
    new_username = data.get('new_username')
    if not username or not new_username:
        return jsonify({'error': 'Both username and new_username are required'}), 400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    user.username = new_username
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/clients', methods=['POST'])
def create_client():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    company_id = data.get('company_id')

    if not all([name, email, phone, company_id]):
        return jsonify({'error': 'Incomplete data provided'}), 400

    if Client.query.filter_by(email=email).first():
        return jsonify({'error': 'Client with this email already exists'}), 400

    client = Client(name=name, email=email, phone=phone, company_id=company_id)
    db.session.add(client)
    try:
        db.session.commit()
        return jsonify({'message': 'Client created successfully'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Company not found'}), 404

@app.route('/clients/<int:client_id>', methods=['PATCH'])
def update_client(client_id):
    data = request.get_json()
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    for key, value in data.items():
        setattr(client, key, value)
    db.session.commit()
    return jsonify({'message': 'Client updated successfully'})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
