# goDaddy_API

python godaddy.com API classes

look `if __name__ == '__main__':` in `.py` file for how to use the class

`pip3 install -r requirements.txt` to setup python3 enviroment

need to setup your own API key/secret vis enviroment variables to make it work

`auto_update.py` run by cronjob behind NAT to automatically update DNS record if the public IPv4 changes

Tips to install `python3.8` on Ubuntu:
```bash
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.8.16/Python-3.8.16.tgz
tar -xf Python-3.8.16.tgz
cd Python-3.8.16/
./configure --enable-optimizations
make -j 8
sudo make altinstall
```