import json
import sys
import semver
import os

# Get bump type from arguments
bump_type = sys.argv[1] if len(sys.argv) > 1 else "patch"

# Read the manifest.json file
with open("custom_components/battery_energy_tracker/manifest.json", "r") as f:
    manifest = json.load(f)

# Get current version
current_version = manifest["version"]

# Bump version according to type
if bump_type == "patch":
    new_version = str(semver.VersionInfo.parse(current_version).bump_patch())
elif bump_type == "minor":
    new_version = str(semver.VersionInfo.parse(current_version).bump_minor())
elif bump_type == "major":
    new_version = str(semver.VersionInfo.parse(current_version).bump_major())
else:
    print(f"Unknown bump type: {bump_type}")
    sys.exit(1)

# Update the version in manifest
manifest["version"] = new_version

# Write back to manifest.json
with open("custom_components/battery_energy_tracker/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

# Output the new version for use in the GitHub Action using environment file
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"new_version={new_version}\n")

print(f"Bumped version from {current_version} to {new_version}")