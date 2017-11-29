# xqa-shard [![travis](https://travis-ci.org/jameshnsears/xqa-shard.svg?branch=master)](https://travis-ci.org/jameshnsears/xqa-shard.svg?branch=master) [![Coverage Status](https://coveralls.io/repos/github/jameshnsears/xqa-shard/badge.svg?branch=master)](https://coveralls.io/github/jameshnsears/xqa-shard?branch=master)
an "embedded" in-memory BaseX instance with a AMQP interface.

## 1. High Level Design
![High Level Design](uml/balancer-sequence-diagram.jpg)

## 2. Docker
### 2.1. Build locally
* docker-compose -p "dev" build

### 2.2. Bring up
* docker-compose -p "dev" up -d

### 2.3. Teardown
* docker-compose -p "dev" down --rmi all -v
