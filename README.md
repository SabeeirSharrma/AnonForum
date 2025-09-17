## AnonForum ✨

![GitHub last commit (branch)](https://img.shields.io/github/last-commit/SabeeirSharrma/AnonForum/main)
![GitHub forks](https://img.shields.io/github/forks/SabeeirSharrma/AnonForum)
![GitHub Release](https://img.shields.io/github/v/release/SabeeirSharrma/AnonForum)


**AnonForum** is a lightweight, locally-hosted forum and chat application designed for easy, private communication. Built with **Flask** and **Socket.IO**, it provides real-time chat functionality, with a **PyQt5** GUI for simple server management.

-----

### Features 🚀

  * **Host Your Own Forum:** Run a local forum over HTTP, perfect for small groups or private use 🏡.
  * **Real-Time Chat:** Engage in multiple, dynamic discussion threads with real-time updates powered by WebSockets 💬.
  * **User-Friendly Web Interface:** Easily create and delete threads and post messages from your browser 🌐.
  * **Flexible Configuration:** Use the PyQt5 GUI to start, stop, or restart the server and edit settings like the host, port, and content length limits ⚙️.
  * **Database Management:** The GUI allows you to view server logs in real-time 📊 and even wipe the entire database to reset all forums and thread IDs 🗑️.
  * **Unique Threads:** Prevents duplicate threads by requiring unique titles ✍️.

-----

### Requirements 📋

To run AnonForum, you'll need **Python 3.10+** and the following packages. You can install them all at once using pip:

```bash
pip install flask flask-socketio eventlet PyQt5
```

-----

### Configuration 🔧

The server configuration can be edited directly in the PyQt5 GUI. Here's a breakdown of the available settings:

```json
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

  * `HOST`: The IP address the server will run on 💻.
  * `PORT`: The port for the server 🚪.
  * `DEBUG`: Enables Flask's debug mode for development 🐞.
  * `LIMITS`: Specifies the maximum character count for usernames, thread titles, and post content 📏.

-----

### Getting Started 🚀

#### 1\. Run the Application

Start the application using the PyQt5 GUI for full control:

```bash
python main.py
```

  * Use the **Start**, **Stop**, and **Restart** buttons to manage the server's status ▶️⏸️🔄.
  * Edit the configuration fields and click **Apply** to save your changes live ✅.
  * Select **Wipe All Forums** to completely reset the database and all thread IDs 💥.

#### 2\. Access the Forum

Once the server is running, open your web browser and go to:

`http://localhost:<PORT>`

Replace `<PORT>` with the port number you've configured. You can then enter a nickname, create new threads, and start chatting in real-time 🗣️.

-----

### API Endpoints 🔌

AnonForum provides a simple REST API for managing forum content:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/threads` | Lists all available threads 📜. |
| `POST` | `/api/threads` | Creates a new thread ✨. |
| `GET` | `/api/threads/<thread_id>/posts` | Retrieves all posts within a specific thread 📩. |
| `POST` | `/api/threads/<thread_id>/posts` | Adds a new post to a thread ➕. |
| `DELETE` | `/api/threads/<thread_id>` | Deletes a specific thread and all its posts ❌. |
| `DELETE` | `/api/threads/wipe` | Wipes the entire database, deleting all threads 🔥. |

-----

### Notes 📝

  * **Unique Titles:** To prevent clutter, a new thread can't be created if a thread with the same title already exists 🚫.
  * **Auto-Incrementing IDs:** Thread IDs are automatically assigned and reset to `1` when the "Wipe All Forums" function is used 🔢.
  * **Conflict Prevention:** The PyQt5 GUI is designed to manage the Flask server in a way that avoids conflicts by disabling the debug reloader 🛡️.

-----

### License 📜

This project is open-source and available under the **MIT License**. Feel free to use, modify, and distribute it.
