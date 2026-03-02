# 🏦 Core Financiero: API de Gestión de Cartera (Colombia)

## 📌 Descripción General

Este proyecto es un motor transaccional de backend construido en **Python (Flask)** para la originación, amortización y recaudo de créditos de consumo. Está diseñado estrictamente bajo los principios de **Arquitectura Hexagonal (Puertos y Adaptadores)** y **Domain-Driven Design (DDD)**, garantizando una separación absoluta entre las reglas matemáticas del negocio y los detalles de infraestructura.

El sistema implementa normativas financieras colombianas específicas, incluyendo la prelación legal en la cascada de pagos, validaciones contra la tasa de usura y causación de intereses usando precisión decimal estricta (`NUMERIC(18,2)`).

## 🏗️ Decisiones Arquitectónicas (ADR Highlights)

- **Arquitectura Hexagonal & DDD:** El núcleo de la aplicación (`src/domain/`) no tiene dependencias externas. Las entidades protegen sus propias invariantes.
- **Transaccionalidad (ACID) & Unit of Work:** La creación de créditos y los asientos contables operan bajo transacciones atómicas. Si la contabilidad falla, la base de datos hace un rollback completo.
- **Concurrencia (Row-Level Locking):** Para evitar _race conditions_ durante el recaudo (ej. webhooks duplicados), se implementan bloqueos pesimistas (`WITH FOR UPDATE`) a nivel de fila en PostgreSQL.
- **Idempotencia:** Los pagos requieren una llave de referencia única para prevenir cobros duplicados por latencia de red.
- **CQRS Ligero:** La consulta del extracto (`/statement`) separa el modelo de lectura del de escritura, optimizando las consultas con `joinedload`.

## 🚀 Tecnologías Principales

- **Lenguaje:** Python 3.11
- **Framework Web:** Flask (Patrón Application Factory & Blueprints)
- **Base de Datos:** PostgreSQL 16
- **ORM & Migraciones:** SQLAlchemy 2.0 + Flask-Migrate (Alembic)
- **Testing:** Pytest + Freezegun (Time-mocking)
- **Contenedores:** Docker & Docker Compose

## 📂 Estructura del Proyecto

La estructura refleja el flujo de dependencias de afuera hacia adentro:

```text
proyecto-cartera/
├── docs/                 # Documentación técnica
│   ├── adr/              # Architecture Decision Records
│   └── diagrams/         # Diagramas ERD y de Secuencia (Mermaid)
├── migrations/           # Historial autogenerado de Flask-Migrate
├── src/
│   ├── domain/           # 1. CORE: Entidades puras, Value Objects y Excepciones.
│   ├── application/      # 2. CASOS DE USO: Orquestación, DTOs y Puertos (Interfaces).
│   ├── infrastructure/   # 3. ADAPTADORES: Flask Controllers, Repositorios SQLAlchemy.
│   └── main.py           # Entrypoint y Application Factory.
└── tests/                # Pruebas Unitarias e Integración.
```

## 🔌 API Endpoints Principales

- **`POST /api/v1/loans/simulate`**: Simula una tabla de amortización (Cuota Fija o Abono Constante) manejando conversiones entre tasas EA y NMV.
- **`POST /api/v1/loans`**: Crea un crédito, valida elegibilidad, tasa de usura y genera el asiento contable de desembolso inicial.
- **`POST /api/v1/loans/{id}/payments`**: Motor de pagos. Aplica abonos siguiendo la ley colombiana (Costas -> Seguros -> Mora -> Corriente -> Capital).
- **`GET /api/v1/loans/{id}/statement`**: Retorna el extracto calculado al día actual, liquidando mora e intereses dinámicamente.

## ⚙️ Configuración del Entorno (`.env`)

Crea un archivo `.env` en la raíz del proyecto basándote en el siguiente ejemplo:

```env
FLASK_APP=src/main.py
FLASK_ENV=development
PORT=5001

# Database Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=loan_management_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

# URL de Conexión de SQLAlchemy
DATABASE_URL=postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
```

## 🐳 Ejecución Local (Docker - Recomendado)

La forma más limpia de levantar la infraestructura completa (App + PostgreSQL):

Construir y levantar los contenedores:

```bash
docker-compose up -d --build
```

Ejecutar migraciones (Primera vez):

