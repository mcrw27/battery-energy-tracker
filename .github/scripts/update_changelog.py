import sys
import os
from datetime import datetime

def update_changelog(version, version_type):
    # Get the current date in YYYY-MM-DD format
    date = datetime.now().strftime("%Y-%m-%d")
    
    # Read the existing changelog
    with open("CHANGELOG.md", "r") as f:
        content = f.read()
    
    # Create the new version entry
    if version_type == "major":
        changes = "### Added\n- Major version release\n\n### Changed\n- Breaking changes\n"
    elif version_type == "minor":
        changes = "### Added\n- New feature\n\n### Changed\n- Non-breaking improvements\n"
    elif version_type == "patch":
        changes = "### Fixed\n- Bug fixes\n"
    
    # Create the new entry
    new_entry = f"## [{version}] - {date}\n{changes}"
    
    # Find the position for the new entry (after Unreleased section)
    unreleased_pos = content.find("## [Unreleased]")
    next_version_pos = content.find("## [", unreleased_pos + 1)
    
    # Insert the new version entry
    updated_content = content[:next_version_pos] + new_entry + "\n\n" + content[next_version_pos:]
    
    # Write back to the file
    with open("CHANGELOG.md", "w") as f:
        f.write(updated_content)
    
    print(f"Changelog updated for version {version}")

if __name__ == "__main__":
    version = sys.argv[1]
    version_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
    update_changelog(version, version_type)