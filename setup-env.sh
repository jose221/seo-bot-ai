#!/bin/bash

echo "Setting up environment configuration files..."

if [ ! -f src/environments/environment.ts ]; then
  cp src/environments/environment.example.ts src/environments/environment.ts
  echo "✓ Created src/environments/environment.ts"
else
  echo "⚠ src/environments/environment.ts already exists, skipping..."
fi

if [ ! -f src/environments/environment.prod.ts ]; then
  cp src/environments/environment.example.ts src/environments/environment.prod.ts
  echo "✓ Created src/environments/environment.prod.ts"
else
  echo "⚠ src/environments/environment.prod.ts already exists, skipping..."
fi

echo ""
echo "Environment configuration complete!"
echo "Remember to update the files with your specific settings:"
echo "  - src/environments/environment.ts (development)"
echo "  - src/environments/environment.prod.ts (production)"

