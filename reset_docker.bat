@echo off
echo ============================================
echo  ScopeSentinel - Docker Full Reset
echo  This removes OLD conflicting containers
echo  and volumes, then starts fresh.
echo ============================================

echo.
echo [1/5] Stopping and removing old containers...
docker stop scopesentinel_postgres scopesentinel_redis scopesentinel_qdrant scopesentinel_neo4j scopesentinel_mongodb 2>nul
docker rm scopesentinel_postgres scopesentinel_redis scopesentinel_qdrant scopesentinel_neo4j scopesentinel_mongodb 2>nul

echo.
echo [2/5] Removing OLD volumes (old project had different credentials)...
docker volume rm ss_fixed_postgres_data 2>nul
docker volume rm scopesentinel_postgres_data 2>nul
docker volume rm backend_postgres_data 2>nul

echo.
echo [3/5] Starting fresh containers with new volume names...
docker compose up -d

echo.
echo [4/5] Waiting 25 seconds for Postgres to initialize...
timeout /t 25 /nobreak >nul

echo.
echo [5/5] Testing Postgres connection...
docker exec scopesentinel_postgres psql -U scopeuser -d scopesentinel -c "SELECT 1;"

echo.
echo ============================================
echo  If you see "1 row" above, it WORKED!
echo  Now run: cd backend ^&^& alembic upgrade head
echo ============================================
pause
