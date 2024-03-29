FROM python:3-buster

WORKDIR /usr/src/app

RUN pip install paho-mqtt~=1.5.1 PyYAML~=5.4.1

COPY . .

CMD [ "python", "./service.py" ]
