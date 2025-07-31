-- Create tables for Events and Bouts in the staging schema
-- Events = fight cards/shows (e.g., a boxing event with multiple fights)
-- Bouts = individual fights between two boxers

-- Table for boxing events (fight cards)
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(500),
    date DATE,
    venue_id VARCHAR(50),
    venue_name VARCHAR(500),
    location VARCHAR(500),
    promoter VARCHAR(500),
    matchmaker VARCHAR(500),
    television VARCHAR(500),
    commission VARCHAR(500),
    attendance INT,
    gate_revenue VARCHAR(100),
    event_type VARCHAR(100), -- 'Pro Boxing', 'Amateur', etc.
    status VARCHAR(50), -- 'completed', 'scheduled', 'cancelled'
    bout_count INT,
    html_scraped BOOLEAN DEFAULT FALSE,
    data_extracted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_date (date),
    INDEX idx_venue_id (venue_id),
    INDEX idx_status (status)
);

-- Table for individual bouts/fights
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bouts (
    id SERIAL PRIMARY KEY,
    bout_id VARCHAR(100) UNIQUE NOT NULL, -- Composite of event_id and bout order
    event_id VARCHAR(50) NOT NULL,
    bout_order INT, -- Order in the event (1 = main event)
    boxer1_id VARCHAR(50),
    boxer1_name VARCHAR(200),
    boxer1_record_before VARCHAR(50), -- W-L-D format
    boxer1_hometown VARCHAR(200),
    boxer1_age INT,
    boxer1_weight DECIMAL(5,2),
    boxer1_height VARCHAR(20),
    boxer1_reach VARCHAR(20),
    boxer1_stance VARCHAR(20),
    boxer2_id VARCHAR(50),
    boxer2_name VARCHAR(200),
    boxer2_record_before VARCHAR(50),
    boxer2_hometown VARCHAR(200),
    boxer2_age INT,
    boxer2_weight DECIMAL(5,2),
    boxer2_height VARCHAR(20),
    boxer2_reach VARCHAR(20),
    boxer2_stance VARCHAR(20),
    weight_class VARCHAR(100),
    scheduled_rounds INT,
    actual_rounds INT,
    result VARCHAR(500), -- 'KO', 'TKO', 'UD', 'SD', 'MD', 'TD', 'DQ', 'NC', 'Draw'
    winner_id VARCHAR(50),
    method VARCHAR(100), -- How the fight ended
    time VARCHAR(20), -- Time of stoppage if applicable
    referee VARCHAR(200),
    judge1_name VARCHAR(200),
    judge1_score VARCHAR(50),
    judge2_name VARCHAR(200),
    judge2_score VARCHAR(50),
    judge3_name VARCHAR(200),
    judge3_score VARCHAR(50),
    titles VARCHAR(1000), -- JSON array of titles on the line
    bout_type VARCHAR(100), -- 'Title Fight', 'Eliminator', etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_id (event_id),
    INDEX idx_boxer1_id (boxer1_id),
    INDEX idx_boxer2_id (boxer2_id),
    INDEX idx_winner_id (winner_id),
    INDEX idx_weight_class (weight_class),
    INDEX idx_result (result),
    FOREIGN KEY (event_id) REFERENCES "data-pipelines-staging".events(event_id)
);

-- Table for round-by-round scoring (if available)
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bout_rounds (
    id SERIAL PRIMARY KEY,
    bout_id VARCHAR(100) NOT NULL,
    round_number INT NOT NULL,
    judge_name VARCHAR(200),
    boxer1_score INT,
    boxer2_score INT,
    notes VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bout_id, round_number, judge_name),
    FOREIGN KEY (bout_id) REFERENCES "data-pipelines-staging".bouts(bout_id)
);

-- Table for punch statistics (if available)
CREATE TABLE IF NOT EXISTS "data-pipelines-staging".bout_stats (
    id SERIAL PRIMARY KEY,
    bout_id VARCHAR(100) UNIQUE NOT NULL,
    boxer1_punches_landed INT,
    boxer1_punches_thrown INT,
    boxer1_punch_percentage DECIMAL(5,2),
    boxer1_jabs_landed INT,
    boxer1_jabs_thrown INT,
    boxer1_power_landed INT,
    boxer1_power_thrown INT,
    boxer2_punches_landed INT,
    boxer2_punches_thrown INT,
    boxer2_punch_percentage DECIMAL(5,2),
    boxer2_jabs_landed INT,
    boxer2_jabs_thrown INT,
    boxer2_power_landed INT,
    boxer2_power_thrown INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bout_id) REFERENCES "data-pipelines-staging".bouts(bout_id)
);

-- Update triggers for updated_at
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON "data-pipelines-staging".events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bouts_updated_at BEFORE UPDATE ON "data-pipelines-staging".bouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE "data-pipelines-staging".events IS 'Boxing events/fight cards containing multiple bouts';
COMMENT ON TABLE "data-pipelines-staging".bouts IS 'Individual boxing matches between two fighters';
COMMENT ON TABLE "data-pipelines-staging".bout_rounds IS 'Round-by-round scoring for bouts';
COMMENT ON TABLE "data-pipelines-staging".bout_stats IS 'Punch statistics for bouts';

COMMENT ON COLUMN "data-pipelines-staging".bouts.bout_id IS 'Unique identifier combining event_id and bout order';
COMMENT ON COLUMN "data-pipelines-staging".bouts.bout_order IS 'Order in event: 1=main event, higher numbers=earlier fights';
COMMENT ON COLUMN "data-pipelines-staging".bouts.result IS 'Fight result: KO, TKO, UD (Unanimous Decision), SD (Split Decision), etc.';