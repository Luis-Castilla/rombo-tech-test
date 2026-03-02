# ALB SG: Solo permite entrada HTTPS desde internet.
resource "aws_security_group" "alb_sg" {
  name        = "loan-api-alb-sg"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS SG: Solo permite tráfico entrante por el puerto 5001 SI viene del ALB.
resource "aws_security_group" "ecs_sg" {
  name        = "loan-api-ecs-sg"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow HTTP 5001 from ALB only"
    from_port       = 5001
    to_port         = 5001
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id] # <- Enlace de confianza
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS SG: Solo permite tráfico entrante por el puerto 5432 SI viene de Fargate.
resource "aws_security_group" "rds_sg" {
  name        = "loan-api-rds-sg"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow PostgreSQL traffic from ECS Tasks only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id] # <- Enlace de confianza
  }
}

resource "aws_db_instance" "postgresql" {
  identifier                  = "loan-management-db"
  engine                      = "postgres"
  engine_version              = "16.1"
  instance_class              = "db.t4g.medium"
  allocated_storage           = 50
  
  # Seguridad y Cumplimiento
  storage_encrypted           = true
  multi_az                    = true
  backup_retention_period     = 7 # Backups automatizados por 7 días
  skip_final_snapshot         = false
  copy_tags_to_snapshot       = true

  # Redes
  db_subnet_group_name        = aws_db_subnet_group.private_subnets.name
  vpc_security_group_ids      = [aws_security_group.rds_sg.id]
  publicly_accessible         = false

  # Credenciales administradas por Secrets Manager (Recomendado en AWS moderno)
  manage_master_user_password = true
  master_username             = "postgres_admin"
}

resource "aws_ecs_task_definition" "flask_app" {
  family                   = "loan-api-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "flask-backend"
      image     = "${var.ecr_repository_url}:latest"
      essential = true
      
      portMappings = [
        {
          containerPort = 5001
          hostPort      = 5001
          protocol      = "tcp"
        }
      ]
      
      # Variables de entorno no sensibles
      environment = [
        { name = "FLASK_ENV", value = "production" },
        { name = "PORT", value = "5001" }
      ]
      
      # Inyección segura de secretos desde Secrets Manager (Crucial para auditorías)
      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.db_credentials.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/loan-api"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "flask"
        }
      }
    }
  ])
}