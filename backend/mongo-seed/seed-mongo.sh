#!/bin/bash
# Seed MongoDB with exported collections.
# Runs as a separate container that connects to the 'mongo' service.
# Uses --drop to replace existing data, making it safe to re-run.

set -e

DB_NAME="tenderec"
MONGO_HOST="mongo"
SEED_DIR="/seed"

echo "=== Seeding MongoDB database '$DB_NAME' on host '$MONGO_HOST' ==="

for file in "$SEED_DIR"/*.json; do
  [ -f "$file" ] || continue
  collection=$(basename "$file" .json)
  echo "  Importing collection '$collection' from $(basename "$file")..."
  mongoimport --host "$MONGO_HOST" --db "$DB_NAME" --collection "$collection" \
    --jsonArray --drop --file "$file"
done

echo "=== MongoDB seeding complete ==="
