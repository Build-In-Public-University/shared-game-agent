# Marvin Witness Flow

The witness rail watches Marvin mentions for an explicit commitment, schedules the seven-day follow-up, and only then replies that the commitment was recorded.

## Ordering invariant

```text
mention detected
  -> commitment passes explicit-language detector
  -> follow-up job appended with durable job_id
  -> commitment persisted with schedule_id
  -> Marvin replies "Recorded..."
```

If scheduling fails, no acknowledgement is posted. If X reply fails after scheduling, the commitment remains recoverable with `status=scheduled` and the job ID.

## VPS timer

Install the service and timer under `/etc/systemd/system/`, create `/etc/shared-game-agent.env` with non-secret runtime settings, then:

```bash
systemctl daemon-reload
systemctl enable --now shared-game-witness.timer
systemctl start shared-game-witness.service
systemctl status shared-game-witness.timer
journalctl -u shared-game-witness.service -n 50 --no-pager
```

The worker requires the VPS `marvin-x` xurl app to be authenticated. It uses explicit `xurl --app marvin-x` calls and does not read `~/.xurl` directly.

The queue file is an auditable handoff for the separate follow-up executor. A later worker should consume `witness_follow_up` jobs and publish the outcome-check prompt in the original conversation, then mark the job complete. The first rail only proves detection, scheduling, and acknowledgement.

## Seed tweet

The initial live-play witness declaration is:

`https://x.com/leo_guinan/status/2079261354448302166`

The public text names leading indicators, the scoreboard, and `@marvin_panics` as witness. Its follow-up is seven days after the tweet timestamp.
