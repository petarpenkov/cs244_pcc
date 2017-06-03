sudo apt-get --assume-yes install clang libudt-dev python-matplotlib bwm-ng git golang

git clone --recursive https://github.com/petarpenkov/cs244_pcc

pushd ~/cs244_pcc

pushd pcc
make
popd

go build server.go
go build client.go

mkdir plots

popd
