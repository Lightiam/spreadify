-- Create sp_options table
CREATE TABLE sp_options (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sp_users table
CREATE TABLE sp_users (
    id SERIAL PRIMARY KEY,
    ids VARCHAR(255) NOT NULL,
    fullname VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sp_purchases table
CREATE TABLE sp_purchases (
    id SERIAL PRIMARY KEY,
    ids VARCHAR(255) NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    is_main BOOLEAN DEFAULT FALSE,
    purchase_code VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sp_plans table
CREATE TABLE sp_plans (
    id SERIAL PRIMARY KEY,
    ids VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    billing_cycle VARCHAR(50),
    features TEXT,
    status BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert admin user
INSERT INTO sp_users (ids, fullname, username, email, password, timezone)
VALUES ('ADMIN_IDS', 'ADMIN_FULLNAME', 'ADMIN_USERNAME', 'ADMIN_EMAIL', 'ADMIN_PASSWORD', 'ADMIN_TIMEZONE');

-- Insert default options
INSERT INTO sp_options (name, value) VALUES
('website_title', 'Spreadify'),
('website_description', 'Social Marketing Tool'),
('website_keywords', 'social media, marketing, automation'),
('website_favicon', '/assets/img/favicon.png'),
('website_logo', '/assets/img/logo.png'),
('website_logo_mark', '/assets/img/logo-mark.png'),
('website_logo_color', '/assets/img/logo-color.png');
