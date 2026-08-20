FROM python:3.12-slim

WORKDIR /docs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["mkdocs"]
CMD ["--help"]