```bash
docker-compose exec web flask db upgrade
```

Verificar Health Check:  
`GET http://localhost:5001/health`

## 💻 Ejecución Local (Modo Clásico)

Crear y activar entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar servidor:

```bash
flask run --host=0.0.0.0 --port=5001
```

## 🧪 Pruebas Automatizadas (Testing)

El proyecto cuenta con una suite de pruebas enfocada en la precisión matemática del dominio y la integridad de la base de datos. Para ejecutarlas:

```bash
# Si usas Docker:
docker-compose exec web pytest -v

# Si estás en local:
pytest tests/ -v --cov=src
```

## 1. Diseño de Base de Datos y Modelo de Datos

- Se puede encontrar el diagrama entidad relación en el archivo [`er_diagram.md`](./docs/diagrams/er_diagram.md).
- Se puede encontrar el script de inicialización de las entidades en el archivo [`init_schema.sql`](./infrastructure/database/init_schema.sql).
- Se puede encontrar la justificación del modelo ER en [`0001-database-design.md`](./docs/adr/0001-database-design.md).

## 3. Entregables de Arquitectura e Infraestructura

- **3.1 Diagrama de Arquitectura en AWS:** El diagrama detallado y su justificación técnica se encuentran en el archivo [`Architecture.md`](./Architecture.md).
- **3.2 Infraestructura como Código (IaC):** El snippet de Terraform definiendo los Security Groups, la base de datos RDS y la tarea ECS Fargate se encuentra en el archivo [`rombo.tf`](./rombo.tf).
- **3.3 Preguntas de Arquitectura:**
  1. **Implementación del pipeline CI/CD**
     - **Code Analysis & Security (Linting & SAST):** Ejecución de `flake8` y `black` para asegurar estándares PEP-8. Adicionalmente, escaneo estático de seguridad con `bandit` para detectar vulnerabilidades en el código Python y `trivy` para analizar la imagen base de Docker.
     - **Testing:** Levantamiento de servicios efímeros (ej. PostgreSQL vía Service Containers) para ejecutar pruebas unitarias y de integración con `pytest`. El pipeline falla si la cobertura de código baja del 80% o si algún test transaccional falla.
     - **Build & Push:** Construcción de la imagen Docker optimizada (multietapa). Se etiqueta con el SHA del commit y se empuja al registry de AWS (Amazon ECR).
     - **Deploy a Staging:** Actualización automática del servicio ECS en el ambiente de Staging (modificando la Task Definition con la nueva imagen). Ejecución de migraciones de base de datos (`flask db upgrade`) mediante un contenedor de inicialización (Init Container) o un job efímero.
     - **Promoción a Producción:** Pasarela de aprobación manual (Manual Approval Gate). Una vez aprobado, se ejecuta el despliegue a Producción usando un patrón Rolling Update en ECS para garantizar cero tiempo de inactividad (Zero Downtime Deployment), monitoreando el health check del ALB antes de drenar las tareas antiguas.
  2. **Estrategia de Backups y Recuperación (RPO < 1h y RTO < 4h)**
     - **Para el RPO < 1 hora (Point-in-Time Recovery):** RDS ofrece backups automáticos y archivo continuo de los registros de transacciones (WAL logs) en S3. Esto nos permite restaurar la base de datos a cualquier segundo específico de los últimos 7 a 35 días. Nuestro RPO real sería de apenas 5 minutos.
     - **Para el RTO < 4 horas: Fallas de infraestructura:** Al tener RDS en modo Multi-AZ, si la instancia principal cae, AWS hace un failover automático a la réplica Standby en menos de 2 minutos. El RTO aquí es casi instantáneo.
  3. **Escalabilidad ante incrementos de carga (10x en cierres de mes)**
     - **Auto Scaling:** Cuando se supere el; 70% de uso de CPU.
     - **Connection Pooling:** Permitir un pool de conexiones a través de AWS RDS Proxy.
     - **Procesamiento Asíncrono:** Para tareas que no requieren respuesta inmediata, se pueden utilizar colas de mensajes (ej. SQS) para procesarlas de forma asíncrona.
  4. **Consideraciones de Seguridad (Cifrado, Auditoría y Cumplimiento)**
     - **Cifrado:** Uso de TLS > 1.2, forzar SSL desde la app a la bd, encriptar la BD, cifrar datos sensibles en la BD.
     - **Auditoría:** Registro de todas las operaciones críticas en una tabla de auditoría, logs de auditoría.
     - **Cumplimiento:** Cumplimiento con las normativas colombianas de protección de datos (Ley 1581 de 2012).

