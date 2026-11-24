cp requirements.txt booking/
cp requirements.txt movie/
cp requirements.txt user/
cp requirements.txt schedule/

cp lib/utils.py booking/
cp lib/utils.py movie/
cp lib/utils.py user/
cp lib/utils.py schedule/

cp schedule/schedule_pb2.py booking/
cp schedule/schedule_pb2_grpc.py booking/

docker compose up --build
