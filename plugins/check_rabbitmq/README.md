# RabbitMQ checks

Nagios-style (works with Nagios, Icinga, Zabbix) script to check status of a RabbitMQ server. 
RabbitMQ is an open source multi-protocol messaging broker. The *checks* are built using the output of ```rabbitmqctl``` command, which is the main command line tool for managing a RabbitMQ server node.

# check_rabbitmq_cluster

When forming and provisioning a RabbitMQ cluster, because several features (e.g. *quorum queues*, *client tracking* in MQTT) require a consensus between cluster members, odd numbers of cluster nodes are highly recommended: 1, 3, 5, 7 and so on. ```check_rabbitmq_cluster``` counts the total number of available members to determine the status of the RabbitMQ cluster.

## usage
```bash
$ ./check_rabbitmq_cluster -h
Usage: check_rabbitmq_cluster -w limit -c limit

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -w INT, --warning=INT
  -c INT, --critical=INT
```

## examples

To check that all cluster members are available (on a 3 node cluster), and 
```bash
./check_rabbitmq_cluster -w 2 -c 1
RabbitMQ Cluster OK - 3 active nodes
```

# check_rabbitmq_server

Get resource usage of a node by parsing the output of ```rabbitmqctl status```. The command displays broker status information such as the running applications on the current Erlang node, RabbitMQ and Erlang versions, OS name, memory and file descriptor statistics.

## usage

```bash
$ ./check_rabbitmq_server  -h
Usage: check_rabbitmq_server -t type -w limit -c limit

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -t STRING, --type=STRING
                        type can be one of the following: memory, disk,
                        sockets, processes or file_descriptors
  -w INT, --warning=INT
                        warning percentage value
  -c INT, --critical=INT
                        critical percentage value
```

## examples

The RabbitMQ server detects the total amount of RAM installed in the computer on startup and when ```rabbitmqctl set_vm_memory_high_watermark fraction``` is executed. When the RabbitMQ server uses above 40% (the default memory threshold) of the available RAM, it raises a memory alarm and blocks all connections that are publishing messages. Once the memory alarm has cleared (e.g. due to the server paging messages to disk or delivering them to clients that consume and acknowledge the deliveries) normal service resumes.

```bash
./check_rabbitmq_server -t memory -w 75 -c 85
RabbitMQ Memory OK - 12.0153279706% used memory | vm_memory_high_watermark_limit=1657002393 total_erlang=199094272 total_rss=199094272 total_allocated=199094272 allocated_unused=54026560 atom=1458513 binary=25832680 code=27060983 connection_channels=394168 connection_other=4055616 connection_readers=1945400 connection_writers=108948 metrics=1412600 mgmt_db=6747340 mnesia=4692616 msg_index=738840 other_ets=3916720 other_proc=24638772 other_system=14018464 plugins=6831008 queue_procs=13379988 queue_slave_procs=0 quorum_ets=23704 quorum_queue_dlx_procs=2824 quorum_queue_procs=0 reserved_unallocated=7802880 stream_queue_coordinator_procs=0 stream_queue_procs=2824 stream_queue_replica_reader_procs=2824
```

When free disk space drops below a configured limit (50 MB by default), an alarm will be triggered and all producers will be blocked. The goal is to avoid filling up the entire disk which will lead all write operations on the node to fail and can lead to RabbitMQ termination.
```bash
./check_rabbitmq_server -t disk -w 75 -c 85
RabbitMQ Memory OK - 2.32483440335% of free disk | diskfree=2150690816 diskfreelimit=50000000
```

