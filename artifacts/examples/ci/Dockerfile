FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask==3.0.0 itsdangerous==2.1.2
USER 1000
CMD ["python3", "-c", "print('ok')"]
