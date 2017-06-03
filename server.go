package main

import (
	"fmt"
	"io"
	"net"
	"os"
	"time"
    "strconv"
)

const (
	CONN_HOST = "0.0.0.0"
	CONN_PORT = "9000"
	CONN_TYPE = "tcp"
)

func main() {
	// Listen for incoming connections.
	l, err := net.Listen(CONN_TYPE, CONN_HOST+":"+CONN_PORT)
	if err != nil {
		fmt.Println("Error listening:", err.Error())
		os.Exit(1)
	}
	// Close the listener when the application closes.
	defer l.Close()
	fmt.Println("Listening on " + CONN_HOST + ":" + CONN_PORT)
	for {
		// Listen for an incoming connection.
		conn, err := l.Accept()
		if err != nil {
			fmt.Println("Error accepting: ", err.Error())
			os.Exit(1)
		}
		// Handle connections in a new goroutine.
		go handleRequest(conn)
	}
}

func handleRequest(conn net.Conn) {
	buf := make([]byte, 2048)
	file := make([]byte, 0)

	start := time.Now()

	n, err := conn.Read(buf)
    total := n
	for err == nil {
		file = append(file, buf[:n]...)
		n, err = conn.Read(buf)
        total += n
	}
	if err != io.EOF {
		fmt.Println("read error:", err)
	}
    t := strconv.Itoa(total)
    s := "total_bytes:"+t+"\n"
    fmt.Println(s)
    fmt.Fprintf(conn, s)
	conn.Close()

	duration := time.Since(start)
	fmt.Println("got", len(file), "bytes, lasted", duration.Nanoseconds() / 1000000)
}
