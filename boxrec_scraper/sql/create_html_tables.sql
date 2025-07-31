-- Create tables for storing HTML content in the staging schema
-- This prevents needing to store HTML files locally

-- Table for boxer HTML pages
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".boxrec_html (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    boxrec_id VARCHAR(50),
    html_content TEXT NOT NULL,
    content_hash VARCHAR(64), -- SHA256 hash of HTML for deduplication
    language VARCHAR(10) DEFAULT 'en',
    page_type VARCHAR(50) DEFAULT 'boxer', -- 'boxer', 'bout', 'venue', etc.
    scrape_status VARCHAR(50) DEFAULT 'valid', -- 'valid', 'login_page', 'error', 'rate_limited'
    status_message TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url),
    INDEX idx_boxrec_id (boxrec_id),
    INDEX idx_page_type (page_type),
    INDEX idx_scrape_status (scrape_status),
    INDEX idx_scraped_at (scraped_at)
);

-- Table for bout/event HTML pages
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bout_html (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    event_id VARCHAR(50),
    html_content TEXT NOT NULL,
    content_hash VARCHAR(64),
    language VARCHAR(10) DEFAULT 'en',
    scrape_status VARCHAR(50) DEFAULT 'valid',
    status_message TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url),
    INDEX idx_event_id (event_id),
    INDEX idx_scrape_status (scrape_status),
    INDEX idx_scraped_at (scraped_at)
);

-- Table to track scraping queue and status
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".scrape_queue (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'boxer', 'bout', 'venue', etc.
    entity_id VARCHAR(50),
    priority INT DEFAULT 5, -- 1-10, lower is higher priority
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    attempts INT DEFAULT 0,
    last_attempt_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url),
    INDEX idx_status_priority (status, priority),
    INDEX idx_entity_type (entity_type),
    INDEX idx_created_at (created_at)
);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_boxrec_html_updated_at BEFORE UPDATE ON "data-pipelines-staging".boxrec_html
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bout_html_updated_at BEFORE UPDATE ON "data-pipelines-staging".bout_html
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scrape_queue_updated_at BEFORE UPDATE ON "data-pipelines-staging".scrape_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE "data-pipelines-staging".boxrec_html IS 'Stores raw HTML content for boxer pages';
COMMENT ON TABLE "data-pipelines-staging".bout_html IS 'Stores raw HTML content for bout/event pages';
COMMENT ON TABLE "data-pipelines-staging".scrape_queue IS 'Manages scraping queue and tracks scraping status';

COMMENT ON COLUMN "data-pipelines-staging".boxrec_html.scrape_status IS 'Status of the scrape: valid, login_page, error, rate_limited';
COMMENT ON COLUMN "data-pipelines-staging".boxrec_html.content_hash IS 'SHA256 hash of HTML content for detecting changes';
COMMENT ON COLUMN "data-pipelines-staging".scrape_queue.priority IS 'Priority 1-10, where 1 is highest priority';