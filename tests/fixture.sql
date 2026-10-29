-- Small database for the unit tests: same schema as data/pachaplan.sqlite, a handful of rows.
-- Reference date of the tests: 2026-11-02.

CREATE TABLE domain (
    domain_code TEXT PRIMARY KEY,
    label       TEXT NOT NULL
);
CREATE TABLE category (
    category_code TEXT PRIMARY KEY,
    label         TEXT NOT NULL,
    description   TEXT
);
CREATE TABLE language (
    language_code TEXT PRIMARY KEY,
    name          TEXT NOT NULL
);
CREATE TABLE session_status (
    status_code TEXT PRIMARY KEY,
    label       TEXT NOT NULL
);
CREATE TABLE company (
    company_id    INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    email_domain  TEXT NOT NULL,
    country_code  TEXT NOT NULL,
    sector        TEXT,
    discount      INTEGER NOT NULL,
    language_code TEXT NOT NULL REFERENCES language(language_code)
);
CREATE TABLE contact (
    contact_id INTEGER PRIMARY KEY,
    title      TEXT,
    last_name  TEXT NOT NULL,
    first_name TEXT,
    email      TEXT,
    company_id INTEGER REFERENCES company(company_id)
);
CREATE TABLE course (
    course_id         INTEGER PRIMARY KEY,
    code              TEXT,
    title             TEXT NOT NULL,
    domain_code       TEXT NOT NULL REFERENCES domain(domain_code),
    category_code     TEXT NOT NULL REFERENCES category(category_code),
    duration_days     INTEGER NOT NULL,
    max_attendees     INTEGER NOT NULL,
    created_on        TEXT NOT NULL,
    cancellation_date TEXT,
    company_id        INTEGER REFERENCES company(company_id)
);
CREATE TABLE location (
    location_id     INTEGER PRIMARY KEY,
    name            TEXT,
    postal_code     TEXT,
    city            TEXT,
    country_code    TEXT NOT NULL,
    is_pacha_center INTEGER NOT NULL,
    opening_date    TEXT NOT NULL,
    closing_date    TEXT,
    meal_flat_fee   NUMERIC NOT NULL
);
CREATE TABLE room (
    room_id     INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES location(location_id),
    name        TEXT,
    seats       INTEGER NOT NULL,
    floor       INTEGER
);
CREATE TABLE trainer (
    trainer_id     INTEGER PRIMARY KEY,
    contact_id     INTEGER NOT NULL REFERENCES contact(contact_id),
    status         TEXT,
    do_not_contact INTEGER NOT NULL,
    arrival_date   TEXT NOT NULL,
    departure_date TEXT
);
CREATE TABLE assignment (
    trainer_id  INTEGER NOT NULL REFERENCES trainer(trainer_id),
    location_id INTEGER NOT NULL REFERENCES location(location_id),
    start_date  TEXT NOT NULL,
    end_date    TEXT,
    PRIMARY KEY (trainer_id, location_id, start_date)
);
CREATE TABLE session (
    session_id    INTEGER PRIMARY KEY,
    course_id     INTEGER NOT NULL REFERENCES course(course_id),
    language_code TEXT NOT NULL REFERENCES language(language_code),
    room_id       INTEGER REFERENCES room(room_id),
    trainer_id    INTEGER REFERENCES trainer(trainer_id),
    company_id    INTEGER REFERENCES company(company_id),
    start_date    TEXT NOT NULL,
    duration_days INTEGER,
    price         NUMERIC,
    rating        INTEGER,
    status_code   TEXT REFERENCES session_status(status_code),
    is_in_house   INTEGER NOT NULL,
    remarks       TEXT,
    created_on    TEXT NOT NULL
);
CREATE TABLE engagement (
    engagement_id   INTEGER PRIMARY KEY,
    session_id      INTEGER NOT NULL REFERENCES session(session_id),
    trainer_id      INTEGER NOT NULL REFERENCES trainer(trainer_id),
    invoice_number  TEXT NOT NULL,
    invoice_date    TEXT NOT NULL,
    day_count       NUMERIC NOT NULL,
    daily_rate      NUMERIC NOT NULL,
    travel_expenses NUMERIC NOT NULL
);
CREATE TABLE enrollment (
    enrollment_id     INTEGER PRIMARY KEY,
    session_id        INTEGER NOT NULL REFERENCES session(session_id),
    contact_id        INTEGER REFERENCES contact(contact_id),
    created_at        TEXT NOT NULL,
    cancellation_date TEXT,
    discount          INTEGER NOT NULL,
    attended          INTEGER NOT NULL,
    waiting_list      INTEGER NOT NULL,
    order_reference   TEXT
);
CREATE TABLE invoice (
    invoice_code          TEXT PRIMARY KEY,
    document_type         TEXT NOT NULL,          -- I invoice, C credit note
    original_invoice_code TEXT REFERENCES invoice(invoice_code),
    session_id            INTEGER REFERENCES session(session_id),
    company_id            INTEGER REFERENCES company(company_id),
    contact_id            INTEGER REFERENCES contact(contact_id),
    invoice_date          TEXT,
    due_date              TEXT,
    net_amount            NUMERIC NOT NULL,
    gross_amount          NUMERIC NOT NULL,
    vat_rate              NUMERIC NOT NULL,
    discount              NUMERIC,
    reminder_level        INTEGER NOT NULL,
    reminder_date         TEXT,
    reason                TEXT
);
CREATE TABLE line_type (
    line_type_code TEXT PRIMARY KEY,
    label          TEXT NOT NULL
);
CREATE TABLE invoice_line (
    invoice_code   TEXT NOT NULL REFERENCES invoice(invoice_code),
    line_number    INTEGER NOT NULL,
    line_type_code TEXT NOT NULL REFERENCES line_type(line_type_code),
    enrollment_id  INTEGER REFERENCES enrollment(enrollment_id),
    label          TEXT NOT NULL,
    quantity       NUMERIC NOT NULL,
    unit_price     NUMERIC NOT NULL,
    net_amount     NUMERIC NOT NULL,
    PRIMARY KEY (invoice_code, line_number)
);
CREATE TABLE payment_method (
    payment_method_code TEXT PRIMARY KEY,
    label               TEXT NOT NULL
);
CREATE TABLE payment (
    payment_id          INTEGER PRIMARY KEY,
    invoice_code        TEXT NOT NULL REFERENCES invoice(invoice_code),
    payment_date        TEXT NOT NULL,
    amount              NUMERIC NOT NULL,
    payment_method_code TEXT NOT NULL REFERENCES payment_method(payment_method_code)
);

