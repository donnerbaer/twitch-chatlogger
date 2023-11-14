import socket
from datetime import datetime, timedelta
import configuration
import sqlite3


class TwitchLogger:
    """
    Get token here: https://twitchapps.com/tmi/

    max. 20 Channel joins per 10s
    """
    
    CHANNEL_FILE = 'ChannelList.txt'
    Socket = socket.socket()
    CHANNEL_LIST = []
    

    def __init__(self) -> None:
        self.SERVER = configuration.SERVER
        self.PORT = configuration.PORT
        self.NICKNAME = configuration.NICKNAME
        self.TOKEN = configuration.TOKEN


    def create_database(self):
        """_summary_
        """
        conn = sqlite3.connect(configuration.DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS twitch_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                username TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()


    def insert_message(self, channel, username, message):
        """_summary_

        Args:
            channel (_type_): _description_
            username (_type_): _description_
            message (_type_): _description_
        """
        #conn = sqlite3.connect(configuration.DATABASE)
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO twitch_chat (channel, username, message, timestamp) VALUES (?, ?, ?, ?)', (channel, username, message, datetime.now()))
        except:
            pass


    def load_channels(self) -> None:
        """_summary_
        """
        f = open(self.CHANNEL_FILE, "r")
        for entry in f:
            self.CHANNEL_LIST.append(entry.replace('\n',''))
        f.close()
        #print("Num of entries: {}".format(len(self.CHANNEL_LIST)))


    def join_channel(self, channel:str) -> None:
        """ a single channel join

        Args:
            channel (str): _description_
        """
        self.Socket.send(f"JOIN #{channel}\r\n".encode('utf-8'))   


    def join_channels_batch(self):
        """_summary_
        """
        batch = 20
        if len(self.CHANNEL_LIST) % 20 > 0:
            batch = len(self.CHANNEL_LIST) % 20

        join = ""
        for _ in range(0,batch,1):
            join = join + "#{},".format(self.CHANNEL_LIST.pop())
        join = join[:-1]
        #join = join + "\r\n"
        join = f"JOIN {join}\r\n".encode('utf-8')
        #print("Send to service: {}".format(join))
        self.Socket.send(join)   
        self.last_join = datetime.now()


    def process_response(self, resp:str):
        """_summary_

        Args:
            resp (str): _description_
        """
        self.conn = sqlite3.connect(configuration.DATABASE)
        messages = resp.splitlines()
        for message in messages:
            if self.NICKNAME in message:
                continue 
            if "PING :tmi.twitch.tv" in message:
                continue
            if ":tmi.twitch.tv RECONNECT" in message:
                continue
            if not '#' in message:
                continue

            text = message.split("#",1)
            if not '!' in text[0]:
                continue
            if not ':' in text[1]:
                continue
            try:
                #print(text)
                username = text[0][1:text[0].find('!')]
                #print("username: {}".format(username))
                channel = text[1][:text[1].find(' ')]
                #print("channel: {}".format(channel))
                message = text[1][text[1].find(':')+1:]
                #print("message: {}".format(message))
                self.insert_message(channel, username, message)
            except:
                continue
        self.conn.commit()
        self.conn.close()
        #print(datetime.now())
            


    def main(self):
        """_summary_
        """
        self.Socket.connect((self.SERVER, self.PORT))
        self.Socket.send(f"PASS {self.TOKEN}\r\n".encode('utf-8'))
        self.Socket.send(f"NICK {self.NICKNAME}\r\n".encode('utf-8'))

        self.last_join = datetime.now() - timedelta(seconds=11)

        self.load_channels()

        try:
            while True:
                time_now = datetime.now()
                if len(self.CHANNEL_LIST) > 0:
                    
                    if time_now - self.last_join > timedelta(seconds=11):
                        #print(time_now)
                        self.join_channels_batch()
                    #if len(self.CHANNEL_LIST) == 0:
                    #    reconnect = False
                
                resp = self.Socket.recv(1048576).decode('utf-8')
                if resp.find('PING :tmi.twitch.tv')>-1:
                    self.Socket.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
                    #print(f'{datetime.now()} send pong')
                #if resp.find(':tmi.twitch.tv RECONNECT') and not reconnect:
                #    reconnect = True
                #    self.load_channels()
                if len(resp) > 0:
                    #print(time_now)
                    #print(resp)
                    self.process_response(resp)

        except KeyboardInterrupt:
            self.Socket.close()
            


if __name__ == '__main__':
    TwitchLogger().create_database()
    TwitchLogger().main()
    
