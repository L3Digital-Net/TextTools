#!/bin/bash
# Setup script for branch protection system

echo "Setting up branch protection system..."

# Create .agents directory if it doesn't exist
mkdir -p .agents

# Create Git hooks directory
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook to prevent direct commits to main branch

BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Allow commits during merge operations
if [ -f .git/MERGE_HEAD ]; then
    exit 0
fi

# Block commits to main branch
if [ "$BRANCH" = "main" ]; then
    echo ""
    echo "❌ ERROR: Direct commits to 'main' branch are not allowed!"
    echo ""
    echo "The main branch is protected. You should:"
    echo "  1. Switch to the testing branch: git checkout testing"
    echo "  2. Make your changes and commit them there"
    echo "  3. Merge to main only when ready: git checkout main && git merge testing"
    echo "  4. Switch back immediately: git checkout testing"
    echo ""
    echo "Current branch: $BRANCH"
    echo "Required branch: testing"
    echo ""
    exit 1
fi

exit 0
EOF

# Create post-checkout hook
cat > .git/hooks/post-checkout << 'EOF'
#!/bin/bash
# Post-checkout hook to warn when switching to main branch

PREVIOUS_HEAD=$1
NEW_HEAD=$2
BRANCH_SWITCH=$3

# Only run for branch checkouts (not file checkouts)
if [ "$BRANCH_SWITCH" = "1" ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

    if [ "$CURRENT_BRANCH" = "main" ]; then
        echo ""
        echo "⚠️  WARNING: You are now on the PROTECTED 'main' branch!"
        echo ""
        echo "The main branch is reserved for merges only. Please:"
        echo "  • Do NOT make changes directly on this branch"
        echo "  • Use 'git checkout testing' to return to development"
        echo "  • Only stay on main for merging from testing"
        echo ""
        echo "Press Enter to acknowledge this warning..."
        read -r
    fi
fi

exit 0
EOF

# Create post-merge hook
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
# Post-merge hook to remind switching back to testing after merge

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo ""
    echo "✅ Merge completed on main branch"
    echo ""
    echo "🔄 IMPORTANT: Switch back to testing branch now!"
    echo ""
    echo "Run this command to continue development:"
    echo "  git checkout testing"
    echo ""
    echo "Remember: main branch is only for receiving merges."
    echo "All development should happen on testing branch."
    echo ""
fi

exit 0
EOF

# Make hooks executable
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-checkout
chmod +x .git/hooks/post-merge

# Ensure branch protection script exists and is executable
if [ -f .agents/branch_protection.py ]; then
    chmod +x .agents/branch_protection.py
    echo "✓ Made .agents/branch_protection.py executable"
else
    echo "⚠️  Warning: .agents/branch_protection.py not found"
    echo "   Please ensure this file exists for AI agent protection"
fi

# Create testing branch if it doesn't exist
git checkout -b testing 2>/dev/null || git checkout testing
echo "✓ Ensured testing branch exists and is current"

echo ""
echo "✅ Branch protection setup completed!"
echo ""
echo "Protection components installed:"
echo "  • Pre-commit hook (prevents commits to main)"
echo "  • Post-checkout hook (warns when on main)"
echo "  • Post-merge hook (reminds to switch back)"
echo "  • Testing branch (ready for development)"
echo ""
echo "Next steps:"
echo "  1. Verify .agents/branch_protection.py exists"
echo "  2. Test protection: 'git checkout main && touch test && git add test && git commit -m test'"
echo "  3. Start development: 'git checkout testing'"
echo ""
