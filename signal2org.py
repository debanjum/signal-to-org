import sqlite3
from datetime import datetime


class Conversation:
    def __init__(self, thread_id) -> None:
        self.thread_id = thread_id
        self.messages = []

class User:
    pass

class Message:
    def __init__(self, date, body, thread) -> None:
        self.date = date
        self.body = body
        self.thread = thread
        self.sender = None

    def __repr__(self) -> str:
        return f'[{self.date.strftime("%Y-%m-%d %H:%M")}]: {self.sender}: {self.body}'

class SignalVDB:
    # contains group, user, message etc
    def __init__(self) -> None:
        self.conversations = [] 
        self.users = []
        self.messages = []

class signal2org:
    """
    """

    def __init__(self, sqlfile) -> None:
        #self.backup_file = backup_file
        # read backup file

        # call signal-to-org to decrypt

        self.sqlfile = sqlfile


        conn = sqlite3.connect(sqlfile)
        cur = conn.cursor()
        #ressms = cur.execute('select * from sms;').fetchall()
        sms = cur.execute('select date, body, thread_id from sms;').fetchall()
        mms = cur.execute('select date, body, thread_id from mms;').fetchall()

        messages = sms + mms
        vdb = SignalVDB()
        for message in messages:
            dt = datetime.utcfromtimestamp(message[0]/1e3)
            thread_id = message[2]

            conversation = [t for t in vdb.conversations if t.thread_id == thread_id]
            if not conversation:
                conversation = Conversation(thread_id)
                vdb.conversations.append(conversation)
            else:
                conversation = conversation[0]

            vdb.messages.append(
                Message(
                    date=dt,
                    body=message[1],
                    thread=conversation
                    )
                )
        self.vdb = vdb

        conn.close()



        print(sqlfile)
        exit

        self.signalvdb = None
        pass

    def export_org(self, outfile):
        with open(outfile, 'w') as fout:
            for message in self.vdb.messages:
                print(f'writing message {message}')
                fout.write(f'* {message} \n')

        # uses vdb to create org file




# read backup, outfile
signal_class = signal2org(sqlfile='data/database.sqlite')
signal_class.export_org('test.org')
#signal_class.export_org(outfile)