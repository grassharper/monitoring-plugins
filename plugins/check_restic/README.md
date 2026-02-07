# check_restic

A simple Nagios-style (works with Nagios, Icinga, Zabbix) script to check when was the last Restic backup made.
Restic passwords are kept in Hashicorp Vault. The path for accessing secrets in Vault is structured as follows:

`${secret engine name} / ${repository} / ${client} / ${project} / ${remote Restic server SSH host alias} / ${hostname of target backup server}.`

## usage

```bash
$ ./check_restic 
Usage: check_restic -w limit -c limit -r <REPOSITORY> -H <HOSTNAME> -s <VAULT-SERVER> -t <TOKEN> -e <ENGINE> -C <CLIENT> -R <REMOTE> -n <NAME>

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -w INT, --warning=INT
                        Number of days to trigger WARNING.
  -c INT, --critical=INT
                        Number of days to trigger CRITICAL.
  -r STRING, --repository=STRING
                        Stored locally, or on some remote server.
  -H STRING, --hostname=STRING
                        In Vault, the path contains the hostname. Multiple
                        key/value pairs can be used, which determines the
                        backup name and passphrase.
  -s STRING, --vault-server=STRING
                        RESTIC_PASSWORD is stored in HashiCorp Vault. To read
                        the passphrase, please specify the Vault server.
  -t STRING, --token=STRING
                        Specify Vault token.
  -e STRING, --engine=STRING
                        Specify Vault engine.
  -C STRING, --client=STRING
                        Specify Client.
  -P STRING, --project=STRING
                        Specify Project.
  -R STRING, --remote=STRING
                        Specify Remote Server Alias.
  -n STRING, --name=STRING
                        Specify name of the backup.
```

## examples

To monitor when the last backup was made with Restic, we can use the command `restic snapshots --json` to retrieve the information about the latest snapshot, including its timestamp.

```bash
$ restic -r /backup/personal/core/vault1.my.tld/vault snapshots --latest 1 --json|jq
enter password for repository: 
[
  {
    "time": "2026-02-07T09:51:35.579787625Z",
    "parent": "a891ecc0e502db19839a758f443a456917c07234041e42dbd276541e525f3e9c",
    "tree": "b0a8d8853a8d1f73cffd0776691b51552f9e37f42f21fa4b556245bd9ff8144d",
    "paths": [
      "/backup/vault"
    ],
    "hostname": "vault1.my.tld",
    "username": "backup",
    "program_version": "restic 0.18.1",
    "summary": {
      "backup_start": "2026-02-07T09:51:35.579787625Z",
      "backup_end": "2026-02-07T09:51:36.337113875Z",
      "files_new": 0,
      "files_changed": 0,
      "files_unmodified": 1,
      "dirs_new": 0,
      "dirs_changed": 0,
      "dirs_unmodified": 3,
      "data_blobs": 0,
      "tree_blobs": 0,
      "data_added": 0,
      "data_added_packed": 0,
      "total_files_processed": 1,
      "total_bytes_processed": 1652107
    },
    "id": "1476228690bda81d0c45d86e3f24b2ff1c3c8e0eecda4188149f0930da94397f",
    "short_id": "14762286"
  }
]
```

We can even process the JSON output to find the timestamp of the most recent snapshot, using `jq`:

```bash
$ restic -r /backup/personal/core/vault1.my.tld/vault snapshots --latest 1 --json||jq -r '.[-1].time'
enter password for repository: 
2026-02-07T09:51:35.579787625Z
```

The `check_restic` script accomplishes this by encapsulating all the logic needed to determine when the last backup was performed and whether it exceeds the specified warning or critical thresholds.

### check Restic repository status

Aside from returning that the last backup is OK (recent enough), the output also contains the timestamp of the last backup made.

```bash
$ ./check_restic -w '1' -c '2' -r '/backup/personal/core/vault1.my.tld/vault' -H 'vault1.my.tld' -s 'https://vault.my.tld:8200' -t '***.******************************' -e 'restic' -C 'personal' -P 'core' -R 'restic_backup' -n 'vault'
OK: last backup made on 2026-02-07T09:51:36.363770426Z
```

## Icinga2 configuration

In this example, I'll focus on an `apply Service` for monitoring *Restic* on a remote host that has NRPE daemon. The NRPE configuration will enable the Icinga2 server to communicate with the remote host to execute custom commands, ensuring both monitoring and alerting.

