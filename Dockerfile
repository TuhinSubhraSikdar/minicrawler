FROM python:3.8-slim

ADD crawltym.py .

RUN pip install requests beautifulsoup4 pandas
CMD ["python", "./crawltym.py"]