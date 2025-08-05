
# 👻 Ghost Port

**Ghost Port** is a lightweight, secure, WebSocket-based tunneling system that connects a central **Hub** to remote **Clients (Houses)** across firewalls, CGNATs, or private networks.

It enables the Hub to send HTTP-like commands and receive responses from any connected House as if it were a local API.

---

## 🔧 Use Cases

- Access internal services behind firewalls or NAT
- Build remote diagnostic or IoT control systems
- Lightweight alternative to VPN or SSH tunneling
- Relay data in low-connectivity or restricted networks
- Cloud-to-edge secure communication system

---

## 🏗️ Architecture
```

Hub (Django + Channels) ─── WebSocket ───▶ Client (House)
↑                                        ↓
└────── Receives HTTP-like responses ◀──┘

```

- The **Hub** runs Django with Channels to manage WebSocket tunnels from each Client.
- Each **Client** (called a **House**) maintains a persistent WebSocket connection with the Hub.
- The Hub sends requests through WebSockets to the correct House.
- The House executes the request and sends the response back to the Hub.

---

## ⚙️ Tech Stack

| Component     | Technology               |
|---------------|--------------------------|
| Backend       | Django, Django Channels  |
| Communication | WebSocket                |
| Message Layer | Redis (`channels_redis`) |
| Database      | PostgreSQL (or SQLite)   |
| Language      | Python 3.10+             |
| Deployable    | Docker (optional)        |

---

## 📂 Project Structure
```

ghostport/
├── ghostport/              # Django project settings
├── tunnel/                 # App: models, consumers, utils
│   ├── [consumers.py](http://consumers.py)        # WebSocket logic
│   ├── [models.py](http://models.py)           # HouseTunnel model
│   ├── [utils.py](http://utils.py)            # Response queue mapping
├── [manage.py](http://manage.py)
├── requirements.txt
├── docker-compose.yml     # Optional
└── [README.md](http://README.md)

```

---

## 🔐 Authentication Protocol

Each House has:
- A unique `house_id`
- A secret key stored on the server

The House sends:
```json
{
  "action": "authenticate",
  "house_id": "abc123",
  "auth_hash": "<sha256(house_id + secret_key)>"
}
```

The Hub verifies the hash and authenticates the connection.


---

## 🚀 Setup Guide

### 🔹 1. Clone and Install Dependencies

```bash
git clone https://github.com/yourusername/ghostport.git
cd ghostport
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 🔹 2. Install Redis

#### On Linux:

```bash
sudo apt install redis
```

#### On Windows (use Docker):

```bash
docker run -p 6379:6379 redis
```

### 🔹 3. Django Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```


---

## 🧠 Key Files and Concepts

### `tunnel/consumers.py`

Handles:

* WebSocket connection and disconnection
* Authentication logic
* Receiving responses from Houses
* Forwarding HTTP frames to Houses

### `tunnel/models.py`

Stores:

* `HouseTunnel`: Tracks house_id, connection status, secret key, and last_seen timestamp.

### `tunnel/utils.py`

In-memory map:

```python
pending_responses = {
    "<frame_id>": asyncio.Future()
}
```

Used to correlate HTTP requests sent to a house with its response.


---

## 🧪 Example Usage

**Send a request from Hub to a House:**

```python
# Inside a Django view
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid

channel_layer = get_channel_layer()
frame_id = str(uuid.uuid4())

# Store the response handler
future = asyncio.get_event_loop().create_future()
pending_responses[frame_id] = future

# Send the event to the group
async_to_sync(channel_layer.group_send)(
    "house_abc123",
    {
        "type": "forward.http",
        "id": frame_id,
        "method": "GET",
        "path": "/status",
        "headers": {},
        "body": ""
    }
)

# Wait for the response
response = await future
```


---

## 🐳 Docker (Optional)

To dockerize the setup:

```bash
# docker-compose.yml
services:
  redis:
    image: redis
    ports:
      - "6379:6379"
  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 ghostport.asgi:application
    ports:
      - "8000:8000"
    depends_on:
      - redis
```

Build & run:

```bash
docker-compose up --build
```


---

## 🔮 Future Enhancements

* End-to-end encryption for tunneled requests
* House reconnection/resilience support
* Web dashboard for managing connections
* Support for multiplexed streams over one WebSocket
* Comparison benchmarks vs VPN, SSH tunnel, ZeroTier


---

## 📄 License

MIT License © 2025 Ganapathi Kodi


---

## 👤 Author

**Lakshmi Ganapathi Kodi**
*B.Tech Mathematics & Computing, NIT Mizoram*
GitHub: [@ganapathikodi](https://github.com/ganapathi1578)