> The ***NRPE*** protocol is considered insecure and has multiple flaws in its design. Upstream is not willing to fix these issues.
>
> If you are not employing a firewall to limit access to the NRPE daemon so that only Icinga2 servers can connect to it, in order to stay safe, please use the *native* ***Icinga 2 client*** or ***SSH*** instead.

### services.conf

```bash
apply Service "nrpe-restic-" for (identifier => backup in host.vars.restic_checks) {
  import "generic-service"
  check_command = "nrpe"
  enable_perfdata = false
  display_name = "Restic-" + identifier

  if (host.vars.restic_check_period != "") {
    check_period = host.vars.restic_check_period
  } else {
    check_period = "noon"
  }

  max_check_attempts = 5
  check_interval = 30m
  retry_interval = 10m

  if (!backup.restic_days_wgreater) { backup.restic_days_wgreater = "1" }
  if (!backup.restic_days_cgreater) { backup.restic_days_cgreater = "2" }
  if (!backup.vault_addr) { backup.vault_addr = "https://127.0.0.1:8200" }
  if (!backup.restic_engine) { backup.restic_engine = "restic" }
  if (!backup.restic_client) { backup.restic_client = "personal" }
  if (!backup.restic_project) { backup.restic_client = "core" }
  if (!backup.restic_remote) { backup.restic_remote = "restic_backup" }

  vars.restic_days_wgreater = backup.restic_days_wgreater
  vars.restic_days_cgreater = backup.restic_days_cgreater
  vars.restic_repo = backup.restic_repo
  vars.restic_host = identifier.split("/").get(0)
  vars.vault_addr = backup.vault_addr
  vars.vault_token = backup.vault_token
  vars.restic_engine = backup.restic_engine
  vars.restic_client = backup.restic_client
  vars.restic_project = backup.restic_project
  vars.restic_remote = backup.restic_remote
  vars.restic_backup_name = identifier.split("/").get(1)

  vars.nrpe_command = "check_restic"
  vars.nrpe_arguments = [ "$restic_days_wgreater$", "$restic_days_cgreater$", "$restic_repo$", "$restic_host$", "$vault_addr$", "$vault_token$", "$restic_engine$", "$restic_client$", "$restic_project$", "$restic_remote$", "$restic_backup_name$" ]

  assign where ( host.vars.is_nrpe && host.vars.restic_checks )
}
```

### hosts.conf

```bash
object Host "my.restic.host" {
  check_command = "hostalive"
  enable_perfdata = false
  address = "127.0.0.1"


  vars.restic_checks["vault.my.tld/vault"] = { restic_days_wgreater = "1", restic_days_cgreater = "2", restic_client = "personal", restic_project = "core", restic_repo = "/backup/personal/core/vault1.my.tld/vault", vault_token = "***.******************************" }
  vars.restic_checks["vault.my.tld/vaultconfigfiles"] = { restic_days_wgreater = "1", restic_days_cgreater = "2", restic_client = "personal", restic_project = "core", restic_repo = "/backup/personal/core/vault1.my.tld/vaultconfigfiles", vault_token = "***.******************************" }
  
  vars.notification["mail"] = {
    global = {
      groups = [
        "monitor"
      ]
    }
  }
}
```

## Backup Restic server 

NRPE on the remote Restic backup server:
```bash
# cat /etc/nagios/nrpe.d/restic.cfg 
command[check_restic]=PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin /usr/bin/sudo /usr/lib/nagios/plugins/check_restic -w "$ARG1$" -c "$ARG2$" -r "$ARG3$" -H "$ARG4$" -s "$ARG5$" -t "$ARG6$" -e "$ARG7$" -C "$ARG8$" -P "$ARG9$" -R "$ARG10$" -n "$ARG11$"
```

> The server we want to backup and the remote Restic server may be the same; in that case, this and the subsequent configuration will be located on the same server.

## Target server to be backed up

Above, you encountered a ***remote*** by default having the value `restic_backup`, which is essentially an SSH host alias. In my configuration, this primarily serves as a differentiator in the event that I have multiple Restic backup servers. So, it serves as a host alias in `.ssh/config` on the target server, instructing `restic` on which *host*, *port*, and *SSH key* to use when connecting to the actual backup server that stores the remote Restic files. Example:

```bash
$ cat .ssh/config 
Host restic_backup
  HostName bck.my.tld
  Port 22
  StrictHostKeyChecking no
  IdentityFile ~/.ssh/id_ed25519_restic
  ServerAliveInterval 10
  ServerAliveCountMax 30
  LogLevel QUIET
```
