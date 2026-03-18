#!/bin/bash
# ──────────────────────────────────────────────────────────────
# publish_release.sh — Build, tag, and publish a GitHub release
# ──────────────────────────────────────────────────────────────
# Usage:
#   ./publish_release.sh                    # uses VERSION file
#   ./publish_release.sh "Release notes"    # custom release notes
#
# Prerequisites:
#   - gh CLI installed and authenticated (gh auth login)
#   - Git remote configured pointing to GitHub
#   - VERSION file at repo root
# ──────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Read version ──
VERSION_FILE="VERSION"
if [ ! -f "$VERSION_FILE" ]; then
    echo "ERROR: VERSION file not found."
    exit 1
fi
VERSION=$(tr -d '[:space:]' < "$VERSION_FILE")
TAG="v${VERSION}"
DMG_NAME="MyFileTool-${VERSION}.dmg"
RELEASE_NOTES="${1:-Release ${VERSION}}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Publishing my.File Tool ${VERSION}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Pre-flight checks ──
echo ""
echo "▶ Pre-flight checks..."

if ! command -v gh &>/dev/null; then
    echo "  ERROR: gh CLI not found. Install: brew install gh"
    exit 1
fi

if ! gh auth status &>/dev/null; then
    echo "  ERROR: gh not authenticated. Run: gh auth login"
    exit 1
fi

if ! git remote -v | grep -q "github.com"; then
    echo "  ERROR: No GitHub remote configured."
    echo "  Run: git remote add origin https://github.com/madore9/myh_file_finder.git"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "  WARNING: You have uncommitted changes."
    read -p "  Continue anyway? (y/N) " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 1
    fi
fi

# Check if tag already exists
if git rev-parse "$TAG" &>/dev/null; then
    echo "  ERROR: Tag ${TAG} already exists. Bump the VERSION file first."
    exit 1
fi

echo "  ✓ All checks passed"

# ── Build DMG ──
echo ""
echo "▶ Building DMG..."
./build_dmg.sh

if [ ! -f "$DMG_NAME" ]; then
    echo "  ERROR: Expected ${DMG_NAME} not found after build."
    exit 1
fi
echo "  ✓ ${DMG_NAME} built"

# ── Git tag ──
echo ""
echo "▶ Creating git tag ${TAG}..."
git tag -a "$TAG" -m "Release ${VERSION}"
git push origin "$TAG"
echo "  ✓ Tag ${TAG} pushed"

# ── GitHub Release ──
echo ""
echo "▶ Creating GitHub release..."
DMG_LATEST="MyFileTool-latest.dmg"
gh release create "$TAG" \
    "$DMG_NAME" \
    "$DMG_LATEST" \
    --title "my.File Tool ${VERSION}" \
    --notes "$RELEASE_NOTES"

RELEASE_URL=$(gh release view "$TAG" --json url -q '.url')
echo "  ✓ Release published: ${RELEASE_URL}"

# ── Done ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ v${VERSION} published!"
echo "  ${RELEASE_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