INSERT INTO domain VALUES ('DB', 'Databases');
INSERT INTO category VALUES ('SC', 'Scheduled course', NULL);
INSERT INTO language VALUES ('FR', 'Français');
INSERT INTO session_status VALUES
  ('CANCELED', 'Canceled'), ('COMPLETED', 'Completed'), ('CONFIRMED', 'Confirmed'),
  ('OPEN', 'Open for enrollment'), ('PLANNED', 'Planned');

INSERT INTO company VALUES (1, 'Durand Industries', 'durand-industries.example', 'FRA', 'Industrie', 0, 'FR');
INSERT INTO contact VALUES
  (1, 'Ms.', 'Martin', 'Claire', 'c.martin@durand-industries.example', 1),
  (2, 'Mr.', 'Petit', 'Louis', 'l.petit@durand-industries.example', 1),
  (3, 'Ms.', 'Roux', 'Anne', 'a.roux@durand-industries.example', 1),
  (4, 'Mr.', 'Fabre', 'Hugo', 'h.fabre@x.example', NULL),
  (10, 'Ms.', 'Lambert', 'Julie', 'j.lambert@x.example', NULL),
  (11, 'Mr.', 'Girard', 'Paul', 'p.girard@x.example', NULL);

INSERT INTO course VALUES
  (1, 'SQL-INTRO', 'SQL: getting started', 'DB', 'SC', 2, 10, '2020-01-01', NULL, NULL),
  (2, 'SQL-TUNE', 'SQL: query tuning', 'DB', 'SC', 3, 4, '2020-01-01', NULL, NULL);
INSERT INTO location VALUES
  (1, 'Centre Pacha Paris', '75011', 'Paris', 'FRA', 1, '2004-01-05', NULL, 29.5),
  (2, 'Centre Pacha Lyon', '69003', 'Lyon', 'FRA', 1, '2012-01-09', NULL, 24);
