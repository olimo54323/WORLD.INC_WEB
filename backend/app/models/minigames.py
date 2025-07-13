from app.extensions import db
from datetime import datetime
from sqlalchemy import func
import json

class GameSession(db.Model):
    """Model sesji gry - przechowuje informacje o rozgrywce"""
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # virus_alert, space_defence, wifi_guard
    score = db.Column(db.Integer, default=0)
    duration = db.Column(db.Integer, default=0)  # czas gry w sekundach
    completed = db.Column(db.Boolean, default=False)
    game_data = db.Column(db.Text)  # JSON z dodatkowymi danymi gry
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    
    # Relacja z użytkownikiem
    user = db.relationship('User', backref=db.backref('game_sessions', lazy=True))
    
    def set_game_data(self, data):
        """Zapisuje dane gry jako JSON"""
        self.game_data = json.dumps(data)
    
    def get_game_data(self):
        """Pobiera dane gry z JSON"""
        if self.game_data:
            return json.loads(self.game_data)
        return {}
    
    def finish_game(self, final_score, additional_data=None):
        """Kończy grę i zapisuje wyniki"""
        self.score = final_score
        self.completed = True
        self.finished_at = datetime.utcnow()
        
        if self.created_at and self.finished_at:
            delta = self.finished_at - self.created_at
            self.duration = int(delta.total_seconds())
        
        if additional_data:
            current_data = self.get_game_data()
            current_data.update(additional_data)
            self.set_game_data(current_data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'game_type': self.game_type,
            'score': self.score,
            'duration': self.duration,
            'completed': self.completed,
            'game_data': self.get_game_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None
        }

class VirusAlert:
    """Klasa obsługująca grę Virus Alert - unikanie wirusów"""
    
    def __init__(self, difficulty=1):
        self.difficulty = difficulty
        self.viruses_count = min(3 + difficulty, 10)
        self.game_duration = 21  # sekundy
        self.points_per_second = 10
        self.penalty_per_hit = -50
    
    def calculate_score(self, survival_time, hits_taken):
        """Oblicza wynik na podstawie czasu przetrwania i liczby trafień"""
        base_score = survival_time * self.points_per_second
        penalty = hits_taken * self.penalty_per_hit
        final_score = max(0, base_score + penalty)
        
        # Bonus za ukończenie gry
        if survival_time >= self.game_duration:
            final_score += 100 * self.difficulty
        
        return int(final_score)
    
    def get_game_config(self):
        """Zwraca konfigurację gry dla frontend"""
        return {
            'viruses_count': self.viruses_count,
            'game_duration': self.game_duration,
            'difficulty': self.difficulty,
            'points_per_second': self.points_per_second,
            'penalty_per_hit': abs(self.penalty_per_hit)
        }

class SpaceDefence:
    """Klasa obsługująca grę Space Defence - strzelanie do wirusów"""
    
    def __init__(self, difficulty=1):
        self.difficulty = difficulty
        self.virus_rows = 3
        self.virus_cols = 4
        self.total_viruses = self.virus_rows * self.virus_cols
        self.game_duration = 60  # sekundy
        self.points_per_virus = 50
        self.time_bonus_multiplier = 2
    
    def calculate_score(self, viruses_destroyed, time_remaining):
        """Oblicza wynik na podstawie zniszczonych wirusów i pozostałego czasu"""
        base_score = viruses_destroyed * self.points_per_virus
        time_bonus = time_remaining * self.time_bonus_multiplier
        
        # Bonus za ukończenie gry
        completion_bonus = 0
        if viruses_destroyed >= self.total_viruses:
            completion_bonus = 200 * self.difficulty
        
        final_score = base_score + time_bonus + completion_bonus
        return int(final_score)
    
    def get_game_config(self):
        """Zwraca konfigurację gry dla frontend"""
        return {
            'virus_rows': self.virus_rows,
            'virus_cols': self.virus_cols,
            'total_viruses': self.total_viruses,
            'game_duration': self.game_duration,
            'difficulty': self.difficulty,
            'points_per_virus': self.points_per_virus,
            'time_bonus_multiplier': self.time_bonus_multiplier
        }

