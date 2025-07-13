from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.extensions import db
from app.models.user import User
from app.models.minigames import GameSession, VirusAlert, SpaceDefence, WifiGuard, Leaderboard
import json
from datetime import datetime

minigames_bp = Blueprint('minigames', __name__, url_prefix='/minigames')

def require_login():
    """Sprawdza czy użytkownik jest zalogowany"""
    if 'user_id' not in session:
        return False
    user = User.query.get(session['user_id'])
    return user and user.is_active

@minigames_bp.route('/')
def index():
    """Strona główna minigier"""
    if not require_login():
        flash('Musisz się zalogować aby grać w minigry', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    user_stats = Leaderboard.get_user_stats(user.id)
    
    return render_template('minigames/index.html', user=user, stats=user_stats)

@minigames_bp.route('/virus-alert')
def virus_alert():
    """Strona gry Virus Alert"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    difficulty = request.args.get('difficulty', 1, type=int)
    difficulty = max(1, min(difficulty, 5))  # Ograniczenie 1-5
    
    game = VirusAlert(difficulty)
    config = game.get_game_config()
    
    return render_template('minigames/virus_alert.html', 
                         game_config=config, 
                         user=User.query.get(session['user_id']))

@minigames_bp.route('/space-defence')
def space_defence():
    """Strona gry Space Defence"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    difficulty = request.args.get('difficulty', 1, type=int)
    difficulty = max(1, min(difficulty, 5))
    
    game = SpaceDefence(difficulty)
    config = game.get_game_config()
    
    return render_template('minigames/space_defence.html', 
                         game_config=config, 
                         user=User.query.get(session['user_id']))

@minigames_bp.route('/wifi-guard')
def wifi_guard():
    """Strona gry WiFi Guard"""
    if not require_login():
        return redirect(url_for('auth.login'))
    
    difficulty = request.args.get('difficulty', 1, type=int)
    difficulty = max(1, min(difficulty, 5))
    
    game = WifiGuard(difficulty)
    config = game.get_game_config()
    
    return render_template('minigames/wifi_guard.html', 
                         game_config=config, 
                         user=User.query.get(session['user_id']))

@minigames_bp.route('/api/start-game', methods=['POST'])
def start_game():
    """API endpoint do rozpoczynania gry"""
    if not require_login():
        return jsonify({'error': 'Wymagane logowanie'}), 401
    
    data = request.get_json()
    game_type = data.get('game_type')
    difficulty = data.get('difficulty', 1)
    
    if game_type not in ['virus_alert', 'space_defence', 'wifi_guard']:
        return jsonify({'error': 'Nieprawidłowy typ gry'}), 400
    
    user = User.query.get(session['user_id'])
    
    # Utwórz nową sesję gry
    game_session = GameSession(
        user_id=user.id,
        game_type=game_type,
        game_data=json.dumps({'difficulty': difficulty})
    )
    
    db.session.add(game_session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session_id': game_session.id,
        'message': f'Rozpoczęto grę {game_type}'
    })

@minigames_bp.route('/api/finish-game', methods=['POST'])
def finish_game():
    """API endpoint do kończenia gry"""
    if not require_login():
        return jsonify({'error': 'Wymagane logowanie'}), 401
    
    data = request.get_json()
    session_id = data.get('session_id')
    score = data.get('score', 0)
    game_data = data.get('game_data', {})
    
    game_session = GameSession.query.filter_by(
        id=session_id,
        user_id=session['user_id']
    ).first()
    
    if not game_session:
        return jsonify({'error': 'Sesja gry nie została znaleziona'}), 404
    
    if game_session.completed:
        return jsonify({'error': 'Gra już została ukończona'}), 400
    
    # Walidacja wyniku na podstawie typu gry
    game_config = game_session.get_game_data()
    difficulty = game_config.get('difficulty', 1)
    
    if game_session.game_type == 'virus_alert':
        game = VirusAlert(difficulty)
        max_score = game.calculate_score(game.game_duration, 0)  # Maksymalny wynik bez trafień
        validated_score = min(score, max_score * 1.1)  # 10% tolerancja
    elif game_session.game_type == 'space_defence':
        game = SpaceDefence(difficulty)
        max_score = game.calculate_score(game.total_viruses, game.game_duration)
        validated_score = min(score, max_score * 1.1)
    elif game_session.game_type == 'wifi_guard':
        game = WifiGuard(difficulty)
        max_score = game.calculate_score(True, 0, 1)  # Najlepszy możliwy wynik
        validated_score = min(score, max_score * 1.1)
    else:
        validated_score = score
    
    # Zakończ grę
    game_session.finish_game(int(validated_score), game_data)
    db.session.commit()
    
    # Pobierz nową rangę użytkownika
    user_rank = Leaderboard.get_user_rank(session['user_id'], game_session.game_type)
    
    return jsonify({
        'success': True,
        'score': game_session.score,
        'duration': game_session.duration,
        'rank': user_rank,
        'message': f'Gra zakończona! Wynik: {game_session.score} punktów'
    })

