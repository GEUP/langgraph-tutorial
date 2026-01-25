LMStudio 실행

cp example.env .env

docker build -t my-langgraph-agent .

# --add-host=host.docker.internal:host-gateway 옵션은 "컨테이너야, host.docker.internal이라는 주소를 찾으면 host-gateway(도커가 호스트와 연결된 문) IP로 연결해줘" 라고 /etc/hosts 파일에 수동으로 적어주는 것과 같습니다.
docker run -p 8000:8000 --add-host=host.docker.internal:host-gateway my-langgraph-agent


curl -X POST "http://localhost:8000/chat/stream" \
-H "Content-Type: application/json" \
-d '{"thread_id": "user1", "message": "안녕, 너는 누구니?"}'