import socket
import threading
import time

TCP_HOST = '127.0.0.1'  # Server address (localhost)
TCP_PORT = 6000         # Must match the server's TCP port
UDP_PORT = 6001         # Must match the server's UDP port

class GameClient:
    def __init__(self):
        self.username = self.get_username()
        self.tcp_sock = None
        self.udp_sock = None
        self.game_started = threading.Event()
        self.continue_game = threading.Event()
        self.continue_game.set()

    def get_username(self):
        while True:
            username = input("Enter your username: ").strip()
            if username and ' ' not in username:
                return username
            print("Invalid username (no spaces allowed)")

    def tcp_listener(self):
        while self.continue_game.is_set():
            if not self.tcp_sock:
                break
            try:
                message = self.tcp_sock.recv(1024).decode().strip()
                if not message:
                    break

                print(f"\n{message}")

                if "Continue playing?" in message:
                    choice = input("\n" + message + " ")
                    self.tcp_sock.send(choice.encode())
                    if choice.upper() != 'Y':
                        self.continue_game.clear()
                        break

                if "GAME STARTED" in message:
                    self.game_started.set()

            except Exception as e:
                print(f"\nConnection error: {e}")
                self.continue_game.clear()
                break

    def udp_guess_loop(self):
        server_addr = (TCP_HOST, UDP_PORT)
        self.udp_sock.settimeout(2)
        start_time = time.time()
        time_left = 60

        while self.continue_game.is_set() and time_left > 0:
            try:
                time_left = max(0, 60 - (time.time() - start_time))

                if time_left == 0:
                    print("\nTime is up!")
                    self.continue_game.clear()
                    break

                guess = input(f"\nEnter guess (1-100) [Time left: {int(time_left)}s]: ").strip()

                if not guess.isdigit():
                    print("Please enter a valid number between 1-100")
                    continue

                self.udp_sock.sendto(f"{self.username} {guess}".encode(), server_addr)

                try:
                    response, _ = self.udp_sock.recvfrom(1024)
                    response = response.decode()

                    if "WINNER" in response:
                        print(f"\n🎉 {response}")
                        self.continue_game.clear()
                        break
                    else:
                        print(f"\n{response}")
                except socket.timeout:
                    print("No response from server. Retrying...")

            except Exception as e:
                print(f"\nUDP error: {e}")
                break

    def run(self):
        try:
            # Create TCP connection
            self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_sock.connect((TCP_HOST, TCP_PORT))
            self.tcp_sock.send(f"JOIN {self.username}".encode())

            # Create UDP socket
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Start TCP listener thread
            threading.Thread(target=self.tcp_listener, daemon=True).start()

            print(f"\nConnected as: {self.username}")
            print("Waiting for the game to start...")

            self.game_started.wait()
            if self.continue_game.is_set():
                self.udp_guess_loop()

        except Exception as e:
            print(f"\nFatal error: {e}")
        finally:
            if self.tcp_sock:
                try:
                    self.tcp_sock.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                self.tcp_sock.close()
            if self.udp_sock:
                try:
                    self.udp_sock.close()
                except:
                    pass
            print("\nGame session ended.")

if __name__ == "__main__":
    client = GameClient()
    client.run()