## 4. Resolución de Prueba Técnica: Conceptos y Práctica

### 4.1 Respuestas Teóricas

#### 1. Tasa Nominal vs. Tasa Efectiva

- **Tasa Nominal:** Es una tasa de referencia o "etiqueta" anual que indica cuántas veces se liquidarán los intereses en el año, pero **no** tiene en cuenta la reinversión de los mismos (interés compuesto).
- **Tasa Efectiva Anual (EA):** Es la tasa real que muestra el costo verdadero del dinero al final del año, incorporando el efecto de la capitalización compuesta (cobrar intereses sobre los intereses generados).

**Conversión de 24% Nominal Mes Vencido (NMV) a Efectiva Anual (EA):**

1. Hallamos la tasa periódica mensual ($i$):
   $$i = \frac{0.24}{12} = 0.02$$ (2% mensual)
2. Aplicamos la fórmula de capitalización:
   $$EA = (1 + 0.02)^{12} - 1$$
   $$EA \approx 1.26824 - 1 = 0.26824$$
   **Resultado:** Una tasa del 24% NMV equivale exactamente a una tasa del **26.82% EA**.

#### 2. Interés Simple vs. Interés Compuesto

- **Interés Simple:** El interés se calcula siempre sobre el capital inicial. Los intereses no se suman al capital.
- **Interés Compuesto:** El interés se calcula sobre el capital inicial más los intereses acumulados.
- **Uso en Colombia:** Para los créditos de consumo se utiliza el **Interés Compuesto** para calcular la tabla de amortización (cuotas fijas basadas en anualidades). Sin embargo, por ley (para evitar el anatocismo), los intereses de mora **no** se pueden cobrar sobre intereses corrientes pendientes, solo sobre el saldo de capital vencido.

#### 3. Principio de Partida Doble y Asientos Contables (PUC Financiero)

El principio establece que toda transacción afecta al menos dos cuentas, donde los Débitos deben igualar a los Créditos.

**(a) Desembolso ($10.000.000 COP):**
| Código | Cuenta | Débito | Crédito |
| :--- | :--- | :--- | :--- |
| 1405 | Cartera de Créditos de Consumo | $10.000.000 | - |
| 1110 | Bancos y Otras Entid. Financieras | - | $10.000.000 |

**(b) Causación de intereses primer mes (Ej: $200.000 COP):**
| Código | Cuenta | Débito | Crédito |
| :--- | :--- | :--- | :--- |
| 1605 | Intereses por Cobrar (Activo) | $200.000 | - |
| 4105 | Ingresos Operac. por Intereses | - | $200.000 |

**(c) Recaudo primera cuota (Ej: $1.000.000 COP total / $800k capital, $200k interés):**
| Código | Cuenta | Débito | Crédito |
| :--- | :--- | :--- | :--- |
| 1110 | Bancos y Otras Entid. Financieras | $1.000.000 | - |
| 1605 | Intereses por Cobrar (Activo) | - | $200.000 |
| 1405 | Cartera de Créditos de Consumo | - | $800.000 |

#### 4. Provisión de Cartera

Es un gasto que la Superintendencia Financiera obliga a contabilizar para cubrir el riesgo de impago. Se calcula aplicando un porcentaje normativo sobre el saldo de capital, el cual aumenta si la calificación de riesgo del cliente se deteriora (A, B, C, D, E).

- **Modelado en BD:** Nunca se resta directamente del saldo del crédito. Se modela en una tabla anexa `portfolio_provisions` (relacionada al `loan_id`) que registra la calificación, fecha y monto provisionado, disparando el asiento contable correspondiente (Gasto vs. Cuenta compensatoria de activo).

#### 5. Contabilidad de Causación vs. Caja

- **Caja:** Reconoce ingresos/gastos solo cuando el dinero entra o sale del banco.
- **Causación (Devengo):** Reconoce los hechos económicos en el momento en que ocurren.
- **Aplicación:** Un sistema de créditos debe causar intereses mensualmente porque el servicio financiero (prestar el dinero) ya se ejecutó en ese periodo. Las NIIF exigen reflejar el derecho de cobro y el ingreso real generado para la entidad en ese mes, aunque el cliente pague después.

