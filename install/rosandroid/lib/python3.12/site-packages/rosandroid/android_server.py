import rclpy
from rclpy.node import Node

from std_msgs.msg import String

import socket
from threading import Thread
 
class ServerPublisher(Node):
    Clients = []
    
    def __init__(self, HOST, PORT):
        # Publish Node
        super().__init__('server_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        
    
        # Create a TCP socket over IPv4. Accept at max 5 connections.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen(5)
        print('Server waiting for connection....')

        # Activate Listen Function
        self.listen()

    # Listen for connections on the main thread. When a connection
    # is received, create a new thread to handle it and add the client
    # to the list of clients.
    def listen(self):
        while True:
            client_socket, address = self.socket.accept()
            print("Connection from: " + str(address))

            # The first message will be the username
            client_name = client_socket.recv(1024).decode()
            client = {'client_name': client_name, 'client_socket': client_socket}

            # Broadcast that the new client has connected
            self.broadcast_message(client_name, client_name + " has joined the chat!")

            ServerPublisher.Clients.append(client)
            Thread(target = self.handle_new_client, args = (client,)).start()

    def handle_new_client(self, client):

        client_name = client['client_name']
        client_socket = client['client_socket']
        while True:
            # Listen out for messages and broadcast the message to all clients.
            client_message = client_socket.recv(1024).decode()
            # If the message is bye, remove the client from the list of clients and
            # close down the socket.
            if client_message.strip() == client_name + ": bye" or not client_message.strip():
                self.broadcast_message(client_name, client_name + " has left the chat!")
                ServerPublisher.Clients.remove(client)
                client_socket.close()
                break
            else: 
                # Send the message to all other clients
                self.broadcast_message(client_name, client_message)
                self.send_message(client_message)

    # Loop through the clients and send the message down each socket.
    # Skip the socket if it's the same client.
    def broadcast_message(self, sender_name, message):
        for client in self.Clients:
            client_socket = client['client_socket']
            client_name = client['client_name']
            if client_name != sender_name:
                client_socket.send(message.encode())

    # Publish Message over Node
    def send_message(self, message):
        msg = String()
        msg.data = message
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = ServerPublisher('192.168.137.94', 6000)
    rclpy.spin(minimal_publisher)
    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()