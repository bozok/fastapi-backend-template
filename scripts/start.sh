#!/bin/bash

# FastAPI Clean Project - Startup Script
# This script starts the application with proper database initialization

echo "🚀 Starting FastAPI Clean Project..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
while ! uv run python -c "
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

async def check_db():
    try:
        url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://fastapi_user:fastapi_password@localhost:5432/fastapi_db')
        # Parse the URL to get connection parameters
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 5432
        user = parsed.username
        password = parsed.password
        database = parsed.path.lstrip('/')
        
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        await conn.close()
        print('Database is ready!')
        return True
    except Exception as e:
        print(f'Database not ready: {e}')
        return False

asyncio.run(check_db())
"; do
  echo "⏳ Database not ready, waiting 2 seconds..."
  sleep 2
done

echo "✅ Database connection established!"

echo "🎯 Starting FastAPI application..."
echo "📊 Database tables will be created automatically by the lifespan event..."

# Start the application
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
