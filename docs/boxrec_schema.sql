-- BoxRec Database Schema
-- Extracted from BoxRec.com HTML entity pages

-- Boxers/Fighters table
CREATE TABLE boxers (
    boxer_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    gender ENUM('male', 'female'),
    nationality VARCHAR(3),  -- Country code
    residence VARCHAR(255),
    age INTEGER,
    division VARCHAR(50),
    ranking INTEGER,
    record_wins INTEGER DEFAULT 0,
    record_losses INTEGER DEFAULT 0,
    record_draws INTEGER DEFAULT 0,
    career_start_year INTEGER,
    career_end_year INTEGER,
    last_6_results VARCHAR(6),  -- e.g., 'WWLWDL'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Venues/Locations table
CREATE TABLE venues (
    venue_id INTEGER PRIMARY KEY,
    venue_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state_region VARCHAR(100),
    country VARCHAR(100),
    country_code VARCHAR(3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events table
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    event_date DATE NOT NULL,
    venue_id INTEGER,
    promoter_id INTEGER,
    matchmaker_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
);

-- Bouts/Fights table
CREATE TABLE bouts (
    bout_id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    bout_date DATE NOT NULL,
    boxer_1_id INTEGER NOT NULL,
    boxer_2_id INTEGER NOT NULL,
    boxer_1_weight DECIMAL(5,2),
    boxer_2_weight DECIMAL(5,2),
    result VARCHAR(10),  -- W-TKO, W-UD, W-SD, L, D
    result_details VARCHAR(20),  -- TKO, KO, UD, SD, MD
    winner_id INTEGER,
    round_ended INTEGER,
    total_rounds INTEGER,
    venue_id INTEGER,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (boxer_1_id) REFERENCES boxers(boxer_id),
    FOREIGN KEY (boxer_2_id) REFERENCES boxers(boxer_id),
    FOREIGN KEY (winner_id) REFERENCES boxers(boxer_id),
    FOREIGN KEY (venue_id) REFERENCES venues(venue_id)
);

-- Titles table
CREATE TABLE titles (
    title_id INTEGER PRIMARY KEY,
    organization VARCHAR(10),  -- WBC, WBO, IBF, WBA
    weight_class VARCHAR(50),
    title_type VARCHAR(20),  -- World, Regional
    supervisor_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Title Bouts junction table
CREATE TABLE title_bouts (
    bout_id INTEGER NOT NULL,
    title_id INTEGER NOT NULL,
    defending_boxer_id INTEGER,
    challenging_boxer_id INTEGER,
    PRIMARY KEY (bout_id, title_id),
    FOREIGN KEY (bout_id) REFERENCES bouts(bout_id),
    FOREIGN KEY (title_id) REFERENCES titles(title_id),
    FOREIGN KEY (defending_boxer_id) REFERENCES boxers(boxer_id),
    FOREIGN KEY (challenging_boxer_id) REFERENCES boxers(boxer_id)
);

-- Clubs/Gyms table
CREATE TABLE clubs (
    club_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    state_region VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    type ENUM('box-am', 'box-pro', 'both'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personnel table (promoters, referees, judges, etc.)
CREATE TABLE personnel (
    person_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role ENUM('promoter', 'matchmaker', 'inspector', 'doctor', 'supervisor', 'referee', 'judge'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event Personnel junction table
CREATE TABLE event_personnel (
    event_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    role VARCHAR(50),
    PRIMARY KEY (event_id, person_id, role),
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (person_id) REFERENCES personnel(person_id)
);

-- Scoring table
CREATE TABLE scoring (
    bout_id INTEGER NOT NULL,
    judge_id INTEGER NOT NULL,
    judge_score VARCHAR(20),  -- e.g., "115-113"
    fan_score VARCHAR(20),    -- e.g., "112-116"
    PRIMARY KEY (bout_id, judge_id),
    FOREIGN KEY (bout_id) REFERENCES bouts(bout_id),
    FOREIGN KEY (judge_id) REFERENCES personnel(person_id)
);

-- Ratings table
CREATE TABLE ratings (
    boxer_id INTEGER NOT NULL,
    rating_date DATE NOT NULL,
    division VARCHAR(50),
    rank INTEGER,
    points DECIMAL(10,2),
    PRIMARY KEY (boxer_id, rating_date, division),
    FOREIGN KEY (boxer_id) REFERENCES boxers(boxer_id)
);

-- Boxer Club affiliations
CREATE TABLE boxer_clubs (
    boxer_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    PRIMARY KEY (boxer_id, club_id),
    FOREIGN KEY (boxer_id) REFERENCES boxers(boxer_id),
    FOREIGN KEY (club_id) REFERENCES clubs(club_id)
);

-- Indexes for performance
CREATE INDEX idx_bouts_date ON bouts(bout_date);
CREATE INDEX idx_bouts_boxer1 ON bouts(boxer_1_id);
CREATE INDEX idx_bouts_boxer2 ON bouts(boxer_2_id);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_events_venue ON events(venue_id);
CREATE INDEX idx_boxers_division ON boxers(division);
CREATE INDEX idx_boxers_ranking ON boxers(ranking);
CREATE INDEX idx_ratings_date ON ratings(rating_date);