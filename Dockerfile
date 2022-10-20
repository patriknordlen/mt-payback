# Stage 1
FROM python:3.9 AS build-env

WORKDIR /app
COPY . .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

# Stage 2
FROM gcr.io/distroless/python3:nonroot

EXPOSE 3000
WORKDIR /app

COPY --from=build-env /app /app
COPY --from=build-env /opt /opt

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.9/site-packages"

CMD [ "/opt/venv/bin/gunicorn", "-b", "0.0.0.0:3000", "app:app" ]