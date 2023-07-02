FROM    python:3.8.6-slim

# Set the working directory to /scripts
WORKDIR /scripts
COPY    . /scripts

RUN     pip install -r /scripts/requirements.txt
RUN     chmod +x /scripts/api-peek
RUN     ln -s /scripts/api-peek /bin/api-peek

CMD     [ "api-peek", "-h" ]