FROM golang

RUN go get github.com/garyburd/redigo/redis
RUN curl -sSL https://github.com/bitly/forgettable/archive/master.tar.gz \ 
| tar -v -C /go/src/ -xz

RUN go build forgettable-master/goforget
RUN go install forgettable-master/goforget

EXPOSE 8080

ENTRYPOINT goforget -redis-host=$REDIS_PORT_6379_TCP_ADDR:$REDIS_PORT_6379_TCP_PORT:1 -http=:8080 -default-rate=0.2
