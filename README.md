# concurrency-control

Controller that serializes Tekton PipelineRuns on shared test machines. Each
PipelineRun is created `Pending` and names the machine(s) it needs through
labels; the controller starts it once those machines are `free`, marks them
`busy`, writes a warning to the machine's MOTD, and frees them when the run
(or the labelled task) finishes.

A web dashboard showing machine status, running pipelines and the log is served
on port 8080.

## Configuration

| Env var              | Meaning                                                              |
|----------------------|----------------------------------------------------------------------|
| `NAMESPACE`          | Namespace where PipelineRuns live                                    |
| `MACHINE_CM`         | ConfigMap holding `<machine>: free\|busy`                            |
| `PIPELINE_CM`        | ConfigMap holding the `wait_finish_runs` / `wait_finish_task` lists  |
| `LABEL_MACHINE_PR`   | PipelineRun label naming the machine held for the whole run          |
| `LAEBL_MACHINE_TASK` | PipelineRun label naming a machine held only during one task         |
| `LABEL_TASK`         | Name of the task that releases the `LAEBL_MACHINE_TASK` machine      |
| `API_TOKEN`          | Bearer token for the machine API; the write endpoints are off if unset |

## Machines

A machine has three parts:

1. **A key in `MACHINE_CM`.** The key is the machine name and the value is its
   status. The scheduler only treats `free` and `busy` as meaningful. Any other
   value, such as `maintenance`, keeps runs pending and logs a warning.
2. **A secret named after the machine**, with the keys `host`, `username` and
   `id_rsa`. The controller uses it over SSH to set and clear the MOTD. It
   reads the secret from `/opt/<machine>/` when it's mounted there. Otherwise
   it fetches the secret from the cluster at runtime, which needs `get` on
   secrets for the controller's service account.
3. **PipelineRuns that use it**, through the `LABEL_MACHINE_PR` or
   `LAEBL_MACHINE_TASK` label.

The controller picks the MOTD variant from the machine name: any name containing
`windows` is treated as a Windows host.

### Requirements on the machine

- An SSH server that accepts the public half of `id_rsa` for `username`.
- Linux: `username` can run `sudo tee /etc/motd` without a password.
- Windows: OpenSSH server with Git Bash as the default shell, because the
  controller runs `echo ... > C:\Users\<user>\ssh_motd.txt` through it.
- The tools the pipelines build with:
  - `git`
  - `make`
  - `golang`
  - `dotnet` (the Windows installer build)
  - Git Bash (Windows)

### Adding a machine manually

```sh
oc create secret generic <machine> \
  --from-literal=host=<host> \
  --from-literal=username=<user> \
  --from-file=id_rsa=<path-to-private-key>
oc set data configmap $MACHINE_CM <machine>=free
```

That's enough because the controller reads unmounted secrets from the cluster.
To keep using mounts, add the secret as a volume at `/opt/<machine>` in the
Deployment and roll it out.

Then point the pipelines at the new machine through the
`LABEL_MACHINE_PR` / `LAEBL_MACHINE_TASK` label value.

### Removing a machine manually

1. **Drain it** so no new run gets scheduled on it:
   `oc set data configmap $MACHINE_CM <machine>=maintenance`
2. **Wait for running work to finish.** The machine must not appear in
   `wait_finish_runs` or `wait_finish_task` in `PIPELINE_CM`, or on the
   dashboard. Don't skip this: when a run finishes, the controller writes
   `<machine>=free` again and the machine comes back.
3. **Remove the machine:**
   ```sh
   oc set data configmap $MACHINE_CM <machine>-
   oc delete secret <machine>   # and drop the volume mount, if there is one
   ```
4. **Update the pipelines** that reference the machine. While they still do,
   their runs stay `Pending` forever and the controller logs a warning.

### Web UI

The dashboard on port 8080 can also add and remove machines. Click **Unlock**
and enter `API_TOKEN`. The token is kept for the browser tab only. You can then
fill in the **Add machine** form, or use **Remove** next to a machine. Busy
machines can't be removed. Without `API_TOKEN` on the controller the page is
read-only.

If the controller has no Route, reach the page with
`oc port-forward <controller-pod> 8080` and open <http://localhost:8080>.

### Machine API

`GET` is open. `POST` and `DELETE` need `Authorization: Bearer $API_TOKEN`.

```sh
# list machines and their status
curl http://<controller>:8080/api/machines

# add a machine (creates the secret and sets it free)
jq -n --arg key "$(cat id_rsa)" \
  '{name: "<machine>", host: "<host>", username: "<user>", private_key: $key}' |
curl -X POST -H "Authorization: Bearer $API_TOKEN" -H 'Content-Type: application/json' \
  -d @- http://<controller>:8080/api/machines

# remove a machine (409 while it is busy)
curl -X DELETE -H "Authorization: Bearer $API_TOKEN" http://<controller>:8080/api/machines/<machine>
```

Machine names must be DNS-1123 labels: lowercase letters, digits and `-`.
`DELETE` only removes a secret that the API created. Mounted secrets are left
alone because the Deployment owns them. The service account needs `create`,
`get`, `patch` and `delete` on secrets for these endpoints.

## Tests

The tests run against an in-memory fake of `oc` and never touch a real
cluster or machine.

```sh
pip install -r requirements-dev.txt
python -m pytest                     # API and browser tests, in the installed Google Chrome
python -m pytest tests/test_api.py   # API tests only, no browser needed
```

Without Google Chrome, run `python -m playwright install chromium` once and pass
`--browser chromium`. `--browser` also takes `firefox` and `webkit` and can be
repeated.

Tests marked `xfail` describe known bugs. Once a fix makes one pass, pytest
reports it as a failure so that the marker gets removed.
