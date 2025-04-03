# Test

## 1. Deploy consul.

```shell
docker run -d \
  --name consul \
  -p 8500:8500 \
   consul:1.15 agent -server -bootstrap-expect=1 -client=0.0.0.0

```

## 2. Run tests.

```shell
make init
make coverage
make test

```