# app/routes/leaderboard.py - NOWY PLIK
from flask import Blueprint, render_template, request, jsonify, session
from app.extensions import db
from app.models.user import User
from app.models.minigames import GameSession, Leaderboard
from sqlalchemy import func, desc
from datetime import datetime, timedelta

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

def require_auth():
    """Sprawdza czy użytkownik jest zalogowany"""
    if 'user_id' not in session:
        return None
    return User.query.get(session['user_id'])

@leaderboard_bp.route('/')
def index():
    """Główna strona leaderboard"""
    return render_template('leaderboard/index.html')

@leaderboard_bp.route('/<game_type>')
def game_leaderboard(game_type):
    """Leaderboard dla konkretnej gry"""
    if game_type not in ['virus_alert', 'space_defence', 'wifi_guard']:
        return render_template('404.html'), 404
    
    # Pobierz top 20 wyników
    leaderboard_data = []
    top_scores = Leaderboard.get_top_scores(game_type, limit=20)
    
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
    
    current_user = require_auth()
    user_rank = None
    user_best_score = None
    
    if current_user:
        user_rank = Leaderboard.get_user_rank(current_user.id, game_type)
        user_best = db.session.query(func.max(GameSession.score)).filter(
            GameSession.user_id == current_user.id,
            GameSession.game_type == game_type,
            GameSession.completed == True
        ).scalar()
        user_best_score = user_best if user_best else 0
    
    return render_template('leaderboard/game.html',
                         leaderboard=leaderboard_data,
                         current_game=game_type,
                         game_name=game_names.get(game_type, game_type),
                         game_names=game_names,
                         user_rank=user_rank,
                         user_best_score=user_best_score)

@leaderboard_bp.route('/live')
def live_leaderboard():
    """Live leaderboard z real-time updates"""
    return render_template('leaderboard/live.html')

@leaderboard_bp.route('/api/<game_type>')
def api_get_leaderboard(game_type):
    """API: Pobiera leaderboard dla gry z paginacją"""
    if game_type not in ['virus_alert', 'space_defence', 'wifi_guard', 'all']:
        return jsonify({'error': 'Invalid game type'}), 400
    
    # Parametry paginacji
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    if game_type == 'all':
        # Globalny leaderboard
        leaderboard_data = []
        for gt in ['virus_alert', 'space_defence', 'wifi_guard']:
            game_leaders = Leaderboard.get_top_scores(gt, limit=5)
            for leader in game_leaders:
                user = User.query.get(leader.user_id)
                leaderboard_data.append({
                    'username': user.username,
                    'score': leader.score,
                    'game_type': gt,
                    'date': leader.created_at.isoformat()
                })
        
        # Sortuj po wyniku malejąco
        leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
        
        # Paginacja manualna
        start = (page - 1) * per_page
        end = start + per_page
        paginated_data = leaderboard_data[start:end]
        total = len(leaderboard_data)
        
        return jsonify({
            'leaderboard': paginated_data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'game_type': game_type
        })
    else:
        # Leaderboard dla konkretnej gry
        query = db.session.query(
            GameSession.user_id,
            func.max(GameSession.score).label('best_score'),
            func.count(GameSession.id).label('games_played'),
            func.avg(GameSession.score).label('avg_score'),
            func.min(GameSession.created_at).label('first_played'),
            func.max(GameSession.created_at).label('last_played')
        ).filter(
            GameSession.game_type == game_type,
            GameSession.completed == True
        ).group_by(GameSession.user_id).order_by(desc('best_score'))
        
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        
        leaderboard = []
        for i, result in enumerate(results, start=(page - 1) * per_page + 1):
            user = User.query.get(result.user_id)
            leaderboard.append({
                'rank': i,
                'user_id': result.user_id,
                'username': user.username,
                'best_score': result.best_score,
                'games_played': result.games_played,
                'avg_score': round(result.avg_score, 1),
                'first_played': result.first_played.isoformat(),
                'last_played': result.last_played.isoformat()
            })
        
        return jsonify({
            'leaderboard': leaderboard,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'game_type': game_type
        })

@leaderboard_bp.route('/api/recent-activity')
def api_recent_activity():
    """API: Ostatnia aktywność na leaderboard"""
    # Ostatnie wyniki z ostatnich 15 minut
    cutoff_time = datetime.utcnow() - timedelta(minutes=15)
    
    recent_sessions = db.session.query(
        GameSession.game_type,
        GameSession.score,
        GameSession.user_id,
        GameSession.created_at,
        User.username
    ).join(User).filter(
        GameSession.completed == True,
        GameSession.created_at >= cutoff_time
    ).order_by(GameSession.created_at.desc()).limit(10).all()
    
    activities = []
    for session in recent_sessions:
        activities.append({
            'type': 'game_completed',
            'username': session.username,
            'game_type': session.game_type,
            'score': session.score,
            'timestamp': session.created_at.isoformat(),
            'time_ago': get_time_ago(session.created_at)
        })
    
    return jsonify({
        'activities': activities,
        'timestamp': datetime.utcnow().isoformat()
    })

@leaderboard_bp.route('/api/stats')
def api_global_stats():
    """API: Globalne statystyki leaderboard"""
    try:
        # Statystyki globalne
        total_games = GameSession.query.filter_by(completed=True).count()
        total_players = db.session.query(func.count(func.distinct(GameSession.user_id))).filter(
            GameSession.completed == True
        ).scalar()
        
        # Najwyższy wynik globalnie
        highest_score = db.session.query(func.max(GameSession.score)).filter(
            GameSession.completed == True
        ).scalar() or 0
        
        # Top gracz
        top_player_session = db.session.query(GameSession, User).join(User).filter(
            GameSession.completed == True,
            GameSession.score == highest_score
        ).first()
        
        top_player = None
        if top_player_session:
            session_obj, user_obj = top_player_session
            top_player = {
                'username': user_obj.username,
                'score': session_obj.score,
                'game_type': session_obj.game_type
            }
        
        # Statystyki per-game
        game_stats = {}
        for game_type in ['virus_alert', 'space_defence', 'wifi_guard']:
            game_count = GameSession.query.filter_by(game_type=game_type, completed=True).count()
            game_max_score = db.session.query(func.max(GameSession.score)).filter(
                GameSession.game_type == game_type,
                GameSession.completed == True
            ).scalar() or 0
            
            game_stats[game_type] = {
                'total_games': game_count,
                'highest_score': game_max_score
            }
        
        return jsonify({
            'total_games': total_games,
            'total_players': total_players,
            'highest_score': highest_score,
            'top_player': top_player,
            'game_stats': game_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch stats'}), 500

@leaderboard_bp.route('/api/user/<int:user_id>/rank')
def api_user_rank(user_id):
    """API: Pozycja użytkownika w rankingach"""
    current_user = require_auth()
    if not current_user or (current_user.id != user_id and not hasattr(current_user, 'is_admin')):
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    ranks = {}
    for game_type in ['virus_alert', 'space_defence', 'wifi_guard']:
        rank = Leaderboard.get_user_rank(user_id, game_type)
        best_score = db.session.query(func.max(GameSession.score)).filter(
            GameSession.user_id == user_id,
            GameSession.game_type == game_type,
            GameSession.completed == True
        ).scalar()
        
        ranks[game_type] = {
            'rank': rank,
            'best_score': best_score or 0
        }
    
    return jsonify({
        'user': user.to_dict(),
        'ranks': ranks,
        'timestamp': datetime.utcnow().isoformat()
    })

def get_time_ago(timestamp):
    """Oblicza czas jaki minął od danej daty"""
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"