# Python 3.10 versiyasini tanlaymiz
FROM python:3.10-slim

# Ishchi papkani belgilaymiz
WORKDIR /app

# Kerakli kutubxonalarni o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Asosiy kodni ko'chiramiz
COPY main.py .

# Downloads papkasini ochib qo'yamiz (xatolik bo'lmasligi uchun)
RUN mkdir -p downloads

# Botni ishga tushiramiz
CMD ["python", "main.py"]