class WifiGuard:
    """Klasa obsługująca grę WiFi Guard - ochrona hasła"""
    
    def __init__(self, difficulty=1):
        self.difficulty = difficulty
        self.password_length = min(6 + difficulty, 12)
        self.time_limit = max(30 - difficulty * 2, 10)  # sekundy
        self.max_attempts = 3
        
    def generate_password(self):
        """Generuje losowe hasło"""
        import random
        import string
        
        characters = string.ascii_letters + string.digits
        if self.difficulty > 2:
            characters += "!@#$%"
        
        password = ''.join(random.choices(characters, k=self.password_length))
        return password
    
    def calculate_score(self, success, time_taken, attempts_used):
        """Oblicza wynik na podstawie sukcesu, czasu i liczby prób"""
        if not success:
            return 0
        
        base_score = 200
        time_bonus = max(0, (self.time_limit - time_taken) * 10)
        attempt_bonus = (self.max_attempts - attempts_used + 1) * 50
        difficulty_bonus = self.difficulty * 100
        
        final_score = base_score + time_bonus + attempt_bonus + difficulty_bonus
        return int(final_score)
    
    def get_game_config(self):
        """Zwraca konfigurację gry dla frontend"""
        return {
            'password_length': self.password_length,
            'time_limit': self.time_limit,
            'max_attempts': self.max_attempts,
            'difficulty': self.difficulty,
            'password': self.generate_password()
        }

class Leaderboard:
    """Klasa do zarządzania rankingami"""
    
    @staticmethod
    def get_top_scores(game_type, limit=10):
        """Pobiera najlepsze wyniki dla danej gry"""
        top_scores = db.session.query(
            GameSession.score,
            GameSession.user_id,
            GameSession.created_at,
            GameSession.duration
        ).join(
            db.session.query(GameSession.user_id, func.max(GameSession.score).label('max_score'))
            .filter(GameSession.game_type == game_type, GameSession.completed == True)
            .group_by(GameSession.user_id)
            .subquery(),
            GameSession.score == db.text('max_score') and GameSession.user_id == db.text('user_id')
        ).filter(
            GameSession.game_type == game_type,
            GameSession.completed == True
        ).order_by(
            GameSession.score.desc()
        ).limit(limit).all()
        
        return top_scores
    
    @staticmethod
    def get_user_rank(user_id, game_type):
        """Pobiera rangę użytkownika w danej grze"""
        user_best = db.session.query(func.max(GameSession.score)).filter(
            GameSession.user_id == user_id,
            GameSession.game_type == game_type,
            GameSession.completed == True
        ).scalar()
        
        if not user_best:
            return None
        
        better_scores = db.session.query(func.count(func.distinct(GameSession.user_id))).filter(
            GameSession.game_type == game_type,
            GameSession.completed == True,
            GameSession.score > user_best
        ).scalar()
        
        return better_scores + 1
    
    @staticmethod
    def get_user_stats(user_id):
        """Pobiera statystyki użytkownika ze wszystkich gier"""
        stats = {}
        
        for game_type in ['virus_alert', 'space_defence', 'wifi_guard']:
            game_stats = db.session.query(
                func.count(GameSession.id).label('games_played'),
                func.max(GameSession.score).label('best_score'),
                func.avg(GameSession.score).label('avg_score'),
                func.sum(GameSession.duration).label('total_time')
            ).filter(
                GameSession.user_id == user_id,
                GameSession.game_type == game_type,
                GameSession.completed == True
            ).first()
            
            stats[game_type] = {
                'games_played': game_stats.games_played or 0,
                'best_score': int(game_stats.best_score or 0),
                'avg_score': int(game_stats.avg_score or 0),
                'total_time': int(game_stats.total_time or 0),
                'rank': Leaderboard.get_user_rank(user_id, game_type)
            }
        
        return stats