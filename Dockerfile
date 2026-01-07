FROM python:3.12.8
# Allow for user permissions to be set here so that the data can be written in CLinVar Search
#debugged with chatGPT 

ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID appuser && \
    useradd -m -u $UID -g $GID appuser

USER appuser


# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY --chown=appuser:appuser requirements.txt /app/
COPY --chown=appuser:appuser ./clinvar_query /app/clinvar_query


RUN pip install --no-cache-dir -r requirements.txt


 ARG DEFAULT_PORT=5000
 ENV PORT=$DEFAULT_PORT
 EXPOSE $PORT

 ENV PYTHONPATH="/app:$PYTHONPATH"

#these commands will run when the docker is started
CMD ["python", "clinvar_query/ClinVar_Site/app.py"]


