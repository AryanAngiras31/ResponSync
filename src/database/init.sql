-- Drop tables if they exist to start fresh (for development/testing)
DROP TABLE IF EXISTS incidents;
DROP TABLE IF EXISTS resources;
DROP TABLE IF EXISTS allocations;

-- Create the incidents table
CREATE TABLE incidents (
    incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_latitude REAL NOT NULL,
    location_longitude REAL NOT NULL,
    address VARCHAR(255),
    pincode VARCHAR(6),
    severity INTEGER NOT NULL,
    type TEXT NOT NULL,
    report_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create the resources table
CREATE TABLE resources (
    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    current_latitude REAL NOT NULL,
    current_longitude REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('available', 'en_route', 'occupied'))
);

-- Create the allocations table
CREATE TABLE allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    assignment_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    predicted_response_time REAL, -- In minutes or seconds, specify in your code
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
    UNIQUE (incident_id)
);
