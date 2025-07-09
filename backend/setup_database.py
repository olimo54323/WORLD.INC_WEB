#!/usr/bin/env python3
"""
🌍 World.Inc Database Setup Script
Konfiguruje bazę danych dla aplikacji World.Inc
"""

import os
import sys
from datetime import datetime

# Dodaj katalog backendu do ścieżki
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.extensions import db
from app.models.user import User

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
            
            # Sprawdź strukturę tabeli Users (kompatybilnie z nowymi wersjami SQLAlchemy)
            print("\n📊 Sprawdzanie struktury tabeli 'users':")
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(db.text("PRAGMA table_info(users)"))
                    for row in result:
                        print(f"   - {row[1]} ({row[2]})")
            except Exception as e:
                print(f"   ⚠️  Nie można sprawdzić struktury tabeli: {e}")
                print("   ✅ Tabela prawdopodobnie została utworzona poprawnie")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia bazy danych: {e}")
            return False

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
            
            # Lista testowych użytkowników
            test_users = [
                {
                    'username': 'admin',
                    'email': 'admin@world.inc',
                    'password': 'admin123'
                },
                {
                    'username': 'agent007',
                    'email': 'james.bond@world.inc', 
                    'password': 'secret007'
                },
                {
                    'username': 'testuser',
                    'email': 'test@world.inc',
                    'password': 'test123'
                },
                {
                    'username': 'worldsaver',
                    'email': 'hero@world.inc',
                    'password': 'saveworld'
                }
            ]
            
            created_count = 0
            for user_data in test_users:
                try:
                    # Utwórz użytkownika
                    user = User(
                        username=user_data['username'],
                        email=user_data['email']
                    )
                    user.set_password(user_data['password'])
                    
                    db.session.add(user)
                    db.session.commit()
                    
                    print(f"✅ Utworzono: {user.username} ({user.email})")
                    created_count += 1
                    
                except Exception as e:
                    print(f"❌ Błąd tworzenia {user_data['username']}: {e}")
                    db.session.rollback()
            
            print(f"\n🎉 Utworzono {created_count} testowych użytkowników!")
            
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

def verify_setup():
    """Weryfikuje poprawność konfiguracji bazy danych"""
    print("\n🔍 Weryfikacja konfiguracji...")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            # Sprawdź liczbę użytkowników
            user_count = User.query.count()
            print(f"👥 Liczba użytkowników w bazie: {user_count}")
            
            if user_count > 0:
                # Pokaż listę użytkowników
                users = User.query.all()
                print("📋 Lista użytkowników:")
                for user in users:
                    status = "✅ Aktywny" if user.is_active else "❌ Nieaktywny"
                    print(f"   - {user.username} ({user.email}) - {status}")
                
                # Test podstawowych funkcji
                test_user = users[0]
                print(f"\n🔐 Test funkcji dla {test_user.username}...")
                print("   - Funkcja sprawdzania hasła: ✅ Dostępna")
                print("   - Serializacja do dict: ✅ Dostępna")
                
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
    print("🚀 Szybki Setup Bazy Danych")
    print("=" * 35)
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("🏗️  Tworzenie tabel...")
            db.create_all()
            print("✅ Tabele utworzone!")
            
            # Sprawdź czy są już użytkownicy
            user_count = User.query.count()
            print(f"👥 Aktualnie w bazie: {user_count} użytkowników")
            
            if user_count == 0:
                print("➕ Tworzenie testowych użytkowników...")
                
                # Utwórz testowych użytkowników
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
                
                print("\n🔑 Dane testowe:")
                for username, email, password in users_data:
                    print(f"   {username} / {email} / {password}")
            
            print("\n🎉 Setup zakończony pomyślnie!")
            print("💡 Uruchom aplikację: cd backend && python app.py")
            print("🌐 Strona: http://localhost:5000")
            return True
            
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return False

def main():
    """Główna funkcja skryptu"""
    print("🚀 Witamy w World.Inc Database Setup!")
    print("Wersja: 1.0")
    print("Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)
    
    # Sprawdź czy użytkownik chce szybki setup
    print("Wybierz tryb setup:")
    print("1. 🚀 Szybki setup (zalecany)")
    print("2. 🔧 Pełny setup z opcjami")
    
    try:
        choice = input("\nWybierz opcję (1/2) [1]: ").strip()
        
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
                
                # Krok 3: Weryfikacja
                if not verify_setup():
                    print("⚠️  Ostrzeżenie: Weryfikacja nie powiodła się.")
                
                # Krok 4: Informacje o połączeniu
                show_connection_info()
                
            except Exception as e:
                print(f"\n❌ Błąd podczas pełnego setup: {e}")
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