#### 6. Tasa de Usura

Es el límite máximo legal de intereses que se puede cobrar por un préstamo en Colombia. Cobrar por encima de ella es un delito penal e implica sanciones civiles (pérdida de intereses y devolución indexada). Es certificada **mensualmente** por la Superintendencia Financiera de Colombia.

---

### 4.2 Ejercicio Práctico de Amortización

**Parámetros:**

- Monto: $20.000.000 COP
- Tasa: 24% NMV (**2% mensual periódico**)
- Plazo: 12 meses
- Modalidad: Cuota fija

#### Tabla de Amortización

| Fecha      | Saldo Inicial  | Interés (2%) | Cuota Total   | Abono a Capital | Nuevo Saldo    |
| :--------- | :------------- | :----------- | :------------ | :-------------- | :------------- |
| 01/04/2026 | $20,000,000.00 | $400,000.00  | $1,891,191.93 | $1,491,191.93   | $18,508,808.07 |
| 01/05/2026 | $18,508,808.07 | $370,176.16  | $1,891,191.93 | $1,521,015.77   | $16,987,792.30 |
| 01/06/2026 | $16,987,792.30 | $339,755.85  | $1,891,191.93 | $1,551,436.09   | $15,436,356.21 |
| 01/07/2026 | $15,436,356.21 | $308,727.12  | $1,891,191.93 | $1,582,464.81   | $13,853,891.40 |
| 01/08/2026 | $13,853,891.40 | $277,077.83  | $1,891,191.93 | $1,614,114.10   | $12,239,777.30 |
| 01/09/2026 | $12,239,777.30 | $244,795.55  | $1,891,191.93 | $1,646,396.39   | $10,593,380.91 |
| 01/10/2026 | $10,593,380.91 | $211,867.62  | $1,891,191.93 | $1,679,324.31   | $8,914,056.60  |
| 01/11/2026 | $8,914,056.60  | $178,281.13  | $1,891,191.93 | $1,712,910.80   | $7,201,145.80  |
| 01/12/2026 | $7,201,145.80  | $144,022.92  | $1,891,191.93 | $1,747,169.02   | $5,453,976.78  |
| 01/01/2027 | $5,453,976.78  | $109,079.54  | $1,891,191.93 | $1,782,112.40   | $3,671,864.38  |
| 01/02/2027 | $3,671,864.38  | $73,437.29   | $1,891,191.93 | $1,817,754.64   | $1,854,109.74  |
| 01/03/2027 | $1,854,109.74  | $37,082.19   | $1,891,191.93 | $1,854,109.74   | $0.00          |

- **Costo Total (Intereses pagados):** `$2,694,303.19`
- **Verificación de Usura:** Tasa EA calculada (26.82%) < Tasa Usura asumida (27.62%).

#### Cálculo de Interés Moratorio (Cuota 6, Atraso de 15 días)

Para evitar el anatocismo, el interés de mora se calcula únicamente sobre la porción de capital de la cuota vencida (Abono a capital Cuota 6 = **$1,646,396.39**).

1. **Definir Tasa:**
   - Tasa corriente: 2%
   - Tasa mora proyectada (1.5x): 3%
   - Tope máximo (Usura a mes vencido): **2.05%** (Se aplica esta por ser menor a la proyectada).
2. **Aplicar Fórmula:**
   $$Interes\_Mora = Saldo\_Capital\_Vencido \times \left( \frac{Tasa\_Mora\_Mensual}{30} \right) \times Dias\_Atraso$$
   $$Interes\_Mora = 1,646,396.39 \times \left( \frac{0.0205}{30} \right) \times 15$$
   $$Interes\_Mora = 1,646,396.39 \times 0.00068333 \times 15 \approx \$16,875.56$$

#### Asientos Contables Transaccionales

**1. Desembolso del Crédito:**
| Código | Cuenta | Débito | Crédito |
| :--- | :--- | :--- | :--- |
| 1405 | Cartera de Créditos de Consumo | $20,000,000.00 | - |
| 1110 | Bancos y Otras Entid. Financieras | - | $20,000,000.00 |

