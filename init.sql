-- Create tables for Douyin monitor

-- Accounts to monitor
CREATE TABLE monitored_accounts (
    id SERIAL PRIMARY KEY,
    douyin_id VARCHAR(100) NOT NULL UNIQUE,
    nickname VARCHAR(200),
    sec_uid VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    check_interval_minutes INTEGER DEFAULT 10,
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Live streaming sessions
CREATE TABLE live_sessions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES monitored_accounts(id),
    live_id VARCHAR(100) NOT NULL UNIQUE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    max_viewers INTEGER,
    avg_viewers INTEGER,
    total_likes BIGINT DEFAULT 0,
    total_comments BIGINT DEFAULT 0,
    total_shares BIGINT DEFAULT 0,
    total_gifts DECIMAL(15,2) DEFAULT 0,
    products_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ended',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Live session snapshots (time-series data)
CREATE TABLE live_snapshots (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES live_sessions(id),
    snapshot_time TIMESTAMP NOT NULL,
    viewers_count INTEGER,
    likes_count INTEGER,
    comments_count INTEGER,
    shares_count INTEGER,
    gifts_value DECIMAL(10,2),
    products JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products mentioned in live streams
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

-- Monitoring logs
CREATE TABLE monitoring_logs (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES monitored_accounts(id),
    check_time TIMESTAMP NOT NULL,
    is_live BOOLEAN DEFAULT FALSE,
    live_id VARCHAR(100),
    viewers_count INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts configuration
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    condition JSONB NOT NULL,
    channel VARCHAR(50) DEFAULT 'email',
    recipients TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_monitored_accounts_douyin_id ON monitored_accounts(douyin_id);
CREATE INDEX idx_live_sessions_account_start ON live_sessions(account_id, start_time);
CREATE INDEX idx_live_snapshots_session_time ON live_snapshots(session_id, snapshot_time);
CREATE INDEX idx_monitoring_logs_account_time ON monitoring_logs(account_id, check_time);
CREATE INDEX idx_live_sessions_live_id ON live_sessions(live_id);

-- Insert sample account for testing
INSERT INTO monitored_accounts (douyin_id, nickname, is_active, check_interval_minutes) 
VALUES 
    ('demo_account_1', '测试账号1', TRUE, 5),
    ('demo_account_2', '测试账号2', TRUE, 10);