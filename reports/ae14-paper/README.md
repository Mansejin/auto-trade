# AE14 paper logs

Append-only JSONL (gitignored):

- `upbit-premium.jsonl` — premium components each cron tick
- `paper-events.jsonl` — only when H1 / H_rich fires

```bash
python3 scripts/ae12_forward_collect.py
python3 scripts/ae14_paper_log.py
```

Spec: `reports/improve/20260729-ae14-paper-log-spec.md`
