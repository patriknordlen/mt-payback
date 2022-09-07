FROM python:3.9

EXPOSE 3000

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "gunicorn", "-b", "0.0.0.0:3000", "app:app" ]