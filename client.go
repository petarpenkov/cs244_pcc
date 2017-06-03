package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
    "time"
)

func main() {
	server := os.Args[1]
	fmt.Println("connecting to", server)
	//filename := os.Args[2]
	//contents, err := ioutil.ReadFile(filename)
	//if err != nil {
	//	fmt.Println("Read file error:", err)
	//}
    start := time.Now()
	conn, err := net.Dial("tcp", server)
	if err != nil {
		fmt.Println(err)
		return
	}

	// read in input from stdin
	reader := bufio.NewReader(os.Stdin)
	text, _ := reader.ReadString('\n')
	// send to socket
	fmt.Fprintf(conn, text+"\n")

	conn.Close()

    duration := time.Since(start)
    fmt.Println("lasted:", duration.Nanoseconds() / 1000000)
}
