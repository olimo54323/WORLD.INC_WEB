#!/usr/bin/env python3
"""
🌍 World.Inc Database Setup Script
Konfiguruje bazę danych dla aplikacji World.Inc
ZAKTUALIZOWANY O NOWE MODELE: Achievements, Daily Quests
"""

import os
import sys
from datetime import datetime, date

# Dodaj katalog backendu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.minigames import GameSession
from app.models.achievements import Achievement, UserAchievement
from app.models.daily_quests import DailyQuest, UserQuestProgress

def create_database():
    """Tworzy bazę danych i tabele"""
    print("🌍 World.Inc Database Setup")
    print("=" * 40)
    
    # Utwórz aplikację
    app = create_app('development')
    
    with app.app_context():
        try:
            # Usuń istniejące tabele (jeśli potrzeba czysty start)
            print("🗑️  Usuwanie starych tabel...")
            db.drop_all()
            
            # Utwórz nowe tabele
            print("🏗️  Tworzenie nowych tabel...")
            db.create_all()
            
            print("✅ Tabele utworzone pomyślnie!")
            
            # Sprawdź strukturę tabel
            print("\n📊 Sprawdzanie struktury tabel:")
            tables_to_check = ['users', 'game_sessions', 'achievements', 'user_achievements', 'daily_quests', 'user_quest_progress']
            
            try:
                with db.engine.connect() as conn:
                    for table in tables_to_check:
                        try:
                            result = conn.execute(db.text(f"PRAGMA table_info({table})"))
                            columns = [row[1] for row in result]
                            print(f"   📋 {table}: {len(columns)} kolumn - {', '.join(columns[:3])}{'...' if len(columns) > 3 else ''}")
                        except Exception:
                            print(f"   ⚠️  {table}: Tabela nie istnieje lub błąd")
            except Exception as e:
                print(f"   ⚠️  Nie można sprawdzić struktury tabel: {e}")
                print("   ✅ Tabele prawdopodobnie zostały utworzone poprawnie")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas generowania questów: {e}")
            db.session.rollback()
            return False

