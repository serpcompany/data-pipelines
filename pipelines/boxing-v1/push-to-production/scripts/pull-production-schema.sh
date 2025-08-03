#!/bin/bash

# Pull the latest schema from production database
echo "🔍 Introspecting production database schema..."

# Create schema directory if it doesn't exist
mkdir -p src/schema

# Run drizzle-kit introspect to generate TypeScript schema from database
pnpm dlx drizzle-kit introspect:mysql

# Move generated schema to src/schema
mv drizzle/* src/schema/ 2>/dev/null || true

echo "✅ Schema pulled successfully!"
echo "📁 Schema files are in src/schema/"

# Show what tables were found
echo ""
echo "📊 Tables found:"
ls -la src/schema/*.ts | awk '{print "  - " $9}'