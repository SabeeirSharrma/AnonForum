# AnonForum

![GitHub last commit (branch)](https://img.shields.io/github/last-commit/SabeeirSharrma/AnonForum/main)
![GitHub forks](https://img.shields.io/github/forks/SabeeirSharrma/AnonForum)
![GitHub Release](https://img.shields.io/github/v/release/SabeeirSharrma/AnonForum)

A lightweight, locally-hosted forum/chat application built with **Flask**, **Socket.IO**, **SQLite**, and a **PyQt5** GUI for server management.

---

## Features

- **Host your own forums** locally over HTTP.
- **Multiple threads** per forum, with real-time chat posts.
- **Nickname support** for each user.
- **Web interface**: create threads, post messages, delete threads.
- **PyQt5 UI**:
  - Start, stop, and restart the server.
  - View logs in real-time.
  - Edit server configuration (`HOST`, `PORT`, limits for usernames, thread titles, post content).
  - Wipe all forums and reset database.
- **Auto-increment thread IDs**, resettable on wipe.
- **Duplicate thread prevention**.
- **Real-time updates** using WebSockets.

---

## Requirements

- Python 3.10+
- Packages:

```bash
pip install flask flask-socketio eventlet PyQt5
```
---
## Config

```
{
  "HOST": "127.0.0.1",
  "PORT": 8080,
  "DEBUG": true,
  "LIMITS": {
    "USERNAME": 50,
    "THREAD_TITLE": 200,
    "POST_CONTENT": 1000
  }
}
```
- HOST: Server host address.

- PORT: Port to run the server.

- DEBUG: Enable Flask debug mode.

- LIMITS:

  - USERNAME: Max username length.

  - THREAD_TITLE: Max thread title length.

  - POST_CONTENT: Max post content length.
---
## Running the Application
1. Using the PyQt5 GUI
```python main.py```


Use Start to run the server.

Use Stop to safely stop the server.

Use Restart to restart the server.

Edit configuration fields in the GUI and apply changes live.

Click Wipe All Forums to reset the database and IDs.

2. Access the Forum

Open a browser and go to:

```http://localhost:<PORT>```

Enter a nickname and start chatting.

Create threads, post messages, and see updates in real-time.

---
## API Endpoints

| Method | Endpoint                         | Description                         |
| ------ | -------------------------------- | ----------------------------------- |
| GET    | `/api/threads`                   | List all threads                    |
| POST   | `/api/threads`                   | Create a new thread                 |
| GET    | `/api/threads/<thread_id>/posts` | Get posts in a thread               |
| POST   | `/api/threads/<thread_id>/posts` | Post a message to a thread          |
| DELETE | `/api/threads/<thread_id>`       | Delete a specific thread            |
| DELETE | `/api/threads/wipe`              | Wipe all threads and reset database |

---
## Notes

- Duplicate threads are not allowed; titles must be unique.

- Thread IDs auto-increment but reset when “Wipe All” is used.

- PyQt5 GUI prevents socket conflicts by disabling Flask debug reloader when running in threads.

---
## License
MIT License – free to use and modify.

---