**2. Recaudo de la Primera Cuota:**
| Código | Cuenta | Débito | Crédito |
| :--- | :--- | :--- | :--- |
| 1110 | Bancos y Otras Entid. Financieras | $1,891,191.93 | - |
| 1405 | Cartera de Créditos de Consumo | - | $1,491,191.93 |
| 4105 | Ingresos Operac. por Intereses | - | $400,000.00 |

## 5. Caso Práctico Integrador: Resolución de Incidentes en Producción

Ante el reporte de inconsistencias en saldos, pagos duplicados y fallos en la causación, se aborda el incidente desde cuatro frentes: diagnóstico SQL, prevención de concurrencia, script de remediación transaccional y monitoreo proactivo.

### 5.1 Consultas SQL de Diagnóstico

Estas consultas sobre el modelo relacional permiten identificar la magnitud y raíz de los datos corruptos.

**a) Identificar pagos duplicados (por referencia de pasarela y monto):**

```sql
SELECT
    payment_reference,
    COUNT(id) as total_intentos,
    SUM(paid_amount) as monto_total_registrado
FROM payments
GROUP BY payment_reference
HAVING COUNT(id) > 1;
```

**b) Identificar asientos contables descuadrados:**

```sql
SELECT
    journal_entry_id,
    SUM(debit) as total_debito,
    SUM(credit) as total_credito,
    ABS(SUM(debit) - SUM(credit)) as diferencia
FROM journal_entry_lines
GROUP BY journal_entry_id
HAVING SUM(debit) != SUM(credit);
```

**c) Identificar créditos con mora > 30 días que siguen "Al día" (CURRENT):**

```sql
SELECT DISTINCT
    l.id as loan_id,
    l.status as current_status,
    MIN(a.due_date) as oldest_unpaid_due_date,
    CURRENT_DATE - MIN(a.due_date) as days_in_arrears
FROM loans l
JOIN amortization_schedules a ON l.id = a.loan_id
WHERE a.is_paid = FALSE
  AND l.status = 'CURRENT'
GROUP BY l.id, l.status
HAVING (CURRENT_DATE - MIN(a.due_date)) > 30;
```

### 5.2 Prevención de Pagos Duplicados (Patrón de Idempotencia)

Para evitar múltiples callbacks duplicados, se implementa un patrón de Idempotencia estricta en tres capas:

- **Restricción de Base de Datos (Unique Constraint):** El campo `payment_reference` en la tabla `payments` cuenta con un índice UNIQUE. Es la última línea de defensa.
- **Manejo en la Capa de Aplicación:** Al recibir el webhook, el sistema intenta insertar el pago. Si este ya existe (disparando un `IntegrityError`), el backend captura la excepción y responde con un HTTP 200 OK a la pasarela. Devolver un 400 o 500 causaría que la pasarela siga reintentando.
- **Bloqueo a Nivel de Fila (Row-Level Locking):** Si dos webhooks idénticos llegan en el mismo milisegundo, aplicamos `SELECT ... FOR UPDATE` sobre el registro del crédito. El primer hilo procesa; el segundo espera, falla limpiamente por el Unique Constraint al liberarse el bloqueo, y retorna 200 OK.

### 5.4 Reconciliación Contable Automática (Monitoreo Proactivo)

Para evitar que estos incidentes alcancen al cliente final o afecten el cierre contable, se implementa un Job de Cuadre de Cartera Diario:

- **Ejecución:** Un Cron Job batch en ECS Fargate que corre todos los días a las 2:00 AM.
- **Ecuación de Cuadre:** El job extrae y compara tres valores que deben coincidir al centavo:
  - **A.** `SUM(principal_balance)` en la tabla `loans` (Sistema Core).
  - **B.** `SUM(principal_balance)` pendiente en la tabla `amortization_schedules` (Detalle de Cuotas).
  - **C.** Saldo neto (Débitos - Créditos) de la cuenta 1405 (Cartera de Créditos) en `journal_entry_lines` (Libro Contable).
- **Validación y Alerta:** **A == B == C**. Si se detecta una diferencia, el sistema **no** la auto-corrige. Emite una alerta vía webhook a Slack/Teams del equipo de Operaciones Financieras con la diferencia exacta y los IDs afectados, permitiendo una intervención temprana.
