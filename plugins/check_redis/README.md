# check_redis

A simple Nagios-style (works with Nagios, Icinga, Zabbix) script to checks against a Redis server.

## usage

```bash
$ ./check_redis 
Usage: check_redis -H <HOST> -p <PORT> [-P <PASSWORD>] -d <DATABASE> [-t <TIMEOUT>] -w <WARNING> -c <CRITICAL> -a <ACTION>

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -H STRING, --host=STRING
                        Host to be checked.
  -p INT, --port=INT    Port number
  -P STRING, --password=STRING
                        Redis password.
  -d STRING, --dbname=STRING
                        Redis database name (default is db0).
  -t INT, --timeout=INT
                        Number of seconds to wait before timing out.
  -w INT, --warning=INT
                        Warning value.
  -c INT, --critical=INT
                        Critical value.
  -a STRING, --action=STRING
                        Monitoring action.
```

## examples

The `INFO` command returns information and statistics about the server in a format that is simple to parse by computers and easy to read by humans. Parsing that output allows for checking connection, memory usage and hit ratio.

### check connection to Redis

Aside from returning that the connection was successful, the output also container the number of client connections, uptime in days and user memory in human readable representation.

```bash
$ ./check_redis -H 127.0.0.1 -P 1234
OK: Redis version: 3.2.12, connected_clients: 11, uptime_in_days: 590, used_memory_human: 1.77M
```

### check Redis memory

Here is the meaning of tracked fields in the memory section:

- ```used_memory```: Total number of bytes allocated by Redis using its allocator (either standard libc, - jemalloc, or an alternative allocator such as tcmalloc)
- ```used_memory_rss```: Number of bytes that Redis allocated as seen by the operating system (a.k.a - resident set size). This is the number reported by tools such as 
- ```used_memory_peak```: Peak memory consumed by Redis (in bytes)
- ```total_system_memory```: The total amount of memory that the Redis host has

If used_memory is bigger than used_memory_rss it means that physical RAM has run out and part of Redis data resides in ***SWAP*** space and the determined state code is *CRITICAL*.

```bash
$ ./check_redis -H 127.0.0.1 -P 1234 -a memory -w 80 -c 90
OK: 0.044796965843023256% used memory | used_memory=1855728 used_memory_rss=9494528 used_memory_peak=2405416 total_system_memory=4142530560
```

### check Redis hit ratio

To calculate the hit ratio, we divide the total number of hits by the sum of the total number of hits, and the number of misses:

$$ ratio = hits / hits + misses $$

For ```2464291``` hits and ```942690``` misses, then that would mean you would divide 2464291 (total number of cache hits) by ```3406981``` (sum of ```942690``` misses and ```2464291``` hits). The result would be hit ratio of ```0.723306352```. And to express this as a percentage multiply the end result by ```100```.

```bash
$ ./check_redis -H 127.0.0.1 -P 1234 -a hits -w 40 -c 30
OK: 72.33063524569113% hits | keyspace_hits=2464291 keyspace_misses=942690
```