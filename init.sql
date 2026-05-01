-- Create tables for Douyin competitor live monitor

CREATE TABLE monitored_accounts (
    id SERIAL PRIMARY KEY,
    douyin_id VARCHAR(100) NOT NULL UNIQUE,
    nickname VARCHAR(200),
    sec_uid VARCHAR(200),
    live_room_id VARCHAR(100),
    live_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    check_interval_minutes INTEGER DEFAULT 10,
    last_checked TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,
    cooldown_until TIMESTAMP,
    risk_status VARCHAR(40) DEFAULT 'normal',
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE live_sessions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES monitored_accounts(id),
    live_id VARCHAR(100) NOT NULL UNIQUE,
    room_id VARCHAR(100),
    live_url VARCHAR(500),
    title VARCHAR(500),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    max_viewers INTEGER,
    avg_viewers INTEGER,
    max_enter_count INTEGER,
    avg_enter_count INTEGER,
    total_likes BIGINT DEFAULT 0,
    total_comments BIGINT DEFAULT 0,
    total_shares BIGINT DEFAULT 0,
    total_gifts DECIMAL(15,2) DEFAULT 0,
    products_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ended',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE live_snapshots (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES live_sessions(id),
    snapshot_time TIMESTAMP NOT NULL,
    viewers_count INTEGER,
    enter_count INTEGER,
    likes_count INTEGER,
    comments_count INTEGER,
    shares_count INTEGER,
    gifts_value DECIMAL(10,2),
    products JSONB,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE live_products (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES live_sessions(id),
    product_id VARCHAR(100),
    product_name VARCHAR(500),
    price DECIMAL(10,2),
    sales_count INTEGER,
    platform VARCHAR(50),
    mentioned_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE monitoring_logs (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES monitored_accounts(id),
    check_time TIMESTAMP NOT NULL,
    is_live BOOLEAN DEFAULT FALSE,
    live_id VARCHAR(100),
    viewers_count INTEGER,
    enter_count INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    risk_status VARCHAR(40) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    condition JSONB NOT NULL,
    channel VARCHAR(50) DEFAULT 'email',
    recipients TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitored_accounts_douyin_id ON monitored_accounts(douyin_id);
CREATE INDEX idx_monitored_accounts_risk ON monitored_accounts(risk_status, cooldown_until);
CREATE INDEX idx_live_sessions_account_start ON live_sessions(account_id, start_time);
CREATE INDEX idx_live_sessions_status ON live_sessions(status);
CREATE INDEX idx_live_snapshots_session_time ON live_snapshots(session_id, snapshot_time);
CREATE INDEX idx_monitoring_logs_account_time ON monitoring_logs(account_id, check_time);
CREATE INDEX idx_live_sessions_live_id ON live_sessions(live_id);
