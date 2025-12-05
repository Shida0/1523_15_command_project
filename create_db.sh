#!/bin/bash
sudo -u postgres psql << EOF
CREATE USER administrator WITH PASSWORD 'strong_password';
CREATE DATABASE asteroid_watch_db 
    ENCODING 'UTF8' 
    LC_COLLATE 'en_US.UTF-8' 
    LC_CTYPE 'en_US.UTF-8' 
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE asteroid_watch_db TO administrator;
\c asteroid_watch_db
GRANT ALL ON SCHEMA public TO administrator;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO administrator;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO administrator;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO administrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO administrator;
EOF