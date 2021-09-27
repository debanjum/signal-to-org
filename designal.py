# Standard Packages
import argparse
from datetime import datetime
import pathlib

# External Packages
import sqlite3


class Conversation:
    """
    A Signal Conversation
    """
    def __init__(self, thread_id, name) -> None:
        self.thread_id = thread_id
        self.messages = []
        self.name = name
        self.current_users = []

    def export(self, indent=0):
        ret = ""
        ret += f"{'*'*indent} {self.name}\n"
        for message in sorted(self.messages, key=lambda x: x.date):
            ret += f"{'*'*(indent+1)} {message.heading_str()}\n"
            ret += f'{message.body}\n'
        return ret

    def add_message(self, message: "Message"):
        self.messages.append(message)


class User:
    """
    A Signal User
    """
    def __init__(self) -> None:
        pass


class Message:
    """
    A Signal Message
    """
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
    """
    In-Memory DB. Stores an Intermediate Representation of Signal conversations
    """
    # contains group, user, message etc
    def __init__(self) -> None:
        self.conversations = [] 
        self.users = []
        self.messages = []


class Signal:
    """
    Main Interface to Load, Export Signal Conversations from Backups
    """

    def __init__(self, sqlfile, verbose=0) -> None:
        # TODO: read backup file amd decrypt it to sqlite
        self.sqlfile = sqlfile
        self.verbose = verbose
        self.vdb = self.load_db(self.sqlfile)

    def load_db(self, sqlfile):
        # open connection to sqlite db
        vdb = SignalVDB()
        conn = sqlite3.connect(sqlfile)
        cur = conn.cursor()

        # Get all plain and rich-text Signal messages
        sms = cur.execute('select date, body, thread_id from sms;').fetchall()
        mms = cur.execute('select date, body, thread_id from mms;').fetchall()
        messages = sms + mms

        # Create Thread Id to Conversation Name Map
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

        # Load Signal data into VDB in an intermediate representation
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
        conn.close()

        return vdb

    def export_org(self, outfile):
        """Create Org File from Virtual DB
        """
        with open(outfile, 'w') as fout:
            for conversation in self.vdb.conversations:
                fout.write(conversation.export(indent=1))


if __name__ == '__main__':
    # Setup Argument Parser for the Commandline Interface
    parser = argparse.ArgumentParser(description="An Exporter of Signal Conversations")
    parser.add_argument('--sql-file', '-i', type=pathlib.Path, required=True, help="Sqlite DB with decrypted Signal conversations")
    parser.add_argument('--output-file', '-o', type=pathlib.Path, required=True, help="Export file for Signal conversations")
    parser.add_argument('--verbose', '-v', action='count', default=0, help="Show verbose conversion logs. Default: 0")
    args = parser.parse_args()

    # Load Signal conversations into In-Memory from Sqlite DB
    signal = Signal(sqlfile=args.sql_file, verbose=args.verbose)

    # Export Signal conversations to Org-Mode
    if args.output_file.suffix == '.org':
        signal.export_org(args.output_file)
