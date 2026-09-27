FROM python:3.14.7-alpine3.24
# can you find a lighter image?

WORKDIR /app

# copy the requirements file in the workdir
COPY requirements.txt /app/

# install the Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# copy the app files and directories
COPY . .

# start user.py when the container is started
CMD ["python", "-u" , "user.py"]
