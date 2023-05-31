import json, socket, struct, random, os, sys, requests
from threading import Thread
from datetime import datetime, timedelta
import src.logs as logs
import lookups.words
from src.database import Data
from src.mojang import MojangAPI

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

class SocketServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = logs.init_logger()

    def on_new_client(self, client_socket: socket.socket, addr):
        # Get data from connection
        try:
            data = client_socket.recv(4096)
        except:
            return

        # Get packet type
        (_, i) = self.read_varint(data, 0)
        (packetID, i) = self.read_varint(data, i)

        if packetID != 0:
            return

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
            return
        
        # Connection has been attempted, send verification code and related info
        name = ""
        if len(data) != i:
            (_, i) = self.read_varint(data, i)
            (_, i) = self.read_varint(data, i)
            (name, i) = self.read_utf(data, i)

        # If cant get connecting players username for some reason
        if not name:
            self.logger.info("An unknown user failed to join the verification server.")

            self.write_response(client_socket, json.dumps(
                {"text": "§cError: Please try again\n§cIf the issue persists, please contact staff to manually verify you."}))
            
            return

        time = datetime.utcnow()
        player_uuid = MojangAPI.get_uuid_from_name(name)

        self.logger.info(f"{name} ({player_uuid}) joined the verification server.")

        #If user is verified, say so and tell them how they can unverify
        try:
            user = Data.get_data_item(key=player_uuid, table="verified", name="verification")
            self.write_response(client_socket, json.dumps(
                                {"text": f"§rThis account has already been verified!\n" +
                                 "If you wish to unlink it, use §a/unverify §rin §a#bot-commands§r.\n" +
                                 "If you are having trouble doing this or believe this is a mistake, please contact staff."}))
            return
        except:
            pass

        # Check if user has a pending code
        try:
            user = Data.get_data_item(key=player_uuid, table="pending", name="verification")
            generation_time = datetime.strptime(user['time'], "%m/%d/%Y, %H:%M:%S")

            difference = time - generation_time

            # If greater than an hour
            if difference.total_seconds() > 3600:
                Data.delete_item(item=user, table="pending", name="verification")
            else:
                # User is still pending, display their existing code and time remaining

                minutes, seconds = divmod(difference.total_seconds(), 60)

                self.write_response(client_socket, json.dumps(
                {"text": (f"§rLink your MC account!\n" +
                        f"Your code: §a{user['phrase']}\n" +
                        "§rUse §a/verify <code> §rin §a#bot-commands §rto complete verification.\n" +
                        f"Your code will expire in §a{59-int(minutes)} minutes" +
                        f" §rand §a{59-int(seconds)} seconds§r!")}))
                return
        except:
            pass

        phrase = (random.choice(lookups.words.ADJECTIVES).capitalize() + ' ' +
                    random.choice(lookups.words.NAMES).capitalize() + ' ' +
                    random.choice(lookups.words.ACTIONS) + ' ' +
                    random.choice(lookups.words.NAMES).capitalize() + ' ' +
                    random.choice(lookups.words.TIMES))
        
        Data.set_data_item(key=player_uuid, value={"time": time.strftime("%m/%d/%Y, %H:%M:%S"), "phrase": phrase}, table="pending", name="verification")
        self.write_response(client_socket, json.dumps(
            {"text": (f"§rLink your MC account!\n" +
                        f"Your code: §a{phrase}\n" +
                        "§rUse §a/verify <code> §rin §a#bot-commands §rto complete verification.\n" +
                        "Your code will expire in §a59 minutes §rand §a59 seconds§r!")}))
                
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