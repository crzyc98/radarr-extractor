PUID-PGID Permission Reference (PRD v2)

Audience: Home-lab and NAS users running Docker containers under TrueNAS SCALE, Portainer, or Compose.
Goal: Guarantee that containers write to host volumes with the correct Unix ownership—no root:root surprises—while keeping security tight and maintenance painless.

⸻

1  Why This Matters
	•	NAS File Integrity – Prevents orphaned root files that clutter snapshots and break SMB/NFS ACLs.
	•	Cross-Container Collaboration – Media apps (Radarr, Sonarr, DelugeVPN) share a group ID so they can pass files without chmod headaches.
	•	Security Baseline – Running as non-root stops privilege-escalation exploits dead in their tracks.

⸻

2  When To Set PUID & PGID

Scenario	Required?	Notes
LinuxServer.io images	Always	They enforce PUID/PGID at startup.
Official images (e.g. postgres)	Optional	Only if you mount host volumes that need specific ownership.
Container orchestrated by Portainer Stack	Recommended	Portainer surfaces env vars neatly in the UI.


⸻

3  Quick-Start Cheat-Sheet

# 1 Find your numerical UID & GID
id $USER        # e.g. uid=1000( nick) gid=1000( nick)

# 2 Stick them in a .env file (best practice)
PUID=1000
PGID=1000

# 3 Reference in docker-compose.yml
services:
  radarr:
    image: lscr.io/linuxserver/radarr:latest
    environment:
      - PUID=${PUID}
      - PGID=${PGID}
    volumes:
      - /mnt/Pool1/media:/media


⸻

4  How It Works (︱Mermaid Sequence)

flowchart LR
    subgraph Host
        A[/User Space/]
        B[/ZFS Dataset/]
    end
    subgraph Container
        C(Process uid=PUID gid=PGID)
    end
    C -- "writes via volume mount" --> B
    A -- "ls -n shows PUID/PGID" --> B


⸻

5  Deep-Dive

5.1 Finding the Right IDs

# View mapping for a given directory
ls -n /mnt/Pool1/media | head
# Verify current shell IDs
id $(whoami)

TrueNAS SCALE note: Dataset permission UI shows numeric IDs—handy cross-check.

5.2 Compose Patterns
	•	Global .env at repo root keeps secrets out of compose files.
	•	Per-service overrides in a stack.env when group separation needed (PGID=101 for all media apps).

5.3 Edge Cases & Fixes

Symptom	Likely Cause	Remedy
Files owned by root:root appear in volume	Container started without PUID/PGID	Redeploy with correct env vars, then chown -R 1000:1000 to fix existing files.
Permissions look right but app still can’t write	Dataset ACL overrides Unix perms	In TrueNAS, set ACL mode to PASSTHROUGH or add the UID/GID explicitly.
UID clash after migrating to new NAS	New system assigns different UID numbers	Create matching user/group or tweak .env values to new IDs before container start.

5.4 Security Tips
	•	Never use PUID=0 unless debugging.
	•	Create purpose-built users (e.g., mediausr) to sandbox internet-facing apps.
	•	Pair with read-only mounts where writes aren’t needed.

5.5 Integration with Cloudbound Strategy

OneDrive/
└── DockerDocs/
    └── Permissions/
        ├── PUID-PGID-PRD_v2.md  ← this file
        └── ACL-Strategy.md

Add a cross-link in your master README.md so newcomers see this early.

⸻

6  Troubleshooting Flow
	1.	ls -n → Are numeric IDs correct?
	2.	docker exec whoami → Is process running as expected UID?
	3.	TrueNAS ACL → Any deny entries?
	4.	Audit logs → Look for EPERM or EACCES errors.

⸻

7  Further Reading
	•	LinuxServer.io PUID/PGID docs
	•	TrueNAS SCALE ACL Best Practices
	•	Docker documentation: User Namespaces & Rootless Engine

⸻

Version: 2025-07-07
Maintainer: Nick Amaral
Change Log: Add diagram, edge-cases table, Cloudbound path reference.