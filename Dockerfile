FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar modelos de NLP (SpaCy y NLTK) para que la imagen ya los tenga listos
RUN pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.7.0/es_core_news_sm-3.7.0.tar.gz
RUN python -c "import nltk; nltk.download('punkt')"

# Pre-descargar modelo de FastEmbed para que no se descargue al iniciar el contenedor
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='paraphrase-multilingual-MiniLM-L12-v2')"

COPY . .

EXPOSE 3005

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3005/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3005"]
