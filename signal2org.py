import sqlite3
from datetime import datetime


class Conversation:
    def __init__(self, thread_id, name) -> None:
        self.thread_id = thread_id
        self.messages = []
        self.name = name
        self.current_users = []

    def export(self, indent=0):
        ret = ""
        ret += f"{'*'*indent} {self.name} \n"
        for message in sorted(self.messages, key=lambda x: x.date):
            #print(f'writing message {message}')
            ret += f"{'*'*(indent+1)} {message.heading_str()} \n"
            ret += f'{message.body} \n'
            #fout.write(f'* {message} \n')
        return ret

    def add_message(self, message: "Message"):
        self.messages.append(message)

class User:
    def __init__(self) -> None:
        pass

class Message:
    def __init__(self, date, body, conversation: Conversation) -> None:
        self.date = date
        self.body = body if body else ""
        self.conversation = conversation
        self.sender = None

    def heading_str(self) -> str:
        body_header = self.body.split('\n')[0]
        return f'[{self.date.strftime("%Y-%m-%d %H:%M")}] {self.sender}: {body_header}'

    def __repr__(self) -> str:
        return f'[{self.date.strftime("%Y-%m-%d %H:%M")}]: {self.sender}: {self.body}'

class SignalVDB:
    # contains group, user, message etc
    def __init__(self) -> None:
        self.conversations = [] 
        self.users = []

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

        conversation_name_dict = {}

        threads = cur.execute('select _id, thread_recipient_id from thread;').fetchall()
        for thread in threads:
            recipients = cur.execute(f'select system_display_name, group_id from recipient where _id={thread[1]};').fetchall()
            for recipient in recipients:
                if recipient[1]: #group id
                    group = cur.execute(f'select title from groups where recipient_id={thread[1]};').fetchone()
                    conversation_name_dict[thread[0]] = group[0]
                else:
                    conversation_name_dict[thread[0]] = recipient[0]



        messages = sms + mms
        vdb = SignalVDB()
        for message in messages:
            dt = datetime.utcfromtimestamp(message[0]/1e3)
            thread_id = message[2]

            conversation = [t for t in vdb.conversations if t.thread_id == thread_id]
            if not conversation:
                conversation = Conversation(thread_id, name=conversation_name_dict[thread_id])
                vdb.conversations.append(conversation)
            else:
                conversation = conversation[0]

            conversation.add_message(
                Message(
                    date=dt,
                    body=message[1],
                    conversation=conversation
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
            for conversation in self.vdb.conversations:
                fout.write(conversation.export(indent=1))

        # uses vdb to create org file




# read backup, outfile
signal_class = signal2org(sqlfile='data/database.sqlite')
signal_class.export_org('test.org')
#signal_class.export_org(outfile)