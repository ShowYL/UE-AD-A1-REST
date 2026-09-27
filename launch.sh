cp requirements.txt booking/
cp requirements.txt movie/
cp requirements.txt user/
cp requirements.txt schedule/

cp lib/utils.py booking/
cp lib/utils.py movie/
cp lib/utils.py user/
cp lib/utils.py schedule/

docker compose up --build
