docker build -f postgres.dockerfile -t straders_db .
docker stop spacetraders_db
docker rm spacetraders_db
docker run --name spacetraders_db -env-file .env   -p 6432:5432 -d straders_db