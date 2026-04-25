build:
	docker build -t queues .

run:
	docker run -it -v ${PWD}:/app -p 8050:8050 queues