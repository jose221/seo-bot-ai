"""
Script de prueba para verificar la estructura del código sin base de datos.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Verifica que todos los módulos se importen correctamente"""
    print("🧪 Probando imports...")

    try:
        from app.core.config import settings
        print("✅ Config: OK")
        print(f"   - Project: {settings.PROJECT_NAME}")
        print(f"   - Version: {settings.VERSION}")
    except Exception as e:
        print(f"❌ Config: {e}")
        return False

    try:
        from app.schemas.auth_schemas import LoginRequest, RegisterRequest
        print("✅ Auth Schemas: OK")
    except Exception as e:
        print(f"❌ Auth Schemas: {e}")
        return False

    try:
        from app.models.user import User
        print("✅ User Model: OK")
    except Exception as e:
        print(f"❌ User Model: {e}")
        return False

    try:
        from app.services.auth_provider import auth_provider
        print("✅ Auth Provider: OK")
        print(f"   - Base URL: {auth_provider.base_url}")
    except Exception as e:
        print(f"❌ Auth Provider: {e}")
        return False

    try:
        from app.api.v1.endpoints.auth import router
        print("✅ Auth Router: OK")
        print(f"   - Prefix: {router.prefix}")
    except Exception as e:
        print(f"❌ Auth Router: {e}")
        return False

    return True


def test_schemas():
    """Verifica la validación de schemas"""
    print("\n🧪 Probando validación de schemas...")

    from app.schemas.auth_schemas import LoginRequest, RegisterRequest

    try:
        # Test LoginRequest
        login = LoginRequest(
            email="test@example.com",
            password="securepass"
        )
        print(f"✅ LoginRequest: {login.email}")

        # Test RegisterRequest
        register = RegisterRequest(
            email="new@example.com",
            password="securepass",
            full_name="Test User",
            username="testuser",
            city="Mexico City",
            country_code="MX"
        )
        print(f"✅ RegisterRequest: {register.email}")

        return True
    except Exception as e:
        print(f"❌ Schema validation: {e}")
        return False


def main():
    print("=" * 60)
    print("🚀 SEO BOT AI - TEST DE ESTRUCTURA")
    print("=" * 60)
    print()

    all_ok = True

    # Test imports
    if not test_imports():
        all_ok = False

    # Test schemas
    if not test_schemas():
        all_ok = False

    print()
    print("=" * 60)
    if all_ok:
        print("✅ TODOS LOS TESTS PASARON")
        print("=" * 60)
        print()
        print("📝 Notas:")
        print("   - La estructura del código es correcta")
        print("   - Todos los módulos se importan sin errores")
        print("   - Los schemas validan correctamente")
        print()
        print("⚠️  Para iniciar la aplicación completa:")
        print("   1. Inicia PostgreSQL: docker-compose up -d db")
        print("   2. O usa: docker-compose up")
        print()
        return 0
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

