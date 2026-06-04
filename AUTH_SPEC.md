# DeltaGrid — Auth MVP (email + password + JWT)

## Контекст
- Проект: DeltaGrid, backtesting terminal для perpetual futures
- Путь: C:\Users\viach\OneDrive\Desktop\Deltagrid
- Backend: FastAPI, SQLAlchemy 2.0, SQLite (52 таблицы)
- Alembic head: d08fc5113b42
- Цель: простой email/password auth для будущего ЛК и SaaS

## Что реализовать

### 1. SQLAlchemy модель
Файл: backend/app/domain/models.py (добавить)

```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Расширение ЛК (пока nullable, для Phase B):
    # full_name = Column(String(255), nullable=True)
    # phone = Column(String(50), nullable=True)
    # api_key_coinglass = Column(String(255), nullable=True)
    # api_key_coingecko = Column(String(255), nullable=True)
    # subscription_tier = Column(String(50), default='free')
    # subscription_expires_at = Column(DateTime, nullable=True)
```

Alembic миграция: создать revision, добавить таблицу users.

### 2. Pydantic схемы
Файл: backend/app/schemas/auth.py (новый)

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime
```

### 3. Auth service
Файл: backend/app/services/auth_service.py (новый)

```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION"  # берется из .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except JWTError:
        return None
```

requirements.txt добавить:
```
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.6
pydantic[email]>=2.0
```

### 4. API endpoints
Файл: backend/app/api/v1/auth.py (новый)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/register", response_model=Token)
def register(body: UserCreate, db: Session = Depends(get_db)):
    # Проверить что email не занят
    # Hash password
    # Создать user
    # Вернуть JWT token

@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    # Найти user по email
    # Verify password
    # Вернуть JWT token

@router.get("/me", response_model=UserResponse)
def me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # Decode token → user_id
    # Вернуть user data
```

### 5. Optional auth dependency
Файл: backend/app/api/dependencies.py (новый или дополнить)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

security = HTTPBearer(auto_error=False)

def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Возвращает user если токен валиден, иначе None. Не падает."""
    if not credentials:
        return None
    user_id = decode_token(credentials.credentials)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()

def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Возвращает user или 401. Для защищенных endpoints."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

### 6. Подключение

main.py:
```python
from app.api.v1 import auth as auth_router
app.include_router(auth_router.router, prefix="/api/v1")
```

.env:
```
AUTH_SECRET_KEY=your-secret-key-change-in-production
AUTH_TOKEN_EXPIRE_DAYS=30
```

### 7. Интеграция с существующими endpoints

Существующие endpoints (backtest, data health) остаются БЕЗ auth для MVP.
Просто добавить опциональный user:

```python
@router.post("/run")
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    # user будет None для anonymous, User object для authenticated
    # пока не используем, но архитектурно заложено
```

## Приёмочные тесты

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# → {"access_token":"...","token_type":"bearer"}

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
# → {"access_token":"...","token_type":"bearer"}

# Me
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
# → {"id":1,"email":"test@example.com","is_active":true,...}

# Backtest without auth (still works)
curl -X POST http://localhost:8000/api/v1/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"strategy":"funding_mean_reversion","symbol":"BTC","days":30}'
# → works without token (optional auth)
```

## Правила
- Не ломай существующие endpoints (auth optional)
- Git commit
- .md на русском, код на английском
- SECRET_KEY из .env, не хардкодь в коде

## Ожидаемый результат
- [ ] users таблица (Alembic migration)
- [ ] POST /api/v1/auth/register
- [ ] POST /api/v1/auth/login
- [ ] GET /api/v1/auth/me
- [ ] JWT encode/decode
- [ ] bcrypt password hashing
- [ ] Optional auth dependency (не ломает существующее)
- [ ] requirements.txt обновлён
- [ ] uvicorn стартует
