# S25 GitHub -> Alien auto-pull

Version-controlled systemd user units for the existing safe auto-pull script.

## Safety
The script uses `git pull --ff-only origin main`. It does not reset, clean, stash, or force-overwrite the Alien working tree.

## Installation on Alien
Installation is intentionally not automatic. First inspect the local dirty tree and /tmp/auto_pull.log.

When approved locally, copy the two unit files to `~/.config/systemd/user/`, run `systemctl --user daemon-reload`, enable/start `s25-auto-pull.timer`, then verify with `systemctl --user status s25-auto-pull.timer` and `journalctl --user -u s25-auto-pull.service`.

This makes the GitHub -> Alien pull schedule observable and recoverable after reboot.
