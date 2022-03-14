# pull official base image
FROM python:3.10.2-alpine

# Install git for pip3 install from git. iputils allows us to ping without elevating to root permissions
RUN apk add --no-cache git iputils

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
RUN addgroup -S app && adduser -S app -G app

# create the appropriate directories
ENV HOME=/home/app
WORKDIR $HOME

# install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . $HOME

# chown all the files to the app user
RUN chown -R app:app $HOME

# change to the app user
USER app

# Set unbuffered
ENV PYTHONUNBUFFERED 1

# run python file
CMD [ "python", "./ping-port-toggle.py" ]