from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.config import settings
from app.database import Base, engine
from app.limiter import limiter
from app.routers import auth, users, records, dashboard
from contextlib import asynccontextmanager
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan, 
    description="""
## Finance Data Processing & Access Control Backend

A structured backend for a finance dashboard system with **role-based access control**,
financial record management, and analytics APIs.

### Roles
| Role     | Capabilities |
|----------|-------------|
| **admin**    | Full access: manage users, create/update/delete records |
| **analyst**  | Read records + dashboard analytics |
| **viewer**   | Read-only access to records and summaries |

    """,
    contact={"name": "Paras", "email": "gcloud.paras28@gmail.com"},
    license_info={"name": "MIT"},
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request ID Middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())[:8]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ─── Global Validation Error Handler ──────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({"field": field, "message": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": errors},
    )

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)

# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
def health_check():
    """Returns API status and version. No authentication required."""
    return {"status": "ok", "version": settings.app_version, "app": settings.app_name}

# ─── Auto-SEED ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-seed if database is empty
    from app.database import SessionLocal
    from app.models import User
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.close()
            import subprocess
            subprocess.run(["python", "seed.py"], check=True)
        else:
            db.close()
    except Exception as e:
        db.close()
        print(f"Auto-seed skipped: {e}")
    
    yield 