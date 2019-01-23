# xqa-shard [![Build Status](https://travis-ci.org/jameshnsears/xqa-shard.svg?branch=master)](https://travis-ci.org/jameshnsears/xqa-shard) [![Coverage Status](https://coveralls.io/repos/github/jameshnsears/xqa-shard/badge.svg?branch=master)](https://coveralls.io/github/jameshnsears/xqa-shard?branch=master) [![sonarcloud](https://sonarcloud.io/api/project_badges/measure?project=jameshnsears_xqa-shard&metric=alert_status)](https://sonarcloud.io/dashboard?id=jameshnsears_xqa-shard) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/6c2fc5e0559941dba27ccefb79072cb4)](https://www.codacy.com/app/jameshnsears/xqa-shard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=jameshnsears/xqa-shard&amp;utm_campaign=Badge_Grade)
* BaseX engine with AMQP interface.

## 1. Trace Inserts from CLI / IDE:
* mkdir $HOME/tmp
* XQA_WRITE_FOLDER=$HOME/tmp python src/xqa/shard.py

## 2. Docker
### 2.1. Start
* docker-compose up -d xqa-message-broker
* docker-compose up -d --scale xqa-shard=2

### 2.2. Stop
* docker-compose down -v

## 3. BaseX client
```
docker ps -a
CONTAINER ID        IMAGE                                    COMMAND                  CREATED              STATUS              PORTS                                                                 NAMES
149541f33e75        xqa-shard                                "python3 xqa/shard.p…"   42 seconds ago       Up 38 seconds       0.0.0.0:32774->1984/tcp                                               xqa-shard_xqa-shard_2_f1b6d058634a
728c11d6c054        xqa-shard                                "python3 xqa/shard.p…"   42 seconds ago       Up 39 seconds       0.0.0.0:32773->1984/tcp                                               xqa-shard_xqa-shard_1_68144eb07e3f

basexclient -U admin -P admin -p 32774 
list # nothing will show when using: -storage_mainmem
open xqa
```