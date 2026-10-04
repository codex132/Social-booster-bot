FROM cypress/browsers:latest

# install python3 + pip
RUN apt-get update && apt-get install -y python3 python3-pip

ENV PATH /home/root/.local/bin:${PATH}

COPY requirements.txt .
RUN pip install -r requirements.txt --break-system-packages

COPY . .

CMD python3 bot.py
