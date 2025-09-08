
FROM python:3.9
RUN pip install pandas openpyxl

WORKDIR /app
COPY converter.py ./

CMD ["python", "converter.py"]
