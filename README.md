# xqa-shard [![Build Status](https://travis-ci.org/jameshnsears/xqa-shard.svg?branch=master)](https://travis-ci.org/jameshnsears/xqa-shard) [![Coverage Status](https://coveralls.io/repos/github/jameshnsears/xqa-shard/badge.svg?branch=master)](https://coveralls.io/github/jameshnsears/xqa-shard?branch=master)
* an embedded in-memory BaseX instance with a AMQP interface.

* See .travis.yml for py.test example, including flake8 and coverage arguments.

## 1. High Level Design
![High Level Design](uml/balancer-sequence-diagram.jpg)

## 2. Docker
### 2.1. Build locally
* docker-compose -p "dev" build --rm

### 2.2. Bring up
* docker-compose -p "dev" up -d  # single instance

or

* docker-compose -p "dev" up -d --scale xqa-shard=2  # two instances

### 2.3 Stop
* docker-compose stop

### 2.4. Teardown
* docker-compose -p "dev" down --rmi all -v

## 3. Debug inserts into /tmp
$ XQA_WRITE_FILE=1 python src/xqa/shard.py
