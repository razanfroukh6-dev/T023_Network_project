Socket Programming Project (Web Server & Multiplayer Game)

This project demonstrates practical implementation of computer networking concepts using Python socket programming. It consists of three main tasks covering network analysis, web server development, and a multiplayer game using TCP/UDP protocols.

Features
Network analysis using common commands and Wireshark
HTTP web server built using Python sockets
Multilingual web pages (English & Arabic)
File handling with support for images, videos, and redirection
Multiplayer guessing game using TCP/UDP hybrid communication
Real-time client-server interaction
_Project Structure
Task 1 – Network Commands & Wireshark
Used tools like:
ipconfig, ping, tracert, nslookup, telnet
Captured and analyzed DNS traffic using Wireshark
Verified domain-to-IP resolution and network behavior
Task 2 – Web Server (Socket Programming)
Built a simple HTTP web server using Python
Served static web pages (HTML, CSS, images, videos)
Supported:
English & Arabic pages
Local file requests
Error handling (404 Not Found)
Redirection to Google/YouTube for missing media (307 Redirect)

Key Concepts:

HTTP request/response handling
Content-Type detection
File serving and routing
Task 3 – TCP/UDP Hybrid Guessing Game
Multiplayer game using:
TCP → registration & game control
UDP → fast guessing communication

Game Features:

Multiple players
Real-time guessing
Server feedback (Higher / Lower / Correct)
Winner announcement
Handling disconnections
Technologies Used
Python (socket, threading, random, time)
HTML & CSS
Wireshark
Testing & Results
Verified network connectivity and DNS resolution
Tested HTTP requests and server responses
Validated game scenarios:
Normal gameplay
Invalid guesses
Player disconnection
Ports Used
Web Server: 9912
Game TCP: 6000
Game UDP: 6001
