import sqlite3
from flask import Flask, request, jsonify, g

DATABASE = '../database/responsync.db' # Adjust path as needed

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False # Keep JSON order as is

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row # Return rows as dictionary-like objects
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()

def query_db(query, args=(), one=False):
    """Helper function to query the database."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Helper function to execute commands (INSERT, UPDATE, DELETE)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

# --- Incident Endpoints (CRD) ---

@app.route('/incidents', methods=['POST'])
def create_incident():
    """Creates a new incident."""
    data = request.get_json()
    if not data or not all(k in data for k in ('location_latitude', 'location_longitude', 'severity', 'type')):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        incident_id = execute_db(
            'INSERT INTO incidents (location_latitude, location_longitude, severity, type) VALUES (?, ?, ?, ?)',
            [data['location_latitude'], data['location_longitude'], data['severity'], data['type']]
        )
        new_incident = query_db('SELECT * FROM incidents WHERE incident_id = ?', [incident_id], one=True)
        return jsonify(dict(new_incident)), 201
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/incidents', methods=['GET'])
def get_incidents():
    """Retrieves all incidents."""
    try:
        incidents = query_db('SELECT * FROM incidents')
        return jsonify([dict(ix) for ix in incidents]), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/incidents/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Retrieves a specific incident by ID."""
    try:
        incident = query_db('SELECT * FROM incidents WHERE incident_id = ?', [incident_id], one=True)
        if incident is None:
            return jsonify({"error": "Incident not found"}), 404
        return jsonify(dict(incident)), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/incidents/<int:incident_id>', methods=['DELETE'])
