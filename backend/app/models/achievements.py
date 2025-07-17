# app/models/achievements.py - NOWY PLIK
from app.extensions import db
from datetime import datetime
from sqlalchemy import func

class Achievement(db.Model):
    """Model osiągnięć w grze"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default='trophy')  # FontAwesome icon class
    category = db.Column(db.String(50), default='general')  # general, game_specific, social
    condition_type = db.Column(db.String(50), nullable=False)  # score, games_played, streak, time
    condition_value = db.Column(db.Integer, nullable=False)
    condition_game = db.Column(db.String(50))  # null = all games, or specific game
    points = db.Column(db.Integer, default=10)  # punkty za osiągnięcie
    is_hidden = db.Column(db.Boolean, default=False)  # ukryte osiągnięcia
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacja z użytkownikami którzy mają to osiągnięcie
    user_achievements = db.relationship('UserAchievement', backref='achievement', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'category': self.category,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value,
            'condition_game': self.condition_game,
            'points': self.points,
            'is_hidden': self.is_hidden,
            'is_active': self.is_active
        }
    
    @staticmethod
    def check_and_unlock(user_id, game_type=None, score=None):
        """Sprawdza i odblokowuje osiągnięcia dla użytkownika"""
        from app.models.minigames import GameSession
        from app.models.user import User
        
        unlocked_achievements = []
        
        # Pobierz wszystkie aktywne osiągnięcia
        achievements = Achievement.query.filter_by(is_active=True).all()
        
        for achievement in achievements:
            # Sprawdź czy użytkownik już ma to osiągnięcie
            existing = UserAchievement.query.filter_by(
                user_id=user_id, 
                achievement_id=achievement.id
            ).first()
            
            if existing:
                continue
            
            # Sprawdź warunki osiągnięcia
            if achievement.condition_type == 'score':
                # Najwyższy wynik w grze
                query = db.session.query(func.max(GameSession.score)).filter(
                    GameSession.user_id == user_id,
                    GameSession.completed == True
                )
                
                if achievement.condition_game:
                    query = query.filter(GameSession.game_type == achievement.condition_game)
                
                max_score = query.scalar() or 0
                
                if max_score >= achievement.condition_value:
                    unlock_achievement(user_id, achievement.id)
                    unlocked_achievements.append(achievement.to_dict())
            
            elif achievement.condition_type == 'games_played':
                # Liczba zagranych gier
                query = db.session.query(func.count(GameSession.id)).filter(
                    GameSession.user_id == user_id,
                    GameSession.completed == True
                )
                
                if achievement.condition_game:
                    query = query.filter(GameSession.game_type == achievement.condition_game)
                
                games_count = query.scalar() or 0
                
                if games_count >= achievement.condition_value:
                    unlock_achievement(user_id, achievement.id)
                    unlocked_achievements.append(achievement.to_dict())
            
            elif achievement.condition_type == 'streak':
                # Seria wygranych gier (implementacja zaawansowana)
                # Tutaj można dodać logikę sprawdzania serii
                pass
            
            elif achievement.condition_type == 'time':
                # Całkowity czas gry
                query = db.session.query(func.sum(GameSession.duration)).filter(
                    GameSession.user_id == user_id,
                    GameSession.completed == True
                )
                
                if achievement.condition_game:
                    query = query.filter(GameSession.game_type == achievement.condition_game)
                
                total_time = query.scalar() or 0
                
                if total_time >= achievement.condition_value:
                    unlock_achievement(user_id, achievement.id)
                    unlocked_achievements.append(achievement.to_dict())
        
        return unlocked_achievements
    
    @staticmethod
    def create_default_achievements():
        """Tworzy domyślne osiągnięcia"""
        default_achievements = [
            # Osiągnięcia punktowe
            {'name': 'First Blood', 'description': 'Zdobądź swoje pierwsze punkty', 'icon': 'star', 'condition_type': 'score', 'condition_value': 1, 'points': 5},
            {'name': 'Century Club', 'description': 'Zdobądź 100 punktów w jednej grze', 'icon': 'medal', 'condition_type': 'score', 'condition_value': 100, 'points': 10},
            {'name': 'High Roller', 'description': 'Zdobądź 500 punktów w jednej grze', 'icon': 'crown', 'condition_type': 'score', 'condition_value': 500, 'points': 25},
            {'name': 'World Saver', 'description': 'Zdobądź 1000 punktów w jednej grze', 'icon': 'trophy', 'condition_type': 'score', 'condition_value': 1000, 'points': 50},
            
            # Osiągnięcia za granie
            {'name': 'Getting Started', 'description': 'Zagraj swoją pierwszą grę', 'icon': 'play', 'condition_type': 'games_played', 'condition_value': 1, 'points': 5},
            {'name': 'Regular Agent', 'description': 'Zagraj 10 gier', 'icon': 'gamepad', 'condition_type': 'games_played', 'condition_value': 10, 'points': 15},
            {'name': 'Veteran Agent', 'description': 'Zagraj 50 gier', 'icon': 'shield-alt', 'condition_type': 'games_played', 'condition_value': 50, 'points': 30},
            {'name': 'Elite Agent', 'description': 'Zagraj 100 gier', 'icon': 'star-of-life', 'condition_type': 'games_played', 'condition_value': 100, 'points': 50},
            
            # Osiągnięcia czasowe
            {'name': 'Time Keeper', 'description': 'Spędź 10 minut grając', 'icon': 'clock', 'condition_type': 'time', 'condition_value': 600, 'points': 10},
            {'name': 'Marathon Runner', 'description': 'Spędź godzinę grając', 'icon': 'stopwatch', 'condition_type': 'time', 'condition_value': 3600, 'points': 25},
            
            # Osiągnięcia specyficzne dla gier
            {'name': 'Virus Hunter', 'description': 'Zdobądź 200 punktów w Virus Alert', 'icon': 'bug', 'condition_type': 'score', 'condition_value': 200, 'condition_game': 'virus_alert', 'points': 15},
            {'name': 'Space Defender', 'description': 'Zdobądź 300 punktów w Space Defence', 'icon': 'rocket', 'condition_type': 'score', 'condition_value': 300, 'condition_game': 'space_defence', 'points': 15},
            {'name': 'Network Guardian', 'description': 'Zdobądź 250 punktów w WiFi Guard', 'icon': 'wifi', 'condition_type': 'score', 'condition_value': 250, 'condition_game': 'wifi_guard', 'points': 15},
            
            # Ukryte osiągnięcia
            {'name': 'Secret Agent', 'description': 'Odkryj sekretną funkcję', 'icon': 'user-secret', 'condition_type': 'games_played', 'condition_value': 1, 'points': 100, 'is_hidden': True},
        ]
        
        for achievement_data in default_achievements:
            existing = Achievement.query.filter_by(name=achievement_data['name']).first()
            if not existing:
                achievement = Achievement(**achievement_data)
                db.session.add(achievement)
        
        db.session.commit()

class UserAchievement(db.Model):
    """Model łączący użytkowników z osiągnięciami"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.Column(db.Integer, default=0)  # dla osiągnięć z postępem
    
    # Unikalna kombinacja user + achievement
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),)
    
    # Relacje
    user = db.relationship('User', backref=db.backref('achievements', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'unlocked_at': self.unlocked_at.isoformat(),
            'progress': self.progress,
            'achievement': self.achievement.to_dict()
        }

def unlock_achievement(user_id, achievement_id):
    """Odblokowuje osiągnięcie dla użytkownika"""
    existing = UserAchievement.query.filter_by(
        user_id=user_id,
        achievement_id=achievement_id
    ).first()
    
    if not existing:
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id
        )
        db.session.add(user_achievement)
        db.session.commit()
        return True
    return False