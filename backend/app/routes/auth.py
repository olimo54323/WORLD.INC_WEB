from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user import User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def validate_email(email):
    """Walidacja formatu email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Walidacja hasła - minimum 6 znaków"""
    return len(password) >= 6

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Strona logowania"""
    if request.method == 'POST':
        if request.is_json:
            # API endpoint
            data = request.get_json()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
        else:
            # Form submission
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
        
        # Walidacja danych
        if not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email i hasło są wymagane'}), 400
            flash('Email i hasło są wymagane', 'danger')
            return render_template('auth/login.html')
        
        # Sprawdzenie użytkownika
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active:
            # Logowanie udane
            session['user_id'] = user.id
            session['username'] = user.username
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': f'Witamy z powrotem, {user.username}!',
                    'user': user.to_dict()
                })
            
            flash(f'Witamy z powrotem, {user.username}! Gotowy na nową misję?', 'success')
            return redirect(url_for('game'))
        else:
            # Błędne dane lub nieaktywne konto
            if request.is_json:
                return jsonify({'success': False, 'message': 'Nieprawidłowy email lub hasło'}), 401
            flash('Nieprawidłowy email lub hasło', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Strona rejestracji"""
    if request.method == 'POST':
        if request.is_json:
            # API endpoint
            data = request.get_json()
            username = data.get('username', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
        else:
            # Form submission
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
        
        # Walidacja danych
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Nazwa użytkownika musi mieć co najmniej 3 znaki')
        
        if not email or not validate_email(email):
            errors.append('Podaj prawidłowy adres email')
        
        if not password or not validate_password(password):
            errors.append('Hasło musi mieć co najmniej 6 znaków')
        
        # Sprawdzenie unikalności
        if User.query.filter_by(username=username).first():
            errors.append('Ta nazwa użytkownika jest już zajęta')
        
        if User.query.filter_by(email=email).first():
            errors.append('Ten email jest już zarejestrowany')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'message': '; '.join(errors)}), 400
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        try:
            # Tworzenie nowego użytkownika
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Automatyczne logowanie po rejestracji
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': f'Konto utworzone! Witamy w World.Inc, {username}!',
                    'user': new_user.to_dict()
                })
            
            flash(f'Konto utworzone! Witamy w World.Inc, {username}!', 'success')
            return redirect(url_for('game'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': 'Błąd podczas tworzenia konta'}), 500
            flash('Błąd podczas tworzenia konta. Spróbuj ponownie.', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Wylogowanie"""
    username = session.get('username', 'Agent')
    session.clear()
    
    if request.is_json:
        return jsonify({'success': True, 'message': f'Do zobaczenia, {username}!'})
    
    flash(f'Do zobaczenia, {username}! Dziękujemy za służbę.', 'info')
    return redirect(url_for('home'))

@auth_bp.route('/profile')
def profile():
    """Profil użytkownika (wymaga logowania)"""
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Wymagane logowanie'}), 401
        flash('Musisz się zalogować aby zobaczyć profil', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Użytkownik nie istnieje'}), 404
        flash('Użytkownik nie istnieje', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.is_json:
        return jsonify({'success': True, 'user': user.to_dict()})
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/check-auth')
def check_auth():
    """API endpoint do sprawdzania statusu logowania"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': user.to_dict()
            })
    
    return jsonify({'authenticated': False})

@auth_bp.route('/delete-account', methods=['GET', 'POST'])
def delete_account():
    """Usuwanie konta użytkownika"""
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({'success': False, 'message': 'Wymagane logowanie'}), 401
        flash('Musisz się zalogować aby usunąć konto', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        if request.is_json:
            return jsonify({'success': False, 'message': 'Użytkownik nie istnieje'}), 404
        flash('Użytkownik nie istnieje', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            password = data.get('password', '')
            confirmation = data.get('confirmation', '')
        else:
            password = request.form.get('password', '')
            confirmation = request.form.get('confirmation', '')
        
        # Sprawdź hasło
        if not password or not user.check_password(password):
            if request.is_json:
                return jsonify({'success': False, 'message': 'Nieprawidłowe hasło'}), 400
            flash('Nieprawidłowe hasło', 'danger')
            return render_template('auth/delete_account.html', user=user)
        
        # Sprawdź potwierdzenie
        if confirmation != 'USUŃ MOJE KONTO':
            if request.is_json:
                return jsonify({'success': False, 'message': 'Nieprawidłowe potwierdzenie'}), 400
            flash('Musisz wpisać dokładnie: USUŃ MOJE KONTO', 'danger')
            return render_template('auth/delete_account.html', user=user)
        
        try:
            # Usuń wszystkie powiązane dane
            from app.models.minigames import GameSession
            
            # Usuń sesje gier
            GameSession.query.filter_by(user_id=user.id).delete()
            
            # Usuń użytkownika
            username = user.username
            db.session.delete(user)
            db.session.commit()
            
            # Wyloguj
            session.clear()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': f'Konto {username} zostało całkowicie usunięte'
                })
            
            flash(f'Konto {username} zostało całkowicie usunięte. Żegnamy, agencie!', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'message': 'Błąd podczas usuwania konta'}), 500
            flash('Błąd podczas usuwania konta. Spróbuj ponownie.', 'danger')
    
    return render_template('auth/delete_account.html', user=user)

@auth_bp.route('/check-password', methods=['POST'])
def check_password():
    """API endpoint do sprawdzania hasła"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Wymagane logowanie'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False, 'message': 'Użytkownik nie istnieje'}), 404
    
    data = request.get_json()
    password = data.get('password', '')
    
    if user.check_password(password):
        return jsonify({'success': True, 'message': 'Hasło poprawne'})
    else:
        return jsonify({'success': False, 'message': 'Nieprawidłowe hasło'}), 400