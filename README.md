# signal-to-org
Convert Signal Backup to Org-Mode

# Process
  1. Get Signal Backup file. See [Official Signal Docs](https://support.signal.org/hc/en-us/articles/360007059752-Backup-and-Restore-Messages) for details
  2. Extract Decrypted Sqlite DB from Signal Backup. Use [Signal for Android Decryption {Github}](https://github.com/mossblaser/signal_for_android_decryption)
  3. Extract Signal Conversations into Org-Mode using this repository. See **Setup**, **Run** instructions below

## Setup
  ```shell
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

## Run
  ```shell
  python3 designal.py --sql-file data/database.sqlite --output-file data/signal.org
  ```
