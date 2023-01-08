# check_vault

Nagios-style (works with Nagios, Icinga, Zabbix) script to checks status of a Vault server. The ```/sys/health``` endpoint returns the health status of Vault. 
This matches the semantics of a Consul HTTP health check and provides a simple way to monitor the health of a Vault instance. The script will send a ```HEAD``` request using ```curl``` and print out just the HTTP status code.

The default status codes are:
- ```200``` if initialized, unsealed, and active
- ```429``` if unsealed and standby
- ```472``` if disaster recovery mode replication secondary and active
- ```473``` if performance standby
- ```501``` if not initialized
- ```503``` if sealed

## usage

```bash
$ ./check_vault -h

Check if Vault API is reachable

Usage:
./check_vault [-s vault_server] [-p vault_port] [-h]

Either specify -s flag or set VAULT_ADDR environment variable.
```

## examples

Using the ```VAULT_ADDR``` environment variable (for a *Leader* Vault node):
```bash
$ env|grep VAULT_ADDR
VAULT_ADDR=http://127.0.0.1:8200
```
```bash
$ ./check_vault 
OK: Vault is initialized, unsealed, and active.
```

If ```VAULT_ADDR``` environment variable is not set, by specifying ```-s``` and ```-p``` parameters (for a *Follower* Vault node):
```bash
 ./check_vault -s 127.0.0.1 -p 8200
OK: Vault is unsealed and standby.
```

## Icinga2 configuration

### command-plugins.conf
```bash
object CheckCommand "check_vault" {
  import "plugin-check-command"

  command = [ PluginDir + "/check_vault" ]

  arguments = {
    "-s"     = "$vault_host$"
    "-p"     = "$vault_port$"
    "-t"     = {
               set_if = "$vault_tls$"
               description = "Use https"
    }
    "-k"     = {
               set_if = "$vault_insecure$"
               description = "Use curl with -k or --insecure"
    }

  }

  vars.vault_host = "$host.address$"
  vars.vault_port = 8200
}
```
### templates.conf
```bash
template Host "vault-host" {
  import "generic-host"

  vars.tcp_address = "$address$"
  if (!"$host.vars.vault_port$") { vars.tcp_port = 8200 } else { vars.tcp_port = "$host.vars.vault_port$" }
  vars.vault_tls = false
  vars.vault_insecure = false

  check_command = "tcp"
}
```

### services.conf

```bash
apply Service "tcp-vault-connection" {
  import "generic-service"
  check_command = "check_vault"
  display_name = "Vault Status"
  enable_perfdata = false

  vars += host.vars

  if (!vars.vault_port) { vars.vault_port = 8200 }
  if (!vars.vault_tls) { vars.vault_tls = false }
  if (!vars.vault_insecure) { vars.vault_insecure = false }

  assign where "vault" in host.vars.roles
}
```

### hosts.conf
```bash
object Host "my.vault.host" {
  import "vault-host"
  address = "127.0.0.1"

  vars.vault_tls = true
  vars.vault_insecure = true
  vars.roles = [ "vault" ]
}
```
