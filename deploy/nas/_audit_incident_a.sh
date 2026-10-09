#!/bin/sh
# Read-only incident audit: container state + filtered error summaries. No secret values.
D="sudo -n /usr/local/bin/docker"
R=/volume1/docker/p3f8c1a2
F='key=|secret|token|passphrase|sign=|ACCESS-|bot[0-9]+:'
date
echo "== inspect"
for c in w1 w2 w3 w4 w5 w6; do
  n=p3f8c1a2-$c
  $D inspect -f '{{.Name}} status={{.State.Status}} started={{.State.StartedAt}} restarts={{.RestartCount}} health={{if .State.Health}}{{.State.Health.Status}} fails={{.State.Health.FailingStreak}}{{end}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} created={{.Created}}' $n 2>&1
done
for c in w1 w2 w3 w4 w5 w6; do
  n=p3f8c1a2-$c
  echo "================ $c"
  $D logs --since 168h --timestamps $n > /tmp/_al_$c.txt 2>&1
  echo "lines: $(wc -l < /tmp/_al_$c.txt)  first: $(head -n1 /tmp/_al_$c.txt | cut -c1-30)"
  echo "-- level counts"
  grep -ciE 'error|exception|traceback' /tmp/_al_$c.txt
  grep -ciE 'warn' /tmp/_al_$c.txt
  echo "-- top error/warn signatures (normalized)"
  grep -iE 'error|exception|traceback|warn|fail|429|401|403|5[0-9][0-9] ' /tmp/_al_$c.txt | grep -viE "$F" \
    | cut -c32- | sed -E 's/[0-9]{2,}/N/g; s/0x[0-9a-f]+/H/g' | cut -c1-200 | sort | uniq -c | sort -rn | head -n 25
  echo "-- first/last error lines"
  grep -iE 'error|exception|traceback|fail' /tmp/_al_$c.txt | grep -viE "$F" | head -n 5 | cut -c1-300
  grep -iE 'error|exception|traceback|fail' /tmp/_al_$c.txt | grep -viE "$F" | tail -n 8 | cut -c1-300
  echo "-- tail 15"
  tail -n 15 /tmp/_al_$c.txt | grep -viE "$F" | cut -c1-300
done
rm -f /tmp/_al_*.txt
