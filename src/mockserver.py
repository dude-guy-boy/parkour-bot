import json, socket, struct, random, os, sys, requests
from threading import Thread
from datetime import datetime, timedelta
import src.logs as logs
# import words

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

# import json_management as j

class SocketServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = logs.init_logger()

    # TODO: Figure out server timeout thing
    # TODO: Finish reimplementing

    def on_new_client(self, client_socket: socket.socket, addr):
        # Get data from connection
        try:
            data = client_socket.recv(4096)
        except:
            return

        try:
            # Get packet type
            (_, i) = self.read_varint(data, 0)
            (packetID, i) = self.read_varint(data, i)

            if packetID == 0:
                # Do some stuff idk
                (_, i) = self.read_varint(data, i)
                (_, i) = self.read_utf(data, i)
                (_, i) = self.read_ushort(data, i)
                (state, i) = self.read_varint(data, i)

                # If pinged in server list, show motd and other normal server list info
                if state == 1:                    
                    motd = {}
                    motd["version"] = {}
                    motd["version"]["name"] = ""
                    motd["version"]["protocol"] = 47
                    motd["players"] = {}
                    motd["players"]["max"] = 0
                    motd["players"]["online"] = 0
                    motd["players"]["sample"] = []
                    motd["description"] = {
                        "text": "§7Verify Your Account!"}

                    self.write_response(client_socket, json.dumps(motd))

                # If connection is attempted, send kick message
                elif state == 2:
                    name = ""
                    if len(data) != i:
                        (_, i) = self.read_varint(data, i)
                        (_, i) = self.read_varint(data, i)
                        (name, i) = self.read_utf(data, i)

                    if(name):
                        # Log join attempt
                        self.logger.info(f"{name} joined the verification server.")

                        # pending = j.json_get_var(
                        #     "./data/verification.json", "pending")
                        # verified = j.json_get_var(
                        #     "./data/verification.json", "verified")
                        # 
                        # if(not pending):
                        #     pending = []

                        # if(not verified):
                        #     verified = []

                        # Check if user is already verified
                        # for user in verified:
                        #     if(verified[user]['username'] == name):
                        #         self.write_response(client_socket, json.dumps(
                        #             {"text": f"§rThis account has already been verified!\nIf you wish to unlink it, use §a/unverify §rin §a#bot-commands§r."}))
                        #         return

                        # Check if user is already pending
                        # for user in pending:
                        #     if(name in user.keys()):
                        #         generation_time = datetime.strptime(
                        #             user[name]['time'], "%m/%d/%Y, %H:%M:%S")
                        #         current_time = datetime.utcnow()

                        #         difference = current_time - generation_time

                        #         # If longer than an hour, break and generate new code
                        #         if((difference.seconds % 3600) // 60 > 60):
                        #             pending.remove(user)
                        #             break

                        #         self.write_response(client_socket, json.dumps(
                        #             {"text": f"§rVerify your Minecraft Parkour Community Account!\nYour code: §a{user[name]['code']}\n§rUse §a/verify <code> §rin §a#bot-commands §rto complete verification.\nYour code will expire in §a{60-((difference.seconds % 3600) // 60)} minutes §rand §a{60-(difference.seconds % 60)} seconds§r!"}))
                        #         return

                        self.write_response(client_socket, json.dumps(
                            {"text": f"§rVerify your Minecraft Parkour Community Account!"}))
                        return

                        data = requests.get(
                            f"https://api.mojang.com/users/profiles/minecraft/{name}").json()

                        # If user is not verified yet, generate their code
                        code = f"{random.choice(words.ADJECTIVES).capitalize()} {random.choice(words.NAMES).capitalize()} {random.choice(words.ACTIONS)} {random.choice(words.NAMES).capitalize()} {random.choice(words.TIMES)}"
                        current_time = datetime.utcnow().strftime("%m/%d/%Y, %H:%M:%S")
                        mins = 59
                        seconds = 59

                        # Override time if theyre pending already

                        # Add them to pending
                        pending.append({data['name']: {"id": data['id'], "code": code, "time": current_time}})
                        j.json_set_var("./data/verification.json", "pending", pending)

                        self.write_response(client_socket, json.dumps(
                            {"text": f"§rVerify your Minecraft Parkour Community Account!\nYour code: §a{code}\n§rUse §a/verify <code> §rin §a#bot-commands §rto complete verification.\nYour code will expire in §a{mins} minutes §rand §a{seconds} seconds§r!"}))
                    else:
                        self.logger.info("Someone tried to join the verification server")
                        self.write_response(client_socket, json.dumps(
                        {"text": "§cError: Please try again\n§cIf the issue continues, contact staff to manually verify you."}))

        except (TypeError, IndexError):
            self.logger.warning("Received invalid data")
            return

    def write_response(self, client_socket, response):
        response_array = bytearray()
        self.write_varint(response_array, 0)
        self.write_utf(response_array, response)
        length = bytearray()
        self.write_varint(length, len(response_array))
        client_socket.sendall(length)
        client_socket.sendall(response_array)

    def start(self):
        # This is what actually starts the server
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", 25565))
        self.sock.settimeout(5000)
        self.sock.listen(30)
        self.logger.info("Verification server started")
        while 1:
            try:  
                # Waits for connections
                (client, address) = self.sock.accept()

                # Starts a new thread of on_new_client
                Thread(target=self.on_new_client, daemon=True, args=(client, address,)).start()
            except TimeoutError:
                pass

    def read_varint(self, byte, i):
        result = 0
        bytes = 0
        while True:
            byte_in = byte[i]
            i += 1
            result |= (byte_in & 0x7F) << (bytes * 7)
            if bytes > 32:
                raise IOError("Packet is too long!")
            if (byte_in & 0x80) != 0x80:
                return result, i

    def read_utf(self, byte, i):
        (length, i) = self.read_varint(byte, i)
        ip = byte[i:(i + length)].decode('utf-8')
        i += length
        return ip, i

    def read_ushort(self, byte, i):
        new_i = i + 2
        return struct.unpack(">H", byte[i:new_i])[0], new_i

    def read_long(self, byte, i):
        new_i = i + 8
        return struct.unpack(">q", byte[i:new_i]), new_i

    def write_varint(self, byte, value):
        while True:
            part = value & 0x7F
            value >>= 7
            if value != 0:
                part |= 0x80
            byte.append(part)
            if value == 0:
                break

    def write_utf(self, byte, value):
        self.write_varint(byte, len(value))
        for b in value.encode():
            byte.append(b)

    def close(self):
        self.sock.close()

def start():
    server = SocketServer()
    server.start()

if __name__ == "__main__":
    start()