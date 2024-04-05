from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta')

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agentName = db.Column(db.String(80), nullable=False)
    nomeFantasia = db.Column(db.String(80), nullable=False)
    cnpj = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    protocol = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(120), nullable=False)
    returnTime = db.Column(db.DateTime, nullable=False)

def parse_datetime(datetime_str):
    try:
        return datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
    except ValueError:
        return None

@app.route('/')
def login():
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'teste' and password == '123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return 'Credenciais inválidas. Por favor, tente novamente.'
    return render_template('login.html')

@app.route('/index')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

@app.route('/submit', methods=['POST'])
def submit():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    try:
        if request.method == 'POST':
            agentName = request.form['agentName']
            nomeFantasia = request.form['nomeFantasia']
            cnpj = request.form['cnpj']
            phone = request.form['phone']
            protocol = request.form['protocol']
            status = request.form['status']
            returnTime_str = request.form['returnTime']
            returnTime = parse_datetime(returnTime_str)

            if returnTime is None:
                return 'Formato de data e hora inválido. Use DD/MM/AAAA HH:MM.'

            new_user = User(agentName=agentName, nomeFantasia=nomeFantasia, cnpj=cnpj,
                            phone=phone, protocol=protocol, status=status, returnTime=returnTime)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('users'))
    except IntegrityError:
        db.session.rollback()
        return 'Erro: já existe um usuário com este CNPJ.'
    except Exception as e:
        return f'Um erro ocorreu ao salvar os dados: {str(e)}'

@app.route('/edit', methods=['POST'])
def edit():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    try:
        if request.method == 'POST':
            agentName = request.form['agentName']
            nomeFantasia = request.form['nomeFantasia']
            cnpj = request.form['cnpj']
            phone = request.form['phone']
            protocol = request.form['protocol']
            status = request.form['status']
            returnTime_str = request.form['returnTime']
            returnTime = parse_datetime(returnTime_str)

            if returnTime is None:
                return 'Formato de data e hora inválido. Use DD/MM/AAAA HH:MM.'

            existing_user = User.query.filter_by(cnpj=cnpj).first()
            if existing_user:
                existing_user.agentName = agentName
                existing_user.nomeFantasia = nomeFantasia
                existing_user.phone = phone
                existing_user.protocol = protocol
                existing_user.status = status
                existing_user.returnTime = returnTime
                db.session.commit()

            return redirect(url_for('users'))
    except Exception as e:
        db.session.rollback()
        return f'Um erro ocorreu ao atualizar os dados: {str(e)}'

@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    
    # Obtendo a data e hora atual
    now = datetime.now()

    # Obtendo todos os usuários e classificando pelo tempo de retorno do mais antigo para o mais novo
    users = User.query.order_by(User.returnTime.asc()).all()

    return render_template('users.html', users=users, now=now)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
