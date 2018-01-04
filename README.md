# xqa-shard [![Build Status](https://travis-ci.org/jameshnsears/xqa-shard.svg?branch=master)](https://travis-ci.org/jameshnsears/xqa-shard) [![Coverage Status](https://coveralls.io/repos/github/jameshnsears/xqa-shard/badge.svg?branch=master)](https://coveralls.io/github/jameshnsears/xqa-shard?branch=master)
* an embedded in-memory BaseX instance with a AMQP interface.
* See .travis.yml for usage, including flake8 and coverage arguments.

## 1. Docker
### 1.1. Build locally
* docker-compose -p "dev" build --force-rm

### 1.2. Bring up
* docker-compose -p "dev" up -d  # single instance

or

* docker-compose -p "dev" up -d --scale xqa-shard=2  # two instances

### 1.3. Teardown
* docker-compose -p "dev" down -v

## 2. (optional) Trace inserts into /tmp (if running shard from cmd line|ide, not container)
* mkdir $HOME/tmp
* XQA_WRITE_FOLDER=$HOME/tmp python src/xqa/shard.py > $HOME/tmp/xqa-shard-1.log