def delete_incident(incident_id):
    """Deletes an incident by ID."""
    try:
        # Optional: Check if incident exists before deleting
        incident = query_db('SELECT 1 FROM incidents WHERE incident_id = ?', [incident_id], one=True)
        if incident is None:
            return jsonify({"error": "Incident not found"}), 404

        execute_db('DELETE FROM incidents WHERE incident_id = ?', [incident_id])
        # Consider deleting related allocations as well, or handle foreign key constraints
        # execute_db('DELETE FROM allocations WHERE incident_id = ?', [incident_id])
        return jsonify({"message": "Incident deleted successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


# --- Resource Endpoints (CRUD) ---

@app.route('/resources', methods=['POST'])
def create_resource():
    """Creates a new resource."""
    data = request.get_json()
    if not data or not all(k in data for k in ('type', 'current_latitude', 'current_longitude', 'status')):
        return jsonify({"error": "Missing required fields"}), 400
    if data.get('status') not in ('available', 'en_route', 'occupied'):
         return jsonify({"error": "Invalid status value"}), 400

    try:
        resource_id = execute_db(
            'INSERT INTO resources (type, current_latitude, current_longitude, status) VALUES (?, ?, ?, ?)',
            [data['type'], data['current_latitude'], data['current_longitude'], data['status']]
        )
        new_resource = query_db('SELECT * FROM resources WHERE resource_id = ?', [resource_id], one=True)
        return jsonify(dict(new_resource)), 201
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/resources', methods=['GET'])
def get_resources():
    """Retrieves all resources."""
    try:
        resources = query_db('SELECT * FROM resources')
        return jsonify([dict(res) for res in resources]), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    """Retrieves a specific resource by ID."""
    try:
        resource = query_db('SELECT * FROM resources WHERE resource_id = ?', [resource_id], one=True)
        if resource is None:
            return jsonify({"error": "Resource not found"}), 404
        return jsonify(dict(resource)), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/resources/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    """Updates an existing resource."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for update"}), 400

    # Build the update query dynamically based on provided fields
    fields = []
    values = []
    allowed_fields = ['type', 'current_latitude', 'current_longitude', 'status']

    for field in allowed_fields:
        if field in data:
            if field == 'status' and data[field] not in ('available', 'en_route', 'occupied'):
                 return jsonify({"error": "Invalid status value"}), 400
            fields.append(f"{field} = ?")
            values.append(data[field])

    if not fields:
        return jsonify({"error": "No valid fields provided for update"}), 400

    values.append(resource_id) # Add resource_id for the WHERE clause
    query = f"UPDATE resources SET {', '.join(fields)} WHERE resource_id = ?"

    try:
        # Check if resource exists
        resource = query_db('SELECT 1 FROM resources WHERE resource_id = ?', [resource_id], one=True)
        if resource is None:
            return jsonify({"error": "Resource not found"}), 404

        execute_db(query, values)
        updated_resource = query_db('SELECT * FROM resources WHERE resource_id = ?', [resource_id], one=True)
        return jsonify(dict(updated_resource)), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


@app.route('/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    """Deletes a resource by ID."""
    try:
        # Optional: Check if resource exists before deleting
        resource = query_db('SELECT 1 FROM resources WHERE resource_id = ?', [resource_id], one=True)
        if resource is None:
            return jsonify({"error": "Resource not found"}), 404

        execute_db('DELETE FROM resources WHERE resource_id = ?', [resource_id])
        # Consider deleting related allocations as well, or handle foreign key constraints
        # execute_db('DELETE FROM allocations WHERE resource_id = ?', [resource_id])
        return jsonify({"message": "Resource deleted successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


# --- Allocation Endpoints (CRD) ---

@app.route('/allocations', methods=['POST'])
def create_allocation():
    """Creates a new allocation record."""
    data = request.get_json()
    if not data or not all(k in data for k in ('incident_id', 'resource_id')):
        return jsonify({"error": "Missing required fields (incident_id, resource_id)"}), 400

    # Optional: Add predicted_response_time if provided
    predicted_time = data.get('predicted_response_time') # Can be None

    try:
        # Check if incident and resource exist
        incident = query_db('SELECT 1 FROM incidents WHERE incident_id = ?', [data['incident_id']], one=True)
        resource = query_db('SELECT 1 FROM resources WHERE resource_id = ?', [data['resource_id']], one=True)
        if not incident:
            return jsonify({"error": f"Incident with ID {data['incident_id']} not found"}), 404
        if not resource:
            return jsonify({"error": f"Resource with ID {data['resource_id']} not found"}), 404

        # Check for UNIQUE constraint on incident_id (only one allocation per incident)
        existing_allocation = query_db('SELECT 1 FROM allocations WHERE incident_id = ?', [data['incident_id']], one=True)
        if existing_allocation:
             return jsonify({"error": f"Incident {data['incident_id']} already has an allocation"}), 409 # Conflict

        allocation_id = execute_db(
            'INSERT INTO allocations (incident_id, resource_id, predicted_response_time) VALUES (?, ?, ?)',
            [data['incident_id'], data['resource_id'], predicted_time]
        )
        new_allocation = query_db('SELECT * FROM allocations WHERE allocation_id = ?', [allocation_id], one=True)

        # Optionally update resource status to 'en_route' upon allocation
        execute_db('UPDATE resources SET status = ? WHERE resource_id = ?', ['en_route', data['resource_id']])

        return jsonify(dict(new_allocation)), 201
    except sqlite3.IntegrityError as e:
         # Catch potential foreign key or unique constraint errors not caught above
         return jsonify({"error": f"Database integrity error: {e}"}), 400
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/allocations', methods=['GET'])
def get_allocations():
    """Retrieves all allocation records."""
    try:
        # Join with incidents and resources for more context (optional)
        allocations = query_db('''
            SELECT a.*, i.type as incident_type, r.type as resource_type
            FROM allocations a
            JOIN incidents i ON a.incident_id = i.incident_id
            JOIN resources r ON a.resource_id = r.resource_id
        ''')
        # If you only want allocation table data:
        # allocations = query_db('SELECT * FROM allocations')
        return jsonify([dict(alloc) for alloc in allocations]), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/allocations/<int:allocation_id>', methods=['GET'])
def get_allocation(allocation_id):
    """Retrieves a specific allocation by ID."""
    try:
        allocation = query_db('SELECT * FROM allocations WHERE allocation_id = ?', [allocation_id], one=True)
        if allocation is None:
            return jsonify({"error": "Allocation not found"}), 404
        return jsonify(dict(allocation)), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500

@app.route('/allocations/<int:allocation_id>', methods=['DELETE'])
def delete_allocation(allocation_id):
    """Deletes an allocation by ID."""
    try:
        # Optional: Check if allocation exists before deleting
        allocation = query_db('SELECT resource_id FROM allocations WHERE allocation_id = ?', [allocation_id], one=True)
        if allocation is None:
            return jsonify({"error": "Allocation not found"}), 404

        execute_db('DELETE FROM allocations WHERE allocation_id = ?', [allocation_id])

        # Optionally update the previously allocated resource status back to 'available'
        # Be careful: Only do this if the resource isn't immediately re-allocated or occupied
        # resource_id = allocation['resource_id']
        # execute_db('UPDATE resources SET status = ? WHERE resource_id = ? AND status = ?', ['available', resource_id, 'en_route'])

        return jsonify({"message": "Allocation deleted successfully"}), 200
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {e}"}), 500


# --- Main Execution ---
if __name__ == '__main__':
    # You might want to initialize the DB schema here if the file doesn't exist
    # import os
    # if not os.path.exists(DATABASE):
    #     conn = sqlite3.connect(DATABASE)
    #     with open('../database/init.sql', 'r') as f: # Adjust path
    #         conn.executescript(f.read())
    #     conn.close()
    #     print("Database initialized.")

    app.run(debug=True) # debug=True is helpful for development