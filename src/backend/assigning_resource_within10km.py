import pandas as pd
import numpy as np
from geopy.distance import geodesic

incident_data = pd.read_csv("incident_data.csv")
resource_inventory = pd.read_csv("resource_table.csv")

incident_data.columns = incident_data.columns.str.strip().str.lower()
resource_inventory.columns = resource_inventory.columns.str.strip().str.lower()

#assigning resouces forvarioua incidents ig
def simulate_resources(row):
    severity = row["severity"]
    incident_type = row["type"].lower()

    base = severity * 2
    if incident_type == "fire":
        base += 3
    elif incident_type == "medical":
        base += 2
    elif incident_type == "accident":
        base += 1
    elif incident_type == "crime":
        base += 2
    else:
        base += 1

    noise = np.random.randint(-1, 2)
    return max(1, base + noise)

incident_data["resources_required"] = incident_data.apply(simulate_resources, axis=1)


assignments = []
incident_data = incident_data.sort_values(by="severity", ascending=False)

for _, row in incident_data.iterrows():
    incident_location = (row["location_latitude"], row["location_longitude"])
    incident_type = row["type"].lower()

    candidates = resource_inventory[
        (resource_inventory["status"].str.lower() == "available") &
        (resource_inventory["type"].str.lower().str.contains(incident_type))
    ].copy()

    if candidates.empty:
        assigned_resource = "No available resource"
        distance = None
    else:
        # Calculating distance
        candidates["distance"] = candidates.apply(
            lambda r: geodesic(
                incident_location,
                (r["current latitude"], r["current longitude"])
            ).kilometers,
            axis=1
        )
        candidates_within_radius = candidates[candidates["distance"] <= 10]#resources within 10 km

        if candidates_within_radius.empty:
            assigned_resource = "No resource within 10km"
            distance = None
        else:
           
            nearest = candidates_within_radius.loc[candidates_within_radius["distance"].idxmin()]
            assigned_resource = nearest["type"]
            distance = nearest["distance"]

            resource_inventory.loc[resource_inventory["resource_id"] == nearest["resource_id"], "status"] = "allocated"

    assignments.append({
        "Incident ID": row["incident_id"],
        "Type": row["type"],
        "Severity": row["severity"],
        "Resources Required": row["resources_required"],
        "Assigned Resource": assigned_resource,
        "Distance to Resource (km)": round(distance, 2) if distance is not None else "N/A"
    })
assignments_df = pd.DataFrame(assignments)
print(assignments_df)

assignments_df.to_csv("incident_assignments1.csv", index=False)
