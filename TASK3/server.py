import socket
import threading
import random
import time

# Game configuration
TCP_PORT = 6000
UDP_PORT = 6001
SERVER_HOST = '0.0.0.0'
MIN_PLAYERS = 2
MAX_PLAYERS = 4
GUESS_TIMEOUT = 10
GAME_DURATION = 60
NUMBER_RANGE = (1, 100)

class GameServer:
    def __init__(self):
        self.clients = {}
        self.udp_addresses = {}
        self.secret_number = None
        self.game_active = False
        self.lock = threading.Lock()
        self.remaining_players = 0
        self.server_sock = None
        self.udp_sock = None

    def handle_tcp_client(self, tcp_socket, address):
        username = None
        try:
            tcp_socket.send(b"Welcome! Please enter: JOIN <username>\n")
            data = tcp_socket.recv(1024).decode().strip()
            
            if not data.startswith("JOIN "):
                tcp_socket.send(b"Invalid format. Use JOIN <username>\n")
                tcp_socket.close()
                return

            username = data.split(" ", 1)[1]
            with self.lock:
                if username in self.clients:
                    tcp_socket.send(b"Username taken. Use another name.\n")
                    tcp_socket.close()
                    return
                
                self.clients[username] = (tcp_socket, address)
                self.remaining_players += 1
                print(f"[TCP] {username} joined from {address}")
                self.broadcast_tcp(f"\nWaiting Room:\n{'\n'.join(self.clients.keys())}\n")

            tcp_socket.send(b"Registered successfully. Waiting for players...\n")

            with self.lock:
                if len(self.clients) >= MIN_PLAYERS and not self.game_active:
                    threading.Thread(target=self.start_game, daemon=True).start()
                    
            # Keep connection alive
            while True:
                try:
                    msg = tcp_socket.recv(1024)
                    if not msg:
                        break
                except:
                    break
                    
        except Exception as e:
            print(f"[TCP Error] {e}")
        finally:
            self.handle_disconnect(username)

    def handle_disconnect(self, username):
        if not username:
            return
            
        with self.lock:
            if username in self.clients:
                try:
                    self.clients[username][0].close()
                except:
                    pass
                del self.clients[username]
                self.remaining_players -= 1
                print(f"[SERVER] {username} disconnected")
                
                if self.game_active and self.remaining_players >= 1:
                    self.broadcast_tcp(f"\n {username} disconnected!!")
                    self.broadcast_tcp("Continue? (Y/N): ")

    def start_game(self):
        with self.lock:
            self.game_active = True
            self.secret_number = random.randint(*NUMBER_RANGE)
            print(f"[GAME] Secret number: {self.secret_number}")
            
            self.broadcast_tcp("\n=== GAME STARTED ===")
            self.broadcast_tcp(f"Players: {', '.join(self.clients.keys())}")
            self.broadcast_tcp(f"Guess between {NUMBER_RANGE[0]}-{NUMBER_RANGE[1]} (Time: {GAME_DURATION}s)\n")
            
            threading.Thread(target=self.udp_server, daemon=True).start()
            threading.Thread(target=self.game_timer, daemon=True).start()

    def game_timer(self):
        time.sleep(GAME_DURATION)
        if self.game_active:
            self.end_game()

    def broadcast_tcp(self, message):
        for username, (sock, _) in list(self.clients.items()):
            try:
                sock.send((message + "\n").encode())
            except:
                self.handle_disconnect(username)

    def udp_server(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind((SERVER_HOST, UDP_PORT))
        self.udp_sock.settimeout(1)
        
        while self.game_active and self.remaining_players > 0:
            try:
                data, addr = self.udp_sock.recvfrom(1024)
                self.process_guess(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[UDP Error] {e}")
                continue

        self.udp_sock.close()

    def process_guess(self, data, addr):
        try:
            guess_data = data.decode().strip().split()
            if len(guess_data) != 2:
                return

            username, guess = guess_data
            
            if username not in self.clients:
                return

            try:
                guess = int(guess)
                if not (NUMBER_RANGE[0] <= guess <= NUMBER_RANGE[1]):
                    self.udp_sock.sendto(b"ERROR: Number must be 1-100", addr)
                    return

                if guess < self.secret_number:
                    self.udp_sock.sendto(b"HINT: Higher", addr)
                elif guess > self.secret_number:
                    self.udp_sock.sendto(b"HINT: Lower", addr)
                else:
                    self.udp_sock.sendto(b"WINNER: Correct!", addr)
                    self.announce_winner(username)
                    
            except ValueError:
                self.udp_sock.sendto(b"ERROR: Invalid number", addr)
                
        except Exception as e:
            print(f"[Guess Processing Error] {e}")

    def announce_winner(self, winner):
        with self.lock:
            if not self.game_active:
                return
                
            self.broadcast_tcp("\n=== GAME OVER ===")
            self.broadcast_tcp(f"Secret number: {self.secret_number}")
            self.broadcast_tcp(f" Winner: {winner}")
            self.game_active = False
            self.reset_game()

    def end_game(self):
        with self.lock:
            if not self.game_active:
                return
                
            self.broadcast_tcp("\n=== TIME'S UP ===")
            self.broadcast_tcp(f"Secret number: {self.secret_number}")
            self.broadcast_tcp("No winner this round!")
            self.game_active = False
            self.reset_game()

    def reset_game(self):
        with self.lock:
            for sock, _ in self.clients.values():
                try:
                    sock.close()
                except:
                    pass
                    
            self.clients.clear()
            self.udp_addresses.clear()
            self.secret_number = None
            self.remaining_players = 0
            print("[SERVER] Game reset. Ready for new players.")

    def run(self):
        print("[DEBUG] Server is starting...")
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("[DEBUG] Socket created...")
        self.server_sock.bind((SERVER_HOST, TCP_PORT))
        print("[DEBUG] Socket bound to port...")
        self.server_sock.listen(MAX_PLAYERS)
        print(f"[SERVER] TCP listening on {TCP_PORT}, UDP on {UDP_PORT}")
        
        try:
            while True:
                client_sock, addr = self.server_sock.accept()
                threading.Thread(
                    target=self.handle_tcp_client,
                    args=(client_sock, addr),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.server_sock.close()
            if self.udp_sock:
                self.udp_sock.close()

if __name__ == "__main__":
    server = GameServer()
    server.run()