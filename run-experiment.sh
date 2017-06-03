pushd pcc
make
popd

go build server.go
go build client.go

sudo ./topo/run-rtt.sh
sudo ./topo/run.sh 3