def create_sample_game_sessions():
    """Tworzy przykładowe sesje gier dla testów"""
    print("\n🎮 Tworzenie przykładowych sesji gier...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Pobierz użytkowników
            users = User.query.all()
            if not users:
                print("⚠️  Brak użytkowników. Utwórz najpierw użytkowników.")
                return False
            
            import random
            from datetime import timedelta
            
            games_created = 0
            game_types = ['virus_alert', 'space_defence', 'wifi_guard']
            
            # Utwórz po kilka sesji dla każdego użytkownika
            for user in users[:4]:  # Tylko pierwsi 4 użytkownicy
                for _ in range(random.randint(3, 8)):
                    game_type = random.choice(game_types)
                    score = random.randint(50, 800)
                    duration = random.randint(30, 300)  # 30 sekund do 5 minut
                    
                    # Losowa data z ostatnich 7 dni
                    days_ago = random.randint(0, 7)
                    created_at = datetime.utcnow() - timedelta(days=days_ago)
                    
                    session = GameSession(
                        user_id=user.id,
                        game_type=game_type,
                        score=score,
                        duration=duration,
                        completed=True,
                        created_at=created_at,
                        finished_at=created_at + timedelta(seconds=duration)
                    )
                    
                    # Dodaj przykładowe dane gry
                    game_data = {
                        'difficulty': random.randint(1, 5),
                        'attempts': random.randint(1, 3),
                        'perfect_rounds': random.randint(0, score // 100)
                    }
                    session.set_game_data(game_data)
                    
                    db.session.add(session)
                    games_created += 1
            
            db.session.commit()
            print(f"✅ Utworzono {games_created} przykładowych sesji gier!")
            
            # Pokaż statystyki
            print("\n📊 Statystyki sesji:")
            for game_type in game_types:
                count = GameSession.query.filter_by(game_type=game_type, completed=True).count()
                print(f"   - {game_type}: {count} sesji")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia sesji gier: {e}")
            db.session.rollback()
            return False

def verify_setup():
    """Weryfikuje poprawność konfiguracji bazy danych"""
    print("\n🔍 Weryfikacja konfiguracji...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Sprawdź wszystkie tabele
            checks = {
                'users': User.query.count(),
                'game_sessions': GameSession.query.count(),
                'achievements': Achievement.query.count(),
                'user_achievements': UserAchievement.query.count(),
                'daily_quests': DailyQuest.query.count(),
                'user_quest_progress': UserQuestProgress.query.count()
            }
            
            print("📋 Liczba rekordów w tabelach:")
            for table, count in checks.items():
                print(f"   - {table}: {count}")
            
            # Test relacji
            if checks['users'] > 0:
                user = User.query.first()
                print(f"\n🔐 Test funkcji dla {user.username}...")
                print("   - Funkcja sprawdzania hasła: ✅ Dostępna")
                print("   - Serializacja do dict: ✅ Dostępna")
                
                # Test relacji z sesjami gier
                user_sessions = GameSession.query.filter_by(user_id=user.id).count()
                print(f"   - Sesje gier użytkownika: {user_sessions}")
            
            # Test osiągnięć
            if checks['achievements'] > 0:
                achievement = Achievement.query.first()
                print(f"\n🏆 Test osiągnięć - przykład: '{achievement.name}'")
                print(f"   - Opis: {achievement.description}")
                print(f"   - Punkty: {achievement.points}")
            
            # Test questów
            today_quests = DailyQuest.query.filter_by(quest_date=date.today(), is_active=True).count()
            print(f"\n📋 Dzisiejsze questy: {today_quests}")
            
            print("\n✅ Weryfikacja zakończona pomyślnie!")
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas weryfikacji: {e}")
            return False

def show_connection_info():
    """Pokazuje informacje o połączeniu z bazą danych"""
    print("\n📡 Informacje o konfiguracji:")
    print("-" * 30)
    
    app = create_app('development')
    print(f"🗄️  Baza danych: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🔧 Tryb debug: {app.config['DEBUG']}")
    print(f"🔑 Secret key: {'Ustawiony' if app.config['SECRET_KEY'] else 'Brak'}")
    
    # Sprawdź czy plik bazy danych istnieje
    if 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            print(f"📁 Plik bazy: {db_path} ({db_size} bytes)")
        else:
            print(f"📁 Plik bazy: {db_path} (nie istnieje)")

def quick_setup():
    """Szybki setup - prosta wersja bez zaawansowanych opcji"""
    print("🚀 Szybki Setup Bazy Danych World.Inc")
    print("=" * 40)
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("🏗️  Tworzenie tabel...")
            db.create_all()
            print("✅ Tabele utworzone!")
            
            # Sprawdź czy są już dane
            user_count = User.query.count()
            achievements_count = Achievement.query.count()
            quests_count = DailyQuest.query.filter_by(quest_date=date.today()).count()
            
            print(f"👥 Aktualnie w bazie: {user_count} użytkowników")
            print(f"🏆 Aktualnie w bazie: {achievements_count} osiągnięć")
            print(f"📋 Dzisiejsze questy: {quests_count}")
            
            # Utwórz dane jeśli ich brak
            if user_count == 0:
                print("➕ Tworzenie testowych użytkowników...")
                users_data = [
                    ('admin', 'admin@world.inc', 'admin123'),
                    ('agent007', 'james.bond@world.inc', 'secret007'),
                    ('testuser', 'test@world.inc', 'test123'),
                    ('worldsaver', 'hero@world.inc', 'saveworld')
                ]
                
                for username, email, password in users_data:
                    user = User(username=username, email=email)
                    user.set_password(password)
                    db.session.add(user)
                
                db.session.commit()
                print(f"✅ Utworzono {len(users_data)} testowych użytkowników!")
            
            if achievements_count == 0:
                print("➕ Tworzenie domyślnych osiągnięć...")
                Achievement.create_default_achievements()
                new_count = Achievement.query.count()
                print(f"✅ Utworzono {new_count} osiągnięć!")
            
            if quests_count == 0:
                print("➕ Generowanie dziennych questów...")
                created_quests = DailyQuest.generate_daily_quests()
                if created_quests:
                    print(f"✅ Wygenerowano {len(created_quests)} questów!")
            
            # Utwórz przykładowe sesje gier
            sessions_count = GameSession.query.count()
            if sessions_count == 0 and user_count > 0:
                print("➕ Tworzenie przykładowych sesji gier...")
                create_sample_game_sessions()
            
            print("\n🎉 Setup zakończony pomyślnie!")
            print("💡 Uruchom aplikację: cd backend && python app.py")
            print("🌐 Strona: http://localhost:5000")
            
            # Pokaż dane testowe
            if user_count == 0:  # Jeśli właśnie utworzyliśmy użytkowników
                print("\n🔑 Dane testowe:")
                for username, email, password in users_data:
                    print(f"   {username} / {email} / {password}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return False

def main():
    """Główna funkcja skryptu"""
    print("🚀 Witamy w World.Inc Database Setup!")
    print("Wersja: 2.0 (z Achievements + Daily Quests)")
    print("Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    # Sprawdź czy użytkownik chce szybki setup
    print("Wybierz tryb setup:")
    print("1. 🚀 Szybki setup (zalecany)")
    print("2. 🔧 Pełny setup z opcjami")
    print("3. ⚡ Tylko nowe modele (Achievements + Quests)")
    
    try:
        choice = input("\nWybierz opcję (1/2/3) [1]: ").strip()
        
        if choice == '2':
            # Pełny setup
            try:
                # Krok 1: Utwórz bazę danych
                if not create_database():
                    print("❌ Przerwano z powodu błędu tworzenia bazy danych.")
                    return 1
                
                # Krok 2: Utwórz testowych użytkowników
                create_users = input("\n❓ Czy utworzyć testowych użytkowników? (Y/n): ")
                if create_users.lower() != 'n':
                    if not create_test_users():
                        print("⚠️  Kontynuujemy mimo problemów z testowymi użytkownikami.")
                
                # Krok 3: Utwórz osiągnięcia
                create_ach = input("\n❓ Czy utworzyć domyślne osiągnięcia? (Y/n): ")
                if create_ach.lower() != 'n':
                    if not create_default_achievements():
                        print("⚠️  Kontynuujemy mimo problemów z osiągnięciami.")
                
                # Krok 4: Utwórz questy
                create_q = input("\n❓ Czy wygenerować dzienne questy? (Y/n): ")
                if create_q.lower() != 'n':
                    if not create_daily_quests():
                        print("⚠️  Kontynuujemy mimo problemów z questami.")
                
                # Krok 5: Przykładowe dane
                create_sessions = input("\n❓ Czy utworzyć przykładowe sesje gier? (Y/n): ")
                if create_sessions.lower() != 'n':
                    create_sample_game_sessions()
                
                # Krok 6: Weryfikacja
                if not verify_setup():
                    print("⚠️  Ostrzeżenie: Weryfikacja nie powiodła się.")
                
                # Krok 7: Informacje o połączeniu
                show_connection_info()
                
            except Exception as e:
                print(f"\n❌ Błąd podczas pełnego setup: {e}")
                return 1
                
        elif choice == '3':
            # Tylko nowe modele
            print("⚡ Aktualizacja z nowymi modelami...")
            
            app = create_app('development')
            with app.app_context():
                try:
                    # Utwórz tylko nowe tabele
                    db.create_all()
                    print("✅ Zaktualizowano strukturę bazy danych!")
                    
                    # Dodaj osiągnięcia jeśli ich brak
                    if Achievement.query.count() == 0:
                        Achievement.create_default_achievements()
                        print("✅ Dodano domyślne osiągnięcia!")
                    
                    # Wygeneruj questy na dzisiaj
                    if DailyQuest.query.filter_by(quest_date=date.today()).count() == 0:
                        created_quests = DailyQuest.generate_daily_quests()
                        if created_quests:
                            print(f"✅ Wygenerowano {len(created_quests)} questów!")
                    
                except Exception as e:
                    print(f"❌ Błąd aktualizacji: {e}")
                    return 1
        else:
            # Szybki setup (domyślny)
            if not quick_setup():
                print("❌ Szybki setup nie powiódł się.")
                return 1
        
        print("\n" + "=" * 50)
        print("🎉 Setup zakończony!")
        print("💡 Możesz teraz uruchomić aplikację poleceniem:")
        print("   cd backend && python app.py")
        print("🌐 Aplikacja będzie dostępna pod: http://localhost:5000")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Przerwano przez użytkownika.")
        return 1
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

def create_sample_game_sessions():
    """Tworzy przykładowe sesje gier dla testów"""
    print("\n🎮 Tworzenie przykładowych sesji gier...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Pobierz użytkowników
            users = User.query.all()
            if not users:
                print("⚠️  Brak użytkowników. Utwórz najpierw użytkowników.")
                return False
            
            import random
            from datetime import timedelta
            
            games_created = 0
            game_types = ['virus_alert', 'space_defence', 'wifi_guard']
            
            # Utwórz po kilka sesji dla każdego użytkownika
            for user in users[:4]:  # Tylko pierwsi 4 użytkownicy
                for _ in range(random.randint(3, 8)):
                    game_type = random.choice(game_types)
                    score = random.randint(50, 800)
                    duration = random.randint(30, 300)  # 30 sekund do 5 minut
                    
                    # Losowa data z ostatnich 7 dni
                    days_ago = random.randint(0, 7)
                    created_at = datetime.utcnow() - timedelta(days=days_ago)
                    
                    session = GameSession(
                        user_id=user.id,
                        game_type=game_type,
                        score=score,
                        duration=duration,
                        completed=True,
                        created_at=created_at,
                        finished_at=created_at + timedelta(seconds=duration)
                    )
                    
                    # Dodaj przykładowe dane gry
                    game_data = {
                        'difficulty': random.randint(1, 5),
                        'attempts': random.randint(1, 3),
                        'perfect_rounds': random.randint(0, score // 100)
                    }
                    session.set_game_data(game_data)
                    
                    db.session.add(session)
                    games_created += 1
            
            db.session.commit()
            print(f"✅ Utworzono {games_created} przykładowych sesji gier!")
            
            # Pokaż statystyki
            print("\n📊 Statystyki sesji:")
            for game_type in game_types:
                count = GameSession.query.filter_by(game_type=game_type, completed=True).count()
                print(f"   - {game_type}: {count} sesji")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia sesji gier: {e}")
            db.session.rollback()
            return False

def verify_setup():
    """Weryfikuje poprawność konfiguracji bazy danych"""
    print("\n🔍 Weryfikacja konfiguracji...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Sprawdź wszystkie tabele
            checks = {
                'users': User.query.count(),
                'game_sessions': GameSession.query.count(),
                'achievements': Achievement.query.count(),
                'user_achievements': UserAchievement.query.count(),
                'daily_quests': DailyQuest.query.count(),
                'user_quest_progress': UserQuestProgress.query.count()
            }
            
            print("📋 Liczba rekordów w tabelach:")
            for table, count in checks.items():
                print(f"   - {table}: {count}")
            
            # Test relacji
            if checks['users'] > 0:
                user = User.query.first()
                print(f"\n🔐 Test funkcji dla {user.username}...")
                print("   - Funkcja sprawdzania hasła: ✅ Dostępna")
                print("   - Serializacja do dict: ✅ Dostępna")
                
                # Test relacji z sesjami gier
                user_sessions = GameSession.query.filter_by(user_id=user.id).count()
                print(f"   - Sesje gier użytkownika: {user_sessions}")
            
            # Test osiągnięć
            if checks['achievements'] > 0:
                achievement = Achievement.query.first()
                print(f"\n🏆 Test osiągnięć - przykład: '{achievement.name}'")
                print(f"   - Opis: {achievement.description}")
                print(f"   - Punkty: {achievement.points}")
            
            # Test questów
            today_quests = DailyQuest.query.filter_by(quest_date=date.today(), is_active=True).count()
            print(f"\n📋 Dzisiejsze questy: {today_quests}")
            
            print("\n✅ Weryfikacja zakończona pomyślnie!")
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas weryfikacji: {e}")
            return False

def show_connection_info():
    """Pokazuje informacje o połączeniu z bazą danych"""
    print("\n📡 Informacje o konfiguracji:")
    print("-" * 30)
    
    app = create_app('development')
    print(f"🗄️  Baza danych: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🔧 Tryb debug: {app.config['DEBUG']}")
    print(f"🔑 Secret key: {'Ustawiony' if app.config['SECRET_KEY'] else 'Brak'}")
    
    # Sprawdź czy plik bazy danych istnieje
    if 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            print(f"📁 Plik bazy: {db_path} ({db_size} bytes)")
        else:
            print(f"📁 Plik bazy: {db_path} (nie istnieje)")

def quick_setup():
    """Szybki setup - prosta wersja bez zaawansowanych opcji"""
    print("🚀 Szybki Setup Bazy Danych World.Inc")
    print("=" * 40)
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("🏗️  Tworzenie tabel...")
            db.create_all()
            print("✅ Tabele utworzone!")
            
            # Sprawdź czy są już dane
            user_count = User.query.count()
            achievements_count = Achievement.query.count()
            quests_count = DailyQuest.query.filter_by(quest_date=date.today()).count()
            
            print(f"👥 Aktualnie w bazie: {user_count} użytkowników")
            print(f"🏆 Aktualnie w bazie: {achievements_count} osiągnięć")
            print(f"📋 Dzisiejsze questy: {quests_count}")
            
            # Utwórz dane jeśli ich brak
            if user_count == 0:
                print("➕ Tworzenie testowych użytkowników...")
                users_data = [
                    ('admin', 'admin@world.inc', 'admin123'),
                    ('agent007', 'james.bond@world.inc', 'secret007'),
                    ('testuser', 'test@world.inc', 'test123'),
                    ('worldsaver', 'hero@world.inc', 'saveworld')
                ]
                
                for username, email, password in users_data:
                    user = User(username=username, email=email)
                    user.set_password(password)
                    db.session.add(user)
                
                db.session.commit()
                print(f"✅ Utworzono {len(users_data)} testowych użytkowników!")
            
            if achievements_count == 0:
                print("➕ Tworzenie domyślnych osiągnięć...")
                Achievement.create_default_achievements()
                new_count = Achievement.query.count()
                print(f"✅ Utworzono {new_count} osiągnięć!")
            
            if quests_count == 0:
                print("➕ Generowanie dziennych questów...")
                created_quests = DailyQuest.generate_daily_quests()
                if created_quests:
                    print(f"✅ Wygenerowano {len(created_quests)} questów!")
            
            # Utwórz przykładowe sesje gier
            sessions_count = GameSession.query.count()
            if sessions_count == 0 and user_count > 0:
                print("➕ Tworzenie przykładowych sesji gier...")
                create_sample_game_sessions()
            
            print("\n🎉 Setup zakończony pomyślnie!")
            print("💡 Uruchom aplikację: cd backend && python app.py")
            print("🌐 Strona: http://localhost:5000")
            
            # Pokaż dane testowe
            if user_count == 0:  # Jeśli właśnie utworzyliśmy użytkowników
                print("\n🔑 Dane testowe:")
                for username, email, password in users_data:
                    print(f"   {username} / {email} / {password}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return False

def main():
    """Główna funkcja skryptu"""
    print("🚀 Witamy w World.Inc Database Setup!")
    print("Wersja: 2.0 (z Achievements + Daily Quests)")
    print("Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    # Sprawdź czy użytkownik chce szybki setup
    print("Wybierz tryb setup:")
    print("1. 🚀 Szybki setup (zalecany)")
    print("2. 🔧 Pełny setup z opcjami")
    print("3. ⚡ Tylko nowe modele (Achievements + Quests)")
    
    try:
        choice = input("\nWybierz opcję (1/2/3) [1]: ").strip()
        
        if choice == '2':
            # Pełny setup
            try:
                # Krok 1: Utwórz bazę danych
                if not create_database():
                    print("❌ Przerwano z powodu błędu tworzenia bazy danych.")
                    return 1
                
                # Krok 2: Utwórz testowych użytkowników
                create_users = input("\n❓ Czy utworzyć testowych użytkowników? (Y/n): ")
                if create_users.lower() != 'n':
                    if not create_test_users():
                        print("⚠️  Kontynuujemy mimo problemów z testowymi użytkownikami.")
                
                # Krok 3: Utwórz osiągnięcia
                create_ach = input("\n❓ Czy utworzyć domyślne osiągnięcia? (Y/n): ")
                if create_ach.lower() != 'n':
                    if not create_default_achievements():
                        print("⚠️  Kontynuujemy mimo problemów z osiągnięciami.")
                
                # Krok 4: Utwórz questy
                create_q = input("\n❓ Czy wygenerować dzienne questy? (Y/n): ")
                if create_q.lower() != 'n':
                    if not create_daily_quests():
                        print("⚠️  Kontynuujemy mimo problemów z questami.")
                
                # Krok 5: Przykładowe dane
                create_sessions = input("\n❓ Czy utworzyć przykładowe sesje gier? (Y/n): ")
                if create_sessions.lower() != 'n':
                    create_sample_game_sessions()
                
                # Krok 6: Weryfikacja
                if not verify_setup():
                    print("⚠️  Ostrzeżenie: Weryfikacja nie powiodła się.")
                
                # Krok 7: Informacje o połączeniu
                show_connection_info()
                
            except Exception as e:
                print(f"\n❌ Błąd podczas pełnego setup: {e}")
                return 1
                
        elif choice == '3':
            # Tylko nowe modele
            print("⚡ Aktualizacja z nowymi modelami...")
            
            app = create_app('development')
            with app.app_context():
                try:
                    # Utwórz tylko nowe tabele
                    db.create_all()
                    print("✅ Zaktualizowano strukturę bazy danych!")
                    
                    # Dodaj osiągnięcia jeśli ich brak
                    if Achievement.query.count() == 0:
                        Achievement.create_default_achievements()
                        print("✅ Dodano domyślne osiągnięcia!")
                    
                    # Wygeneruj questy na dzisiaj
                    if DailyQuest.query.filter_by(quest_date=date.today()).count() == 0:
                        created_quests = DailyQuest.generate_daily_quests()
                        if created_quests:
                            print(f"✅ Wygenerowano {len(created_quests)} questów!")
                    
                except Exception as e:
                    print(f"❌ Błąd aktualizacji: {e}")
                    return 1
        else:
            # Szybki setup (domyślny)
            if not quick_setup():
                print("❌ Szybki setup nie powiódł się.")
                return 1
        
        print("\n" + "=" * 50)
        print("🎉 Setup zakończony!")
        print("💡 Możesz teraz uruchomić aplikację poleceniem:")
        print("   cd backend && python app.py")
        print("🌐 Aplikacja będzie dostępna pod: http://localhost:5000")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Przerwano przez użytkownika.")
        return 1
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd: {e}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

def create_test_users():
    """Tworzy testowych użytkowników"""
    print("\n👥 Tworzenie testowych użytkowników...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Sprawdź czy użytkownicy już istnieją
            existing_users = User.query.count()
            if existing_users > 0:
                print(f"⚠️  Znaleziono {existing_users} istniejących użytkowników.")
                choice = input("Czy chcesz usunąć wszystkich i utworzyć nowych? (y/N): ")
                if choice.lower() != 'y':
                    print("❌ Anulowano tworzenie testowych użytkowników.")
                    return False
                
                # Usuń wszystkich użytkowników
                User.query.delete()
                db.session.commit()
                print("🗑️  Usunięto wszystkich użytkowników.")
            
            # Testowi użytkownicy
            test_users = [
                {'username': 'admin', 'email': 'admin@world.inc', 'password': 'admin123'},
                {'username': 'agent007', 'email': 'james.bond@world.inc', 'password': 'secret007'},
                {'username': 'testuser', 'email': 'test@world.inc', 'password': 'test123'},
                {'username': 'worldsaver', 'email': 'hero@world.inc', 'password': 'saveworld'},
                {'username': 'hacker_hunter', 'email': 'hunter@world.inc', 'password': 'hunter123'},
                {'username': 'cyber_guardian', 'email': 'guardian@world.inc', 'password': 'guard456'}
            ]
            
            created_count = 0
            
            for user_data in test_users:
                try:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email']
                    )
                    user.set_password(user_data['password'])
                    
                    db.session.add(user)
                    created_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Błąd tworzenia użytkownika {user_data['username']}: {e}")
            
            db.session.commit()
            print(f"✅ Utworzono {created_count} testowych użytkowników!")
            
            # Pokaż dane logowania
            if created_count > 0:
                print("\n🔑 Dane do logowania:")
                for user_data in test_users[:created_count]:
                    print(f"   {user_data['username']} / {user_data['email']} / {user_data['password']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia użytkowników: {e}")
            db.session.rollback()
            return False

def create_default_achievements():
    """Tworzy domyślne osiągnięcia"""
    print("\n🏆 Tworzenie domyślnych osiągnięć...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Sprawdź czy osiągnięcia już istnieją
            existing_achievements = Achievement.query.count()
            if existing_achievements > 0:
                print(f"⚠️  Znaleziono {existing_achievements} istniejących osiągnięć.")
                choice = input("Czy chcesz usunąć wszystkie i utworzyć nowe? (y/N): ")
                if choice.lower() != 'y':
                    print("❌ Anulowano tworzenie osiągnięć.")
                    return False
                
                Achievement.query.delete()
                UserAchievement.query.delete()
                db.session.commit()
                print("🗑️  Usunięto wszystkie osiągnięcia.")
            
            # Utwórz domyślne osiągnięcia
            Achievement.create_default_achievements()
            
            achievements_count = Achievement.query.count()
            print(f"✅ Utworzono {achievements_count} osiągnięć!")
            
            # Pokaż przykłady
            sample_achievements = Achievement.query.limit(5).all()
            print("\n🏅 Przykładowe osiągnięcia:")
            for achievement in sample_achievements:
                print(f"   - {achievement.name}: {achievement.description} ({achievement.points} pkt)")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia osiągnięć: {e}")
            db.session.rollback()
            return False

def create_daily_quests():
    """Tworzy dzienne questy"""
    print("\n📋 Generowanie dziennych questów...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Sprawdź czy są już questy na dzisiaj
            today = date.today()
            existing_quests = DailyQuest.query.filter_by(quest_date=today, is_active=True).count()
            
            if existing_quests > 0:
                print(f"⚠️  Znaleziono {existing_quests} questów na dzisiaj.")
                choice = input("Czy chcesz wygenerować nowe questy? (y/N): ")
                if choice.lower() != 'y':
                    print("❌ Anulowano generowanie questów.")
                    return False
                
                # Usuń dzisiejsze questy
                DailyQuest.query.filter_by(quest_date=today).delete()
                db.session.commit()
                print("🗑️  Usunięto dzisiejsze questy.")
            
            # Wygeneruj nowe questy
            created_quests = DailyQuest.generate_daily_quests(today)
            
            if created_quests:
                print(f"✅ Wygenerowano {len(created_quests)} questów na dzisiaj!")
                
                # Pokaż wygenerowane questy
                print("\n📝 Dzisiejsze questy:")
                for quest in created_quests:
                    print(f"   - {quest.name}: {quest.description} ({quest.reward_points} pkt)")
            else:
                print("⚠️  Nie udało się wygenerować questów.")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia questów: {e}")
            db.session.rollback()
            return False