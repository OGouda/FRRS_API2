
# FROM python:3.7.9-slim-stretch
FROM omargouda/frrs_base:latest
WORKDIR usr/src/API
COPY ./API ./
# RUN apt-get -y update
# RUN apt-get install -y --fix-missing \
#     build-essential \
#     cmake \
#     gfortran \
#     git \
#     wget \
#     curl \
#     graphicsmagick \
#     libgraphicsmagick1-dev \
#     libatlas-dev \
#     libavcodec-dev \
#     libavformat-dev \
#     libgtk2.0-dev \
#     libjpeg-dev \
#     liblapack-dev \
#     libswscale-dev \
#     libpq-dev \
#     pkg-config \
#     python3-dev \
#     python3-numpy \
#     software-properties-common \
#     zip \
#     && apt-get clean && rm -rf /tmp/* /var/tmp/*

# RUN pip install -r requirements.txt

# If you wanted to use this Dockerfile to run your own app instead, maybe you would do this:
# COPY . /root/your_app_or_whatever
# RUN cd /root/your_app_or_whatever && \
#     pip3 install -r requirements.txt
# RUN whatever_command_you_run_to_start_your_app
#
#RUN ["chmod", "+x", "/usr/src/API/First_Setup.sh"]
#ENTRYPOINT [ "/usr/src/API/First_Setup.sh" ]
ENTRYPOINT [ "python","/usr/src/API/First.py" ]
EXPOSE 5000
CMD ["python","/usr/src/API/app.py"]

