# Installation Steps

### Install Docker (for Ubuntu 18.04)

```bash
sudo apt update
```

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common
```

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

```bash
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
```

```bash
sudo apt update
```

```bash
apt-cache policy docker-ce
```

```bash
sudo apt install docker-ce
```

```bash
sudo systemctl status docker
```

### Install Docker Compose

```bash
sudo curl -L https://github.com/docker/compose/releases/download/1.21.2/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
```

```bash
sudo chmod +x /usr/local/bin/docker-compose
```

```bash
docker-compose --version
```

### Install Superdesk Application

```bash
docker-compose up -d
```

```bash
docker-compose run superdesk-server run python manage.py users:create -u admin -p admin -e admin@localhost --admin
```

```bash
docker-compose run superdesk-server run python manage.py users:create -u dody -p barus -e 'dody@barus.com'
docker-compose run superdesk-server run python manage.py users:create -u christian -p tarigan -e 'christian@tarigan.com'
```

#### For Demo Purpose Only
```bash
docker-compose run superdesk-server run python manage.py app:scaffold_data
```