up:
	docker-compose -f local.yml build
	docker-compose -f local.yml up

ups:
	docker-compose -f sandbox.yml build
	docker-compose -f sandbox.yml up
