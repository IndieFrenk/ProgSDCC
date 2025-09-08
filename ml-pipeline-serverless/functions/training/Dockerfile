
FROM python:3.9

RUN pip install --no-cache-dir pandas scikit-learn joblib

WORKDIR /app
COPY train.py ./

CMD ["python", "train.py"]