Most operating systems limit the number of file handles (including sockets), that can be opened at the same time. When an OS process (such as RabbitMQ's Erlang VM) reaches the limit, it won't be able to open any new files or accept any more TCP connections.
```bash
./check_rabbitmq_server -t sockets -w 75 -c 85
RabbitMQ Sockets OK - 0.074769605286% used sockets | sockets_used=43 sockets_limit=57510
```
```bash
./check_rabbitmq_server -t file_descriptors -w 75 -c 85
RabbitMQ File Descriptors OK - 0.242555122608% used file descriptors | fd_total_used=155 fd_total_limit=63903
```

Check used processes against the maximum number of Erlang processes the VM is configured to allow.
```bash
./check_rabbitmq_server -t processes -w 75 -c 85
RabbitMQ Processes OK - 0.157070159912% used processes | processes_used=1647 processes_limit=1048576
```

# check_rabbitmq_queue

The plugin will check for the number of messages ready to be delivered to clients and the number of messages delivered to clients but not yet acknowledged.

A message is ***Ready*** when it is waiting to be processed. When a consumer connects to the queue it gets a batch of messages to process and while this consumer is working on the messages, they get the status of *unacked*.

**Unacked*** means that the consumer has promised to process them but has not acknowledged that they are processed already. 
If the consumer crashes, the queue knows which messages are to be delivered again when the consumer comes back online. If we have multiple consumers the messages are distributed between them.

Displayed queues are filtered by the following options:
- ```messages_ready```: Number of messages ready to be delivered to clients.
- ```messages_unacknowledged```: Number of messages delivered to clients but not yet acknowledged.
- ```messages```: Sum of ready and unacknowledged messages (queue depth).
- ```messages_ready_ram```: Number of messages from messages_ready which are resident in ram.
- ```messages_unacknowledged_ram```: Number of messages from messages_unacknowledged which are resident in ram.
- ```messages_ram```: Total number of messages which are resident in ram.
- ```messages_persistent```: Total number of persistent messages in the queue (will always be 0 for transient queues).
- ```message_bytes```: Sum of the size of all message bodies in the queue. This does not include the message properties (including headers) or any overhead.
- ```message_bytes_ready```: Like message_bytes but counting only those messages ready to be delivered to clients.
- ```message_bytes_unacknowledged```: Like message_bytes but counting only those messages delivered to clients but not yet acknowledged.
- ```message_bytes_ram```: Like message_bytes but counting only those messages which are currently held in RAM.
- ```message_bytes_persistent```: Like message_bytes but counting only those messages which are persistent.
- ```disk_reads```: Total number of times messages have been read from disk by this queue since it started.
- ```disk_writes```: Total number of times messages have been written to disk by this queue since it started.
- ```consumers```: Number of consumers.
- ```memory```: Bytes of memory allocated by the runtime for the queue, including stack, heap and internal structures.

## usage

```bash
$ ./check_rabbitmq_queue -h
Usage: check_rabbitmq_queue [-r] [-u] -p vhost -q queue -w limit -c limit

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -r, --ready           get number of ready messages (I'm hunting wabbits)
  -u, --unacked         get number of unacknowledged messages
  -p STRING, --vhost=STRING
  -q STRING, --queue=STRING
  -w INT, --warning=INT
  -c INT, --critical=INT
```

## examples

Get number of ready messages for a particular queue:
```bash
./check_rabbitmq_queue -r -p /test -q My.Queue.Default -w 20 -c 30
RabbitMQ My.Queue.Default queue CRITICAL - 30 ready messages | name=My.Queue.Default messages_ready=30 messages_unacknowledged=0 messages=30 messages_ready_ram=28 messages_unacknowledged_ram=0 messages_ram=28 messages_persistent=30 message_bytes=179738628 message_bytes_ready=179738628 message_bytes_unacknowledged=0 message_bytes_ram=38616 message_bytes_persistent=179738628 disk_reads=28 disk_writes=0 consumers=0 memory=143356
```
Get number of unacknowledged messages for a particular queue:
```bash
./check_rabbitmq_queue -u -p /test -q My.Queue.Default -w 20 -c 30
RabbitMQ My.Queue.Default queue OK - 0 unacknowledged messages | name=My.Queue.Default messages_ready=30 messages_unacknowledged=0 messages=30 messages_ready_ram=28 messages_unacknowledged_ram=0 messages_ram=28 messages_persistent=30 message_bytes=179738628 message_bytes_ready=179738628 message_bytes_unacknowledged=0 message_bytes_ram=38616 message_bytes_persistent=179738628 disk_reads=28 disk_writes=0 consumers=0 memory=143356
```