@minigames_bp.route('/api/leaderboard/<game_type>')
def get_leaderboard(game_type):
    """API endpoint do pobierania rankingu"""
    if game_type not in ['virus_alert', 'space_defence', 'wifi_guard']:
        return jsonify({'error': 'Nieprawidłowy typ gry'}), 400
    
    top_scores = Leaderboard.get_top_scores(game_type, 10)
    
    leaderboard = []
    for score_data in top_scores:
        user = User.query.get(score_data.user_id)
        leaderboard.append({
            'username': user.username,
            'score': score_data.score,
            'duration': score_data.duration,
            'date': score_data.created_at.strftime('%d.%m.%Y') if score_data.created_at else ''
        })
    
    return jsonify({
        'game_type': game_type,
        'leaderboard': leaderboard
    })

@minigames_bp.route('/api/user-stats')
def get_user_stats():
    """API endpoint do pobierania statystyk użytkownika"""
    if not require_login():
        return jsonify({'error': 'Wymagane logowanie'}), 401
    
    user_stats = Leaderboard.get_user_stats(session['user_id'])
    
    return jsonify({
        'success': True,
        'stats': user_stats
    })

@minigames_bp.route('/leaderboard')
def leaderboard():
    """Strona rankingów"""
    game_type = request.args.get('game', 'virus_alert')
    
    if game_type not in ['virus_alert', 'space_defence', 'wifi_guard']:
        game_type = 'virus_alert'
    
    top_scores = Leaderboard.get_top_scores(game_type, 20)
    
    leaderboard_data = []
    for i, score_data in enumerate(top_scores, 1):
        user = User.query.get(score_data.user_id)
        leaderboard_data.append({
            'rank': i,
            'username': user.username,
            'score': score_data.score,
            'duration': score_data.duration,
            'date': score_data.created_at.strftime('%d.%m.%Y %H:%M') if score_data.created_at else ''
        })
    
    game_names = {
        'virus_alert': 'Virus Alert',
        'space_defence': 'Space Defence', 
        'wifi_guard': 'WiFi Guard'
    }
    
    return render_template('minigames/leaderboard.html', 
                         leaderboard=leaderboard_data,
                         current_game=game_type,
                         game_name=game_names.get(game_type, game_type),
                         game_names=game_names)

@minigames_bp.route('/api/device-info', methods=['POST'])
def device_info():
    """API endpoint do otrzymywania informacji o urządzeniu"""
    data = request.get_json()
    
    is_mobile = data.get('is_mobile', False)
    has_gyroscope = data.get('has_gyroscope', False)
    screen_width = data.get('screen_width', 1920)
    screen_height = data.get('screen_height', 1080)
    user_agent = request.headers.get('User-Agent', '')
    
    # Zapisz informacje o urządzeniu w sesji
    session['device_info'] = {
        'is_mobile': is_mobile,
        'has_gyroscope': has_gyroscope,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'user_agent': user_agent
    }
    
    return jsonify({
        'success': True,
        'recommendations': {
            'controls': 'touch' if is_mobile else 'keyboard',
            'layout': 'mobile' if is_mobile else 'desktop',
            'gyroscope_available': has_gyroscope
        }
    })

@minigames_bp.route('/api/game-config/<game_type>')
def get_game_config(game_type):
    """API endpoint do pobierania konfiguracji gry"""
    if game_type not in ['virus_alert', 'space_defence', 'wifi_guard']:
        return jsonify({'error': 'Nieprawidłowy typ gry'}), 400
    
    difficulty = request.args.get('difficulty', 1, type=int)
    difficulty = max(1, min(difficulty, 5))
    
    device_info = session.get('device_info', {})
    is_mobile = device_info.get('is_mobile', False)
    
    if game_type == 'virus_alert':
        game = VirusAlert(difficulty)
        config = game.get_game_config()
        config['controls'] = 'touch' if is_mobile else 'keyboard'
    elif game_type == 'space_defence':
        game = SpaceDefence(difficulty)
        config = game.get_game_config()
        config['controls'] = 'gyroscope' if (is_mobile and device_info.get('has_gyroscope')) else 'touch' if is_mobile else 'keyboard'
    elif game_type == 'wifi_guard':
        game = WifiGuard(difficulty)
        config = game.get_game_config()
        config['controls'] = 'touch' if is_mobile else 'keyboard'
    
    config['is_mobile'] = is_mobile
    config['device_info'] = device_info
    
    return jsonify({
        'success': True,
        'config': config
    })