INSERT INTO room VALUES (1, 1, 'Codd', 12, 1), (2, 2, 'Date', 12, 2);
INSERT INTO trainer VALUES (1, 10, 'I', 0, '2015-01-01', NULL), (2, 11, 'E', 0, '2018-01-01', NULL);
INSERT INTO assignment VALUES (1, 1, '2026-01-01', NULL), (2, 2, '2026-01-01', NULL);

-- 101: 2 active enrollments out of 10 seats (20 %), one more canceled.
-- 102: 3 out of 4 (75 %). 103: canceled. 104: beyond the 30-day horizon. 105: past.
INSERT INTO session VALUES
  (101, 1, 'FR', 1, 1, NULL, '2026-11-10', 2, 1500, NULL, 'CONFIRMED', 0, NULL, '2026-06-01'),
  (102, 2, 'FR', 2, 2, NULL, '2026-11-12', 3, 2100, NULL, 'OPEN', 0, NULL, '2026-06-01'),
  (103, 1, 'FR', 1, 1, NULL, '2026-11-16', 2, 1500, NULL, 'CANCELED', 0, NULL, '2026-06-01'),
  (104, 1, 'FR', 1, 1, NULL, '2026-12-20', 2, 1500, NULL, 'PLANNED', 0, NULL, '2026-06-01'),
  (105, 1, 'FR', 1, 1, NULL, '2026-09-07', 2, 1500, NULL, 'COMPLETED', 0, NULL, '2026-03-01');
INSERT INTO enrollment VALUES
  (1, 101, 1, '2026-09-01 10:00:00', NULL, 0, 0, 0, NULL),
  (2, 101, 2, '2026-09-02 10:00:00', NULL, 0, 0, 0, NULL),
  (3, 101, 3, '2026-09-03 10:00:00', '2026-09-20', 0, 0, 0, NULL),
  (4, 102, 1, '2026-09-01 10:00:00', NULL, 0, 0, 0, NULL),
  (5, 102, 2, '2026-09-01 10:00:00', NULL, 0, 0, 0, NULL),
  (6, 102, 3, '2026-09-01 10:00:00', NULL, 0, 0, 0, NULL),
  (7, 105, 4, '2026-07-01 10:00:00', NULL, 0, 1, 0, NULL),
  (8, 105, 1, '2026-07-01 10:00:00', NULL, 0, 1, 0, NULL);

-- FA1 paid, FA2 open, FA3 canceled by the credit note AV1, FA4 open but recent.
INSERT INTO invoice VALUES
  ('FA1', 'I', NULL, 105, 1, NULL, '2026-09-01', '2026-10-01', 1000, 1200, 20, NULL, 0, NULL, NULL),
  ('FA2', 'I', NULL, 105, NULL, 4, '2026-09-15', '2026-10-15', 500, 600, 20, NULL, 1, '2026-10-20', NULL),
  ('FA3', 'I', NULL, 105, 1, NULL, '2026-09-20', '2026-10-20', 200, 240, 20, NULL, 0, NULL, NULL),
  ('AV1', 'C', 'FA3', 105, 1, NULL, '2026-09-25', NULL, -200, -240, 20, NULL, 0, NULL, 'Duplicate invoice'),
  ('FA4', 'I', NULL, 105, 1, NULL, '2026-10-20', '2026-11-19', 300, 360, 20, NULL, 0, NULL, NULL);
INSERT INTO line_type VALUES ('COUR', 'Training'), ('MEAL', 'Meals');
INSERT INTO invoice_line VALUES
  ('FA1', 1, 'COUR', 8, 'Training "SQL: getting started", Claire Martin', 2, 470.5, 941),
  ('FA1', 2, 'MEAL', 8, 'Lunches, 2 days, Claire Martin', 2, 29.5, 59),
  ('FA2', 1, 'COUR', 7, 'Training "SQL: getting started", Hugo Fabre', 2, 250, 500),
  ('FA3', 1, 'COUR', 8, 'Printed course materials, Claire Martin', 1, 200, 200),
  ('AV1', 1, 'COUR', 8, 'Duplicate invoice FA3', 1, -200, -200),
  ('FA4', 1, 'COUR', 8, 'Training "SQL: getting started", Claire Martin', 1, 300, 300);
INSERT INTO payment_method VALUES ('WIRE', 'Bank transfer');
INSERT INTO payment VALUES (1, 'FA1', '2026-09-28', 1200, 'WIRE');
