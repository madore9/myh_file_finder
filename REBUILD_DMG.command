#!/bin/bash
# Rebuild Large File Finder .app and DMG after code changes.
# Double-click to run, or: ./REBUILD_DMG.command

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo ""
echo "Rebuilding Large File Finder DMG..."
echo ""

./build_dmg.sh

echo ""
echo "Opening folder with LargeFileFinder.dmg..."
open "$DIR"

exit 0
