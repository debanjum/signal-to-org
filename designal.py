# Standard Packages
import argparse
from datetime import datetime
import pathlib
from enum import Enum, auto

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
        print('constructing conversation')

    def export(self, indent=0):
        ret = ""
        ret += f"{'*'*indent} {self.name}\n"
        for message in sorted(self.messages, key=lambda x: x.date_received):
            ret += f"{'*'*(indent+1)} {message.heading_str()}\n"
            ret += f":PROPERTIES:\n:CUSTOM_ID: {message.date_sent.isoformat()}\n:END:\n"
            ret += f"{message.body}\n"
            if message.parent:
                ret += f"[[#{message.parent.date_sent.isoformat()}][{message.parent.body_header}]]\n"
            if message.descendants:
                ret += f"{'*'*(indent+2)} Replies\n"
                for descendant in message.descendants:
                    ret += f"[[#{descendant.date_sent.isoformat()}][{descendant.body_header}]]\n"

        return ret

    def add_message(self, message: "Message"):
        self.messages.append(message)

    def __repr__(self) -> str:
        return self.name


class User:
    """
    A Signal User
    """

    def __init__(self, name) -> None:
        self.name = name


# create enum class
class MessageType(Enum):
    INCOMING = auto()
    OUTGOING = auto()
    OTHER = auto()


class Message:
    """
    A Signal Message
    """

    def __init__(
        self,
        date_received,
        date_sent,
        body,
        sender,
        message_type: MessageType,
        conversation: Conversation,
        parent: "Message",
    ) -> None:
        print("construction message")
        self.date_received = date_received
        self.date_sent = date_sent
        self.body = body if body else ""
        self.conversation = conversation
        self.message_type = message_type
        self.sender = sender
        self.parent = parent
        self.children = []

        if self.parent:
            self.parent.children.append(self)

    @property
    def body_header(self):
        return self.body.split("\n")[0]

    def heading_str(self) -> str:
        return f'[{self.date_received.strftime("%Y-%m-%d %H:%M")}] {self.sender}: {self.body_header}'

    def __repr__(self) -> str:
        return f'[{self.date_received.strftime("%Y-%m-%d %H:%M")}]: {self.sender}: {self.body}'

    @property
    def descendants(self):
        ret2 = self.children
        for child in self.children:
            ret2 += child.descendants
        return ret2


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
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get all plain and rich-text Signal messages
        sms = cur.execute(
            "select date_sent, date, body, thread_id, address, type from sms;"
        ).fetchall()
        mms = cur.execute(
            "select date, date_received, body, thread_id, address, msg_box, quote_id from mms;"
        ).fetchall()

        sms = [dict(m) for m in sms]
        mms = [dict(m) for m in mms]

        for m in sms:
            m["date_received"] = m.pop("date")
            m["quote_id"] = 0

        for m in mms:
            m["date_sent"] = m.pop("date")
            m['type'] = m.pop("msg_box")

        messages = sms + mms

        # sort messages by date column in db
        messages.sort(key=lambda m: m["date_received"])

        # Create List of Users
        recipients = cur.execute(
            f"select _id, system_display_name, group_id from recipient"
        ).fetchall()
        user_dict = dict()
        for recipient in recipients:
            user_dict[recipient[0]] = User(recipient[1])

        # Create Thread Id to Conversation Name Map
        conversation_name_dict = {}
        threads = cur.execute("select _id, thread_recipient_id from thread;").fetchall()
        for thread in threads:
            recipients = cur.execute(
                f"select system_display_name, group_id from recipient where _id={thread[1]};"
            ).fetchall()
            for recipient in recipients:
                if recipient[1]:  # group id
                    group = cur.execute(
                        f"select title from groups where recipient_id={thread[1]};"
                    ).fetchone()
                    conversation_name_dict[thread[0]] = group[0]
                else:
                    conversation_name_dict[thread[0]] = recipient[0]

        # Load Signal data into VDB in an intermediate representation
        for message in messages:
            # Ignore Non Processable Messages
            if message["thread_id"] == "" or message["thread_id"] is None:
                continue
            thread_id = message["thread_id"]

            conversation = [t for t in vdb.conversations if t.thread_id == thread_id]
            if not conversation:
                conversation = Conversation(
                    thread_id, name=conversation_name_dict[thread_id]
                )
                vdb.conversations.append(conversation)
            else:
                conversation = conversation[0]

            # Identify Message Sender
            if message["type"] == 10485783:
                message_type = MessageType.INCOMING
                sender = "Me"
            elif message["type"] == 10485780:
                message_type = MessageType.OUTGOING
                sender = user_dict[message["address"]].name
            else:
                continue

            parent_message = None
            if message['quote_id']:
                parent_message = [
                    m
                    for m in conversation.messages
                    if m.date_sent == datetime.utcfromtimestamp(message["quote_id"] / 1e3)
                ][0]

            conversation.add_message(
                Message(
                    date_received=datetime.utcfromtimestamp(message['date_received'] / 1e3),
                    date_sent=datetime.utcfromtimestamp(message["date_sent"] / 1e3),
                    body=message['body'],
                    sender=sender,
                    message_type=message_type,
                    conversation=conversation,
                    parent=parent_message,
                )
            )
        conn.close()

        return vdb

    def export_org(self, outfile):
        """Create Org File from Virtual DB"""
        with open(outfile, "w") as fout:
            print('hello')
            print('hello')
            print('hello')
            print('hello')
            print('hello')
            for conversation in self.vdb.conversations:
                fout.write(conversation.export(indent=1))


if __name__ == "__main__":
    # Setup Argument Parser for the Commandline Interface
    parser = argparse.ArgumentParser(description="An Exporter of Signal Conversations")
    parser.add_argument(
        "--sql-file",
        "-i",
        type=pathlib.Path,
        required=True,
        help="Sqlite DB with decrypted Signal conversations",
    )
    parser.add_argument(
        "--output-file",
        "-o",
        type=pathlib.Path,
        required=True,
        help="Export file for Signal conversations",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Show verbose conversion logs. Default: 0",
    )
    args = parser.parse_args()

    # Load Signal conversations into In-Memory from Sqlite DB
    signal = Signal(sqlfile=args.sql_file, verbose=args.verbose)

    # Export Signal conversations to Org-Mode
    if args.output_file.suffix == ".org":
        signal.export_org(args.output_file)
