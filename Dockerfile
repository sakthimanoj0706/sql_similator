FROM ghcr.io/meta-pytorch/openenv-base:latest

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV ENABLE_WEB_INTERFACE=true
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]