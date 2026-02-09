# FROM mindbowser/python:3.10
# FROM mindbowser/python:3.10
# Copy application artifacts
FROM public.ecr.aws/t6g5d7d1/python:3.10

COPY target /wheelhouse
COPY docker/release/app.ini /app.ini

# Take Arguments
ARG SRC_DIR=src
ENV MODULE=${SRC_DIR}
# Install required libraries
RUN . /appenv/bin/activate && \
    pip install --no-index -f /wheelhouse ${SRC_DIR} && \
    pip install drf_social_oauth2==1.2.1 && \
    rm -rf /wheelhouse
EXPOSE 8443

CMD ["uwsgi" ,"--ini" , "/app.ini"]