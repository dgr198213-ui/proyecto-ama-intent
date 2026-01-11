.PHONY: help build up down logs restart clean test deploy

help:
	@echo "AMA-Intent + SDDCS Docker Commands"
	@echo "===================================="
	@echo "build      - Build Docker images"
	@echo "up         - Start all services"
	@echo "down       - Stop all services"
	@echo "logs       - Show logs (all services)"
	@echo "restart    - Restart all services"
	@echo "clean      - Remove all containers and volumes"
	@echo "test       - Run integration tests"
	@echo "deploy     - Deploy to production"
	@echo "backup     - Create manual backup"

build:
	docker-compose build --no-cache

up:
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "Dashboard: http://localhost:8000"
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -af

test:
	docker-compose exec ama-dashboard pytest tests/ -v

deploy:
	@echo "🚀 Deploying to production..."
	git pull origin main
	docker-compose pull
	docker-compose up -d --build
	@echo "✅ Deployment complete!"

backup:
	docker-compose exec backup python /app/backup_script.py --manual
