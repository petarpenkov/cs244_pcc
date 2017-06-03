pushd pcc
make
popd

go build server.go
go build client.go

sudo ./topo/run.sh
sudo ./topo/run-rtt.sh

