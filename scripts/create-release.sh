#!/usr/bin/env bash
set -euo pipefail

# Create release tag for v0.2.0

if ! command -v git &>/dev/null; then
    echo "Git is required for creating release tags"
    exit 1
fi

# Initialize git repository if not exists
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - Magacin Track v0.2.0"
fi

# Create annotated tag for v0.2.0
echo "Creating release tag v0.2.0..."
git tag -a v0.2.0 -m "Release v0.2.0 - Complete Workflow

Sprint-2 delivers the complete trebovanja workflow from import to real-time monitoring.

Backend: API Gateway extensions, Scheduler algorithm, Import service integration
Frontend: Admin scheduler/override, PWA offline queue, TV privacy/milestones
Performance: P95 < 300ms, TV delta < 1s, RBAC 403 enforcement

Ready for production deployment."

echo "✅ Release tag v0.2.0 created successfully!"
echo ""
echo "To push the tag to remote repository:"
echo "  git push origin v0.2.0"
echo ""
echo "Sprint-2 documentation available in:"
echo "  - docs/test-report.md"
echo "  - docs/sprint2-summary.md"
echo "  - RELEASE-v0.2.0.md"
