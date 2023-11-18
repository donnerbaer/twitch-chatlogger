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
        cursor = self.conn.cursor()
        try:
            cursor.execute('INSERT INTO twitch_chat (channel, username, message, timestamp) VALUES (?, ?, ?, ?)', (channel, username, message, datetime.now()))
        except:
            pass



    def load_channels(self) -> None:
        """ loads a file with channel names; one channel per line
        """
        f = open(self.CHANNEL_FILE, "r")
        for entry in f:
            self.CHANNEL_LIST.append(entry.replace('\n',''))
        f.close()



    def join_channel(self, channel:str) -> None:
        """ a single channel join

        Args:
            channel (str): name of the channel
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
        join = f"JOIN {join}\r\n".encode('utf-8')
        print(f'{datetime.now()}      Send to service: {join}')
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
                print(f'{datetime.now()}    {message}')
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
                username = text[0][1:text[0].find('!')]
                channel = text[1][:text[1].find(' ')]
                message = text[1][text[1].find(':')+1:]
                self.insert_message(channel, username, message)
            except:
                continue

        self.conn.commit()
        self.conn.close()
            


    def send_pong(self):
        self.Socket.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
        print(f'{datetime.now()}    send pong')


    def main(self):
        """_summary_
        """
        self.Socket.connect((self.SERVER, self.PORT))
        self.Socket.send(f"PASS {self.TOKEN}\r\n".encode('utf-8'))
        self.Socket.send(f"NICK {self.NICKNAME}\r\n".encode('utf-8'))

        self.last_join = datetime.now() - timedelta(seconds=11)

        self.load_channels()
        #self.join_channel('')
        
        try:
            while True:
                #time_now = datetime.now()
                if len(self.CHANNEL_LIST) > 0:
                    if datetime.now() - self.last_join > timedelta(seconds=11):
                        self.join_channels_batch()

                try:
                    resp = self.Socket.recv(8388608).decode('utf-8')
                    self.last_time_recived = datetime.now()
                except:
                    self.send_pong()
                    print(f'{datetime.now()}    ERROR Decode')

                if resp.find('PING :tmi.twitch.tv')>-1:
                    print(f'{datetime.now()}    RECEIVED PONG')
                    self.send_pong()
                    
                if len(resp) > 0:
                    print(datetime.now())
                    self.process_response(resp)

                if datetime.now() - self.last_time_recived > timedelta(minutes=11):
                    self.CHANNEL_LIST = [] 
                    self.load_channels()

        except KeyboardInterrupt:
            print(f'{datetime.now}      Socket closed')
            self.Socket.close()
        
            


if __name__ == '__main__':
    TwitchLogger().create_database()
    TwitchLogger().main()